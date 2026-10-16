// WOOW CAN sidebar panel. Holds the shared state; the tabs render it.
// Data: one snapshot, then a live feed (woow_can/subscribe) of interface health (every second while the
// panel is open), periodic sends, recordings and the activity log. The monitor tab subscribes to its own
// per-ID feed while it is shown.

import { LitElement, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import {
  Activity,
  Api,
  CaptureFile,
  FeedEvent,
  HomeAssistant,
  InterfaceInfo,
  OfflineInfo,
  Periodic,
  define,
  errorText,
  storageGet,
  storageSet,
} from "./api";
import { Key, Translate, makeTranslate } from "./i18n";
import { shared } from "./styles";
import "./views/activity";
import "./views/capture";
import "./views/monitor";
import "./views/overview";
import "./views/send";

type Tab = "overview" | "monitor" | "send" | "capture" | "activity";
const TABS: Tab[] = ["overview", "monitor", "send", "capture", "activity"];
const ACTIVITY_KEEP = 500;
const HISTORY_POINTS = 300; // load samples kept per interface (one a second)
const MENU = "M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z";

export class WoowCanPanel extends LitElement {
  @property({ attribute: false }) narrow = false;
  @property({ attribute: false }) route?: unknown;
  @property({ attribute: false }) panel?: unknown;

  @state() private tab: Tab = storageGet<Tab>("woow_can.tab", "overview");
  @state() private interfaces: Record<string, InterfaceInfo> = {};
  @state() private offline: OfflineInfo[] = [];
  @state() private periodic: Record<string, Periodic> = {};
  @state() private activity: Activity[] = [];
  @state() private files: CaptureFile[] = [];
  @state() private history: Record<string, number[]> = {};
  @state() private source = storageGet<string>("woow_can.source", "");
  @state() private draft: { frame: string; entryId: string; n: number } | null = null;
  @state() private confirmed = new Set<string>();
  @state() private loaded = false;
  @state() private error = "";

  private _hass?: HomeAssistant;
  private t: Translate = makeTranslate("en");
  private readonly api = new Api(() => this._hass as HomeAssistant);
  private unsubscribe?: () => Promise<void>;
  private connecting = false;

  static styles = [
    shared,
    css`
      :host {
        min-height: 100vh;
        background: var(--primary-background-color);
      }
      .toolbar {
        display: flex;
        align-items: center;
        gap: 8px;
        height: 56px;
        padding: 0 16px;
        background: var(--app-header-background-color, var(--primary-color));
        color: var(--app-header-text-color, var(--text-primary-color, #fff));
        font-size: 20px;
      }
      .toolbar button {
        border: none;
        background: none;
        color: inherit;
        padding: 8px;
        line-height: 0;
      }
      .tabs {
        display: flex;
        gap: 4px;
        padding: 0 12px;
        background: var(--app-header-background-color, var(--primary-color));
        overflow-x: auto;
      }
      .tab {
        border: none;
        border-bottom: 3px solid transparent;
        border-radius: 0;
        background: none;
        color: var(--app-header-text-color, var(--text-primary-color, #fff));
        opacity: 0.75;
        padding: 10px 14px;
        white-space: nowrap;
      }
      .tab.active {
        opacity: 1;
        border-bottom-color: var(--app-header-text-color, var(--text-primary-color, #fff));
      }
      .count {
        margin-left: 6px;
        font-size: 0.8em;
        opacity: 0.85;
      }
      .content {
        max-width: 1280px;
        margin: 0 auto;
        padding: 16px;
      }
    `,
  ];

  set hass(hass: HomeAssistant) {
    const first = !this._hass;
    this._hass = hass;
    if (first) {
      this.t = makeTranslate(hass.locale?.language ?? hass.language ?? "en");
      if (this.isConnected) void this.connect();
      this.requestUpdate();
    }
  }

  get hass(): HomeAssistant {
    return this._hass as HomeAssistant;
  }

  connectedCallback(): void {
    super.connectedCallback();
    if (this._hass && !this.unsubscribe) void this.connect();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    void this.unsubscribe?.();
    this.unsubscribe = undefined;
  }

  private async connect(): Promise<void> {
    if (this.connecting || this.unsubscribe) return;
    this.connecting = true;
    try {
      // Subscribe first: updates that race the snapshot are upserts, so nothing is lost.
      this.unsubscribe = await this.api.subscribe((event) => this.onEvent(event));
      const snap = await this.api.snapshot();
      this.interfaces = Object.fromEntries(snap.interfaces.map((i) => [i.id, i]));
      this.offline = snap.offline;
      this.periodic = Object.fromEntries(snap.periodic.map((p) => [p.id, p]));
      this.activity = snap.activity;
      if (!this.source || !(this.source in this.interfaces || snap.offline.some((o) => o.id === this.source))) {
        this.source = this.interfaceList[0]?.id ?? "";
      }
      this.loaded = true;
      this.error = "";
      void this.loadFiles();
    } catch (err) {
      this.error = errorText(err);
    } finally {
      this.connecting = false;
    }
  }

  private async loadFiles(): Promise<void> {
    try {
      const res = await this.api.captures();
      this.files = res.captures;
      this.offline = res.offline;
    } catch {
      /* shown again on the next change */
    }
  }

  private onEvent(event: FeedEvent): void {
    switch (event.kind) {
      case "interfaces": {
        const interfaces = { ...this.interfaces };
        const history = { ...this.history };
        for (const info of event.interfaces) {
          interfaces[info.id] = info;
          if (info.load.now != null) {
            history[info.id] = [...(history[info.id] ?? []), info.load.now].slice(-HISTORY_POINTS);
          }
        }
        for (const id of event.removed) delete interfaces[id];
        this.interfaces = interfaces;
        this.history = history;
        if (!this.source && event.interfaces.length) this.source = event.interfaces[0].id;
        break;
      }
      case "periodic": {
        const periodic = { ...this.periodic };
        for (const item of event.items) periodic[item.id] = item;
        for (const id of event.removed) delete periodic[id];
        this.periodic = periodic;
        break;
      }
      case "activity":
        this.activity = [...event.entries.reverse(), ...this.activity].slice(0, ACTIVITY_KEEP);
        break;
      case "captures":
        void this.loadFiles();
        break;
      case "offline":
        this.offline = event.offline;
        if (this.source.startsWith("file:") && !event.offline.some((o) => o.id === this.source)) {
          this.source = this.interfaceList[0]?.id ?? "";
        }
        break;
    }
  }

  private get interfaceList(): InterfaceInfo[] {
    return Object.values(this.interfaces).sort((a, b) => a.name.localeCompare(b.name));
  }

  private setTab(tab: Tab): void {
    this.tab = tab;
    storageSet("woow_can.tab", tab);
  }

  private setSource(source: string): void {
    this.source = source;
    storageSet("woow_can.source", source);
  }

  private toggleMenu(): void {
    this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true }));
  }

  private renderTab() {
    const interfaces = this.interfaceList;
    switch (this.tab) {
      case "monitor":
        return html`<woow-can-monitor
          .interfaces=${interfaces}
          .offline=${this.offline}
          .source=${this.source}
          .t=${this.t}
          .api=${this.api}
          @source-changed=${(e: CustomEvent<string>) => this.setSource(e.detail)}
          @send-frame=${(e: CustomEvent<{ frame: string; entryId: string }>) => {
            this.draft = { ...e.detail, n: (this.draft?.n ?? 0) + 1 };
            this.setTab("send");
          }}
        ></woow-can-monitor>`;
      case "send":
        return html`<woow-can-send
          .interfaces=${interfaces}
          .periodic=${Object.values(this.periodic)}
          .confirmed=${this.confirmed}
          .draft=${this.draft}
          .t=${this.t}
          .api=${this.api}
          @confirmed=${(e: CustomEvent<string>) => (this.confirmed = new Set([...this.confirmed, e.detail]))}
        ></woow-can-send>`;
      case "capture":
        return html`<woow-can-capture
          .interfaces=${interfaces}
          .offline=${this.offline}
          .files=${this.files}
          .t=${this.t}
          .api=${this.api}
          @captures-changed=${() => this.loadFiles()}
          @open-source=${(e: CustomEvent<string>) => {
            this.setSource(e.detail);
            this.setTab("monitor");
          }}
        ></woow-can-capture>`;
      case "activity":
        return html`<woow-can-activity
          .entries=${this.activity}
          .t=${this.t}
          .portName=${(id: string) => this.interfaces[id]?.name ?? "?"}
        ></woow-can-activity>`;
      default:
        return html`<woow-can-overview
          .interfaces=${interfaces}
          .history=${this.history}
          .t=${this.t}
          @open-monitor=${(e: CustomEvent<string>) => {
            this.setSource(e.detail);
            this.setTab("monitor");
          }}
        ></woow-can-overview>`;
    }
  }

  render() {
    const t = this.t;
    const counts: Partial<Record<Tab, number>> = {
      send: Object.values(this.periodic).filter((p) => p.running).length,
      capture: this.files.length,
    };
    return html`
      <div class="toolbar">
        ${this.narrow
          ? html`<button @click=${this.toggleMenu} aria-label="menu">
              <svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d=${MENU}></path></svg>
            </button>`
          : nothing}
        <div>${t("title")}</div>
      </div>
      <div class="tabs">
        ${TABS.map(
          (tab) => html`<button class="tab ${this.tab === tab ? "active" : ""}" @click=${() => this.setTab(tab)}>
            ${t(`tab_${tab}` as Key)}${counts[tab] ? html`<span class="count">${counts[tab]}</span>` : nothing}
          </button>`,
        )}
      </div>
      <div class="content">
        ${this.error
          ? html`<div class="card"><div class="chip bad">${t("error", { msg: this.error })}</div></div>`
          : this.loaded
            ? this.renderTab()
            : html`<div class="empty">${t("loading")}</div>`}
      </div>
    `;
  }
}

define("woow-can-panel", WoowCanPanel);
