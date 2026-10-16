// Send tab: one frame (optionally waiting for a reply ID), and the periodic sends.

import { LitElement, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import { Api, InterfaceInfo, Periodic, define, errorText } from "../api";
import { Translate } from "../i18n";
import { shared } from "../styles";

const value = (e: Event) => (e.target as HTMLInputElement).value;

interface Draft {
  id?: string;
  name: string;
  entry_id: string;
  frame: string;
  period_ms: number;
  count: number;
}

export class WoowCanSend extends LitElement {
  @property({ attribute: false }) interfaces: InterfaceInfo[] = [];
  @property({ attribute: false }) periodic: Periodic[] = [];
  @property({ attribute: false }) confirmed: Set<string> = new Set();
  @property({ attribute: false }) draft: { frame: string; entryId: string; n: number } | null = null;
  @property({ attribute: false }) t!: Translate;
  @property({ attribute: false }) api!: Api;

  @state() private entryId = "";
  @state() private frame = "";
  @state() private waitId = "";
  @state() private waitMs = 0;
  @state() private busy = false;
  @state() private result: { ok: boolean; text: string } | null = null;
  @state() private confirming = false;
  @state() private edit: Draft | null = null;
  @state() private editError = "";
  @state() private listError = "";
  private draftSeen = 0;

  static styles = [
    shared,
    css`
      .form {
        display: grid;
        grid-template-columns: minmax(8em, 1fr) minmax(12em, 3fr) minmax(6em, 1fr) minmax(6em, 1fr) auto;
        gap: 8px;
        align-items: end;
      }
      @media (max-width: 720px) {
        .form {
          grid-template-columns: 1fr 1fr;
        }
        .form .wide {
          grid-column: 1 / -1;
        }
      }
      label {
        display: grid;
        gap: 4px;
        font-size: 0.85em;
        color: var(--secondary-text-color);
      }
      label input,
      label select {
        font-size: 1.05em;
        color: var(--primary-text-color);
      }
      .result {
        margin-top: 10px;
        padding: 8px 10px;
        border-radius: 8px;
        background: rgba(67, 160, 71, 0.12);
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        white-space: pre-wrap;
      }
      .result.bad {
        background: rgba(219, 68, 55, 0.12);
        font-family: inherit;
      }
      .wrap {
        overflow-x: auto;
      }
      table {
        border-collapse: collapse;
        width: 100%;
      }
      th,
      td {
        text-align: left;
        padding: 6px 8px;
        border-bottom: 1px solid var(--divider-color, #eee);
        white-space: nowrap;
      }
      th {
        color: var(--secondary-text-color);
        font-weight: 500;
        font-size: 0.9em;
      }
      .scrim {
        position: fixed;
        inset: 0;
        z-index: 10;
        background: rgba(0, 0, 0, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 16px;
      }
      .dialog {
        width: min(460px, 100%);
        background: var(--card-background-color, #fff);
        border-radius: 12px;
        padding: 20px;
        display: grid;
        gap: 12px;
      }
      .dialog h2 {
        margin: 0;
        font-size: 1.15em;
        font-weight: 500;
      }
      .editor {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(10em, 1fr));
        gap: 8px;
        align-items: end;
        margin-top: 12px;
        padding: 12px;
        border-radius: 10px;
        background: var(--secondary-background-color, #f5f5f5);
      }
    `,
  ];

  protected willUpdate(changed: Map<string, unknown>): void {
    if (changed.has("draft") && this.draft && this.draft.n !== this.draftSeen) {
      this.draftSeen = this.draft.n;
      this.frame = this.draft.frame;
      if (this.draft.entryId) this.entryId = this.draft.entryId;
      this.result = null;
    }
    if (!this.entryId || !this.interfaces.some((i) => i.id === this.entryId)) {
      this.entryId = (this.interfaces.find((i) => i.can_send) ?? this.interfaces[0])?.id ?? "";
    }
  }

  private get iface(): InterfaceInfo | undefined {
    return this.interfaces.find((i) => i.id === this.entryId);
  }

  private whyNot(info: InterfaceInfo | undefined): string {
    if (!info) return "";
    if (!info.available) return this.t("why_unavailable");
    if (!info.can_send) return this.t("why_listen");
    return "";
  }

  private trySend(): void {
    if (!this.frame.trim() || !this.iface) return;
    if (!this.confirmed.has(this.entryId)) {
      this.confirming = true;
      return;
    }
    void this.send();
  }

  private async send(): Promise<void> {
    const t = this.t;
    this.confirming = false;
    this.dispatchEvent(new CustomEvent("confirmed", { detail: this.entryId }));
    this.busy = true;
    this.result = null;
    try {
      const res = await this.api.send(this.entryId, this.frame.trim(), this.waitMs, this.waitId.trim());
      let text = t("sent_ok", { frame: res.sent.frame });
      if (this.waitMs > 0 || this.waitId) {
        text += "\n" + (res.reply ? t("reply", { frame: res.reply.frame }) : t("no_reply"));
      }
      this.result = { ok: true, text };
    } catch (err) {
      this.result = { ok: false, text: t("error", { msg: errorText(err) }) };
    } finally {
      this.busy = false;
    }
  }

  // ---- periodic ----------------------------------------------------------------------------
  private newDraft(): void {
    this.editError = "";
    this.edit = { name: "", entry_id: this.entryId, frame: this.frame.trim(), period_ms: 1000, count: 0 };
  }

  private async saveDraft(): Promise<void> {
    if (!this.edit) return;
    try {
      await this.api.savePeriodic(this.edit);
      this.edit = null;
      this.editError = "";
    } catch (err) {
      this.editError = errorText(err);
    }
  }

  private async control(item: Periodic, action: "start" | "stop" | "delete"): Promise<void> {
    this.listError = "";
    try {
      await this.api.controlPeriodic(item.id, action);
    } catch (err) {
      this.listError = `${item.name}: ${errorText(err)}`;
    }
  }

  private state(item: Periodic): string {
    const t = this.t;
    if (item.running) return t("running");
    if (item.stopped_by === "count") return t("stopped_by_count");
    if (item.stopped_by === "error") return t("stopped_by_error", { x: item.error ?? "?" });
    if (item.stopped_by === "interface") return t("stopped_by_interface");
    return t("stopped");
  }

  private renderEditor() {
    const t = this.t;
    const d = this.edit;
    if (!d) return nothing;
    const set = (patch: Partial<Draft>) => (this.edit = { ...d, ...patch });
    return html`<div class="editor">
      <label>${t("name")}<input .value=${d.name} @input=${(e: Event) => set({ name: value(e) })} /></label>
      <label>${t("interface")}
        <select @change=${(e: Event) => set({ entry_id: value(e) })}>
          ${this.interfaces.map((i) => html`<option value=${i.id} ?selected=${i.id === d.entry_id}>${i.name}</option>`)}
        </select>
      </label>
      <label>${t("frame")}<input class="mono" placeholder=${t("frame_ph")} .value=${d.frame}
        @input=${(e: Event) => set({ frame: value(e) })} /></label>
      <label>${t("period_ms")}<input type="number" min="10" .value=${String(d.period_ms)}
        @input=${(e: Event) => set({ period_ms: Number(value(e)) })} /></label>
      <label>${t("count")}<input type="number" min="0" .value=${String(d.count)}
        @input=${(e: Event) => set({ count: Number(value(e)) })} /></label>
      <div class="row">
        <button class="primary" @click=${() => this.saveDraft()}>${t("save")}</button>
        <button @click=${() => (this.edit = null)}>${t("cancel")}</button>
      </div>
      ${this.editError ? html`<div class="chip bad" style="white-space:normal">${this.editError}</div>` : nothing}
    </div>`;
  }

  render() {
    const t = this.t;
    const info = this.iface;
    const why = this.whyNot(info);
    const name = (id: string) => this.interfaces.find((i) => i.id === id)?.name ?? "?";
    return html`<div class="card">
        <h2>${t("send_title")}</h2>
        <div class="form">
          <label>${t("interface")}
            <select @change=${(e: Event) => (this.entryId = value(e))}>
              ${this.interfaces.map((i) => html`<option value=${i.id} ?selected=${i.id === this.entryId}>
                ${i.name}${i.can_send ? "" : ` (${t("listen_only")})`}</option>`)}
            </select>
          </label>
          <label class="wide">${t("frame")}
            <input class="mono" placeholder=${t("frame_ph")} .value=${this.frame}
              @input=${(e: Event) => (this.frame = value(e))}
              @keydown=${(e: KeyboardEvent) => e.key === "Enter" && this.trySend()} />
          </label>
          <label>${t("wait_id")}<input class="mono" placeholder="7E8" .value=${this.waitId}
            @input=${(e: Event) => (this.waitId = value(e))} /></label>
          <label>${t("wait_ms")}<input type="number" min="0" step="100" .value=${String(this.waitMs)}
            @input=${(e: Event) => (this.waitMs = Math.max(0, Number(value(e)) || 0))} /></label>
          <button class="primary" ?disabled=${this.busy || !!why || !this.frame.trim()} @click=${() => this.trySend()}>
            ${t("send")}
          </button>
        </div>
        <p class="muted">${t("frame_help")}</p>
        ${why && info ? html`<div class="chip warn" style="white-space:normal">${t("cannot_send", { name: info.name, why })}</div>` : nothing}
        ${this.result ? html`<div class="result ${this.result.ok ? "" : "bad"}">${this.result.text}</div>` : nothing}
      </div>
      <div class="card">
        <div class="row">
          <h2 class="grow">${t("periodic_title")}</h2>
          <button @click=${() => this.newDraft()}>${t("add")}</button>
        </div>
        <div class="muted">${t("periodic_hint")}</div>
        ${this.renderEditor()}
        ${this.listError ? html`<div class="chip bad" style="white-space:normal">${this.listError}</div>` : nothing}
        ${this.periodic.length === 0
          ? html`<div class="empty">${t("periodic_empty")}</div>`
          : html`<div class="wrap"><table>
              <thead><tr>
                <th>${t("name")}</th><th>${t("interface")}</th><th>${t("frame")}</th><th>${t("period_ms")}</th>
                <th>${t("count")}</th><th></th><th></th>
              </tr></thead>
              <tbody>
                ${this.periodic.map((item) => html`<tr>
                  <td>${item.name}</td>
                  <td>${name(item.entry_id)}</td>
                  <td class="mono">${item.frame}</td>
                  <td>${item.period_ms}</td>
                  <td>${item.count || "∞"}</td>
                  <td>
                    <span class="chip ${item.running ? "ok" : item.stopped_by === "error" ? "bad" : ""}">${this.state(item)}</span>
                    <span class="muted">${t("sent_n", { n: item.sent })}</span>
                  </td>
                  <td class="row">
                    ${item.running
                      ? html`<button @click=${() => this.control(item, "stop")}>${t("stop")}</button>`
                      : html`<button class="primary" @click=${() => this.control(item, "start")}>${t("start")}</button>`}
                    <button class="link" @click=${() => {
                      this.editError = "";
                      this.edit = { id: item.id, name: item.name, entry_id: item.entry_id, frame: item.frame,
                                    period_ms: item.period_ms, count: item.count };
                    }}>${t("edit")}</button>
                    <button class="link danger" @click=${() => this.control(item, "delete")}>${t("delete")}</button>
                  </td>
                </tr>`)}
              </tbody>
            </table></div>`}
      </div>
      ${this.confirming && info
        ? html`<div class="scrim" @click=${(e: Event) => e.target === e.currentTarget && (this.confirming = false)}>
            <div class="dialog">
              <h2>${t("confirm_title", { name: info.name })}</h2>
              <div class="mono">${this.frame}</div>
              <div>${t("confirm_text")}</div>
              <div class="row">
                <span class="grow"></span>
                <button @click=${() => (this.confirming = false)}>${t("cancel")}</button>
                <button class="primary" @click=${() => this.send()}>${t("confirm_ok")}</button>
              </div>
            </div>
          </div>`
        : nothing}`;
  }
}

define("woow-can-send", WoowCanSend);
