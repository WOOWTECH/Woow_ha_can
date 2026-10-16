// Devices tab: devices made from templates or DBC files, their live values and entities, charts of chosen
// signals, the template picker and the imported DBC files.

import { LitElement, css, html, nothing, svg } from "lit";
import { property, state } from "lit/decorators.js";

import {
  Api,
  DatabaseSummary,
  DeviceView,
  InterfaceInfo,
  SignalStatus,
  TemplateSummary,
  Values,
  define,
  errorText,
} from "../api";
import { Key, Translate, isKey } from "../i18n";
import { shared } from "../styles";

const value = (e: Event) => (e.target as HTMLInputElement).value;
const checked = (e: Event) => (e.target as HTMLInputElement).checked;
export const MAX_CHARTS = 8;

export function formatValue(v: unknown, unit = ""): string {
  if (v === null || v === undefined) return "–";
  if (typeof v === "boolean") return v ? "on" : "off";
  if (typeof v === "number") {
    const text = Number.isInteger(v) ? String(v) : String(parseFloat(v.toFixed(3)));
    return unit ? `${text} ${unit.replace("degC", "°C").replace("degF", "°F")}` : text;
  }
  return String(v);
}

interface Draft {
  template: string;
  entryId: string;
  name: string;
  params: Record<string, string>;
  auto: boolean;
  groups: string[];
}

export class WoowCanDevices extends LitElement {
  @property({ attribute: false }) interfaces: InterfaceInfo[] = [];
  @property({ attribute: false }) devices: DeviceView[] = [];
  @property({ attribute: false }) values: Values = {};
  @property({ attribute: false }) history: Record<string, [number, number][]> = {};
  @property({ attribute: false }) charts: string[] = [];
  @property({ attribute: false }) templates: TemplateSummary[] = [];
  @property({ attribute: false }) databases: DatabaseSummary[] = [];
  @property({ attribute: false }) preferredInterface = "";
  @property({ attribute: false }) t!: Translate;
  @property({ attribute: false }) api!: Api;

  @state() private open = "";
  @state() private draft: Draft | null = null;
  @state() private busy = false;
  @state() private message: { ok: boolean; text: string } | null = null;
  @state() private deleting = "";
  @state() private confirming = ""; // "<device id>|active" or "|allow_write" waiting for confirmation
  @state() private numbers: Record<string, string> = {}; // number inputs being typed
  @state() private settingsFor = "";
  @state() private settings: { min_interval: string; tolerance: string; timeout: string } = {
    min_interval: "", tolerance: "", timeout: "" };
  @state() private dbcDevice: { name: string; entryId: string; deviceName: string; messages: string[] } | null = null;

  static styles = [
    shared,
    css`
      .devices {
        display: grid;
        gap: 12px;
      }
      .device {
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 10px;
        padding: 10px 12px;
        display: grid;
        gap: 6px;
      }
      .device h3 {
        margin: 0;
        font-size: 1.05em;
        font-weight: 500;
      }
      .msg {
        border-top: 1px solid var(--divider-color, #eee);
        padding-top: 6px;
        margin-top: 4px;
      }
      .wrap {
        overflow-x: auto;
      }
      table {
        border-collapse: collapse;
        width: 100%;
        font-size: 0.92em;
        table-layout: fixed;
        min-width: 640px;
      }
      col.c-adopt {
        width: 32px;
      }
      col.c-name {
        width: 26%;
      }
      col.c-value {
        width: 16%;
      }
      col.c-actions {
        width: 110px;
      }
      table.writing col.c-value {
        width: 30%;
      }
      td.val button {
        padding: 2px 10px;
        margin-right: 4px;
      }
      td {
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .off-entity {
        color: var(--secondary-text-color);
      }
      td,
      th {
        padding: 4px 8px;
        text-align: left;
        border-bottom: 1px solid var(--divider-color, #f0f0f0);
        white-space: nowrap;
        vertical-align: middle;
      }
      th {
        color: var(--secondary-text-color);
        font-weight: 500;
      }
      td.val {
        font-variant-numeric: tabular-nums;
        font-weight: 500;
      }
      .charts {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(min(100%, 260px), 1fr));
        gap: 12px;
      }
      .chart {
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 10px;
        padding: 8px 10px;
        display: grid;
        gap: 2px;
      }
      .chart b {
        font-size: 1.3em;
        font-variant-numeric: tabular-nums;
      }
      svg.line {
        width: 100%;
        height: 60px;
        display: block;
      }
      svg.line polyline {
        fill: none;
        stroke: var(--primary-color);
        stroke-width: 1.5;
      }
      svg.line line {
        stroke: var(--divider-color, #ddd);
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
        width: min(860px, 100%);
        max-height: 90vh;
        overflow: auto;
        background: var(--card-background-color, #fff);
        border-radius: 12px;
        padding: 20px;
        display: grid;
        grid-template-columns: minmax(180px, 1fr) 2fr;
        gap: 16px;
      }
      @media (max-width: 640px) {
        .dialog {
          grid-template-columns: 1fr;
        }
      }
      .tpl {
        display: block;
        width: 100%;
        text-align: left;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 8px;
        padding: 8px 10px;
        margin-bottom: 6px;
        background: none;
      }
      .tpl.on {
        border-color: var(--primary-color);
        background: rgba(3, 169, 244, 0.06);
      }
      label.field {
        display: grid;
        gap: 4px;
        font-size: 0.85em;
        color: var(--secondary-text-color);
      }
      label.field input,
      label.field select {
        font-size: 1.05em;
        color: var(--primary-text-color);
      }
      .form {
        display: grid;
        gap: 10px;
        align-content: start;
      }
      details summary {
        cursor: pointer;
        color: var(--secondary-text-color);
      }
      .confirm {
        display: flex;
        flex-wrap: wrap;
        gap: 6px 10px;
        align-items: center;
        padding: 8px 10px;
        border: 1px solid var(--warning-color, #f0ad4e);
        border-radius: 8px;
        margin: 4px 0;
      }
      .toggle-line {
        gap: 6px;
        margin-right: 16px;
      }
      .inline {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: end;
        padding: 8px;
        border-radius: 8px;
        background: var(--secondary-background-color, #f5f5f5);
      }
      .inline input {
        width: 7em;
      }
      input[type="file"] {
        display: none;
      }
      a.entity {
        color: var(--primary-color);
        cursor: pointer;
        text-decoration: none;
      }
    `,
  ];

  private iname = (id: string) => this.interfaces.find((i) => i.id === id)?.name ?? "?";

  private async run(task: () => Promise<unknown>, ok?: string): Promise<boolean> {
    this.busy = true;
    try {
      await task();
      this.message = ok ? { ok: true, text: ok } : null;
      return true;
    } catch (err) {
      this.message = { ok: false, text: this.t("error", { msg: errorText(err) }) };
      return false;
    } finally {
      this.busy = false;
    }
  }

  private moreInfo(entityId: string): void {
    this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));
  }

  private toggleChart(key: string): void {
    this.dispatchEvent(new CustomEvent("toggle-chart", { detail: key }));
  }

  // ---- template dialog --------------------------------------------------------------------
  private startTemplate(): void {
    const first = this.templates[0];
    const entry = this.interfaces.find((i) => i.id === this.preferredInterface) ?? this.interfaces[0];
    this.draft = first ? this.draftFor(first, entry?.id ?? "") : null;
    this.message = null;
  }

  private draftFor(tpl: TemplateSummary, entryId: string): Draft {
    return {
      template: tpl.id,
      entryId,
      name: "",
      params: Object.fromEntries(tpl.params.map((p) => [p.key, p.default === null || p.default === undefined ? "" : String(p.default)])),
      auto: true,
      groups: [],
    };
  }

  private async createFromTemplate(): Promise<void> {
    const d = this.draft;
    if (!d) return;
    const tpl = this.templates.find((x) => x.id === d.template);
    const params: Record<string, unknown> = {};
    for (const p of tpl?.params ?? []) {
      const raw = d.params[p.key] ?? "";
      params[p.key] = typeof p.default === "number" && raw !== "" && !isNaN(Number(raw)) ? Number(raw) : raw;
    }
    let made: DeviceView | null = null;
    const ok = await this.run(async () => {
      made = await this.api.createFromTemplate(d.template, d.entryId, d.name, params, d.auto ? null : d.groups);
    });
    if (ok && made) {
      this.draft = null;
      this.open = (made as DeviceView).id;
      this.message = { ok: true, text: this.t("created_device", { name: (made as DeviceView).name }) };
    }
  }

  private renderTemplateDialog() {
    const d = this.draft;
    if (!d) return nothing;
    const t = this.t;
    const tpl = this.templates.find((x) => x.id === d.template);
    const set = (patch: Partial<Draft>) => (this.draft = { ...d, ...patch });
    const label = (prefix: string, v: string) => (isKey(`${prefix}_${v}`) ? t(`${prefix}_${v}` as Key) : v);
    return html`<div class="scrim" @click=${(e: Event) => e.target === e.currentTarget && (this.draft = null)}>
      <div class="dialog">
        <div>
          ${this.templates.map((x) => html`<button class="tpl ${x.id === d.template ? "on" : ""}"
            @click=${() => (this.draft = this.draftFor(x, d.entryId))}>
            <div><b>${x.name}</b></div>
            <div class="muted">${label("category", x.category)} · ${label("confidence", x.confidence)}</div>
          </button>`)}
        </div>
        ${tpl
          ? html`<div class="form">
              <h2 style="margin:0;font-size:1.15em;font-weight:500">${tpl.name}</h2>
              <div>${tpl.description}</div>
              ${tpl.notes ? html`<div class="muted">${tpl.notes}</div>` : nothing}
              <div class="row">
                ${tpl.transmits
                  ? html`<span class="chip warn">${t("sends_when_on")}</span>`
                  : html`<span class="chip ok">${t("only_listens")}</span>`}
                <span class="chip">${t("confidence", { x: label("confidence", tpl.confidence) })}</span>
                ${tpl.bitrate ? html`<span class="chip">${t("kbps", { n: tpl.bitrate / 1000 })}</span>` : nothing}
              </div>
              <div class="muted">${t("verified_with", { x: tpl.verified.join("；") })}</div>
              <details>
                <summary>${t("sources")}</summary>
                <ul>${tpl.source.map((s) => html`<li>${s}</li>`)}</ul>
                <div class="muted">${t("license_x", { x: tpl.license })}</div>
              </details>
              <label class="field">${t("interface")}
                <select @change=${(e: Event) => set({ entryId: value(e) })}>
                  ${this.interfaces.map((i) => html`<option value=${i.id} ?selected=${i.id === d.entryId}>${i.name} · ${i.port}</option>`)}
                </select>
              </label>
              <label class="field">${t("device_name")}
                <input .value=${d.name} placeholder=${tpl.default_name} @input=${(e: Event) => set({ name: value(e) })} />
              </label>
              ${tpl.params.map((p) => html`<label class="field">${p.key} — ${p.description}
                <input .value=${d.params[p.key] ?? ""} @input=${(e: Event) => set({ params: { ...d.params, [p.key]: value(e) } })} />
              </label>`)}
              ${tpl.groups.length
                ? html`<div>
                    <div class="muted">${t("groups_title")}</div>
                    <label class="row"><input type="checkbox" .checked=${d.auto}
                      @change=${(e: Event) => set({ auto: checked(e) })} />${t("groups_auto")}</label>
                    ${d.auto
                      ? html`<div class="muted">${t("groups_detect_hint")}</div>`
                      : tpl.groups.map((g) => html`<label class="row"><input type="checkbox" .checked=${d.groups.includes(g.id)}
                          @change=${(e: Event) => set({ groups: checked(e) ? [...d.groups, g.id] : d.groups.filter((x) => x !== g.id) })} />
                          ${g.name}</label>`)}
                  </div>`
                : nothing}
              ${this.message && !this.message.ok ? html`<div class="chip bad" style="white-space:normal">${this.message.text}</div>` : nothing}
              <div class="row">
                <span class="grow"></span>
                <button @click=${() => (this.draft = null)}>${t("cancel")}</button>
                <button class="primary" ?disabled=${this.busy || !d.entryId} @click=${() => this.createFromTemplate()}>${t("create")}</button>
              </div>
            </div>`
          : nothing}
      </div>
    </div>`;
  }

  // ---- devices ---------------------------------------------------------------------------
  private async adopt(device: DeviceView, msg: string, sig: SignalStatus, on: boolean): Promise<void> {
    await this.run(() => this.api.setSignal(device.id, msg, sig.name, { adopted: on }));
  }

  private openSettings(device: DeviceView, msg: string, sig: string): void {
    const key = `${device.id}|${msg}.${sig}`;
    if (this.settingsFor === key) {
      this.settingsFor = "";
      return;
    }
    const def = device.definition?.messages.find((m) => m.name === msg)?.signals.find((s) => s.name === sig);
    const e = def?.entity ?? {};
    this.settings = {
      min_interval: e.min_interval !== undefined ? String(e.min_interval) : "",
      tolerance: e.tolerance !== undefined ? String(e.tolerance) : "",
      timeout: e.timeout !== undefined ? String(e.timeout) : "",
    };
    this.settingsFor = key;
  }

  private async applySettings(device: DeviceView, msg: string, sig: string): Promise<void> {
    const entity: Record<string, number | null> = {};
    for (const k of ["min_interval", "tolerance", "timeout"] as const) {
      const raw = this.settings[k].trim();
      entity[k] = raw === "" ? null : Number(raw);
    }
    if (await this.run(() => this.api.setSignal(device.id, msg, sig, { entity: entity as never }))) this.settingsFor = "";
  }

  // ---- polling, writing -----------------------------------------------------------------
  private async setOption(device: DeviceView, what: "active" | "allow_write", on: boolean): Promise<void> {
    this.confirming = "";
    await this.run(() => this.api.deviceOptions(device.id, { [what]: on }));
  }

  private renderControls(device: DeviceView) {
    const t = this.t;
    if (!device.has_requests && !device.writable) return nothing;
    const toggle = (what: "active" | "allow_write", label: string, on: boolean) => {
      const key = `${device.id}|${what}`;
      if (this.confirming === key) {
        return html`<div class="confirm">
          <span>${t(what === "active" ? "confirm_polling" : "confirm_writing", { name: device.name, iface: this.iname(device.interface) })}</span>
          <button class="primary" ?disabled=${this.busy} @click=${() => this.setOption(device, what, true)}>${t("turn_on")}</button>
          <button @click=${() => (this.confirming = "")}>${t("cancel")}</button>
        </div>`;
      }
      return html`<label class="row toggle-line"><input type="checkbox" .checked=${on} ?disabled=${this.busy}
        @change=${(e: Event) => {
          if (checked(e)) {
            (e.target as HTMLInputElement).checked = false;
            this.confirming = key;
          } else void this.setOption(device, what, false);
        }} />${label}</label>`;
    };
    const requests = device.requests ?? [];
    return html`<div class="msg">
      <div class="row">
        ${device.has_requests ? toggle("active", t("polling"), !!device.active) : nothing}
        ${device.writable ? toggle("allow_write", t("writing"), !!device.allow_write) : nothing}
      </div>
      ${requests.length
        ? html`<div class="wrap"><table><tbody>${requests.map((r) => html`<tr>
            <td>${r.name}</td>
            <td class="muted">${t("req_period", { ms: r.period_ms })}${r.effective_ms > r.period_ms
              ? html` · <span style="color:var(--warning-color)">${t("req_slowed", { ms: r.effective_ms })}</span>` : nothing}</td>
            <td class="muted">${t("req_counts", { sent: r.sent, replies: r.replies })}</td>
            <td><span class="chip ${r.state === "ok" ? "ok" : r.state === "waiting" ? "" : "warn"}"
              title=${r.error ?? ""}>${t(`req_${r.state}` as Key)}</span></td>
          </tr>`)}</tbody></table></div>`
        : nothing}
    </div>`;
  }

  private writeControl(device: DeviceView, message: string, s: SignalStatus, current: unknown) {
    const t = this.t;
    const w = s.write!;
    const write = (v: unknown) =>
      this.run(async () => {
        const res = await this.api.writeSignal(device.id, message, s.name, v);
        this.message = { ok: true, text: t("written", { data: res.data }) };
      });
    switch (w.platform) {
      case "switch":
        return html`<button class=${current === w.on ? "primary" : ""} ?disabled=${this.busy} @click=${() => write(w.on ?? 1)}>${t("write_on")}</button>
          <button class=${current === w.off ? "primary" : ""} ?disabled=${this.busy} @click=${() => write(w.off ?? 0)}>${t("write_off")}</button>`;
      case "button":
        return html`<button ?disabled=${this.busy} @click=${() => write(w.press)}>${t("write_press")}</button>`;
      case "select":
        return html`<select ?disabled=${this.busy} @change=${(e: Event) => write(value(e))}>
          ${(w.options ?? []).map((o) => html`<option value=${o} ?selected=${o === current}>${o}</option>`)}
        </select>`;
      default: {
        const key = `${device.id}|${message}.${s.name}`;
        return html`<input type="number" style="width:90px" min=${w.min ?? ""} max=${w.max ?? ""} step=${w.step ?? "any"}
            .value=${this.numbers[key] ?? (typeof current === "number" ? String(current) : "")}
            @input=${(e: Event) => (this.numbers = { ...this.numbers, [key]: value(e) })} />
          <button ?disabled=${this.busy || this.numbers[key] === undefined}
            @click=${() => write(parseFloat(this.numbers[key]))}>${t("write_set")}</button>`;
      }
    }
  }

  private renderDevice(device: DeviceView) {
    const t = this.t;
    const live = this.values[device.id] ?? {};
    const status = device.status;
    const adopted = status.reduce((n, m) => n + m.signals.filter((s) => s.adopted).length, 0);
    const received = status.filter((m) => !m.send);
    const fresh = received.filter((m) => m.fresh === true).length;
    const stale = received.filter((m) => m.fresh === false && m.seen_s_ago !== null).length;
    const never = received.filter((m) => m.seen_s_ago === null).length;
    const open = this.open === device.id;
    return html`<div class="device">
      <div class="row">
        <h3>${device.name}</h3>
        <span class="chip">${this.iname(device.interface)}</span>
        ${device.template ? html`<span class="chip info">${this.templates.find((x) => x.id === device.template)?.name ?? device.template}</span>` : nothing}
        ${device.source.startsWith("dbc:") ? html`<span class="chip info">${device.source.slice(4)}</span>` : nothing}
        ${device.active ? html`<span class="chip warn">${t("polling_chip")}</span>` : nothing}
        ${device.allow_write ? html`<span class="chip bad">${t("writing_chip")}</span>` : nothing}
        <span class="grow"></span>
        <button class="link" @click=${() => (this.open = open ? "" : device.id)}>${open ? "▲" : "▼"}</button>
      </div>
      <div class="muted">
        ${t("messages_n", { n: status.length })} · ${t("entities_n", { n: adopted })}
        ${fresh ? html` · <span class="rx">${fresh} ${t("fresh")}</span>` : nothing}
        ${stale ? html` · <span style="color:var(--warning-color)">${stale} ${t("stale")}</span>` : nothing}
        ${never ? html` · ${never} ${t("never_seen")}` : nothing}
      </div>
      ${open
        ? html`${this.renderControls(device)}${status.map((m) => html`<div class="msg">
              <div class="row">
                <b>${m.name}</b><span class="muted mono">${m.id}</span>
                ${m.send
                  ? html`<span class="chip info">${t("sent_from_here")}</span>`
                  : html`<span class="chip ${m.fresh === true ? "ok" : m.fresh === false && m.seen_s_ago !== null ? "warn" : ""}">
                      ${m.seen_s_ago === null ? t("never_seen") : m.fresh === false ? t("stale") : t("fresh")}</span>`}
              </div>
              <div class="wrap"><table class=${device.allow_write && m.signals.some((x) => x.write) ? "writing" : ""}>
                <colgroup><col class="c-adopt" /><col class="c-name" /><col class="c-value" /><col /><col class="c-actions" /></colgroup>
                <tbody>
                  ${m.signals.map((s) => {
                    const key = `${m.name}.${s.name}`;
                    const v = key in live ? live[key] : s.value;
                    const chartKey = `${device.id}|${key}`;
                    const numeric = typeof v === "number" && (s.platform === "sensor" || s.platform === "number");
                    const writing = !!s.write && !!device.allow_write;
                    return html`<tr>
                        <td><input type="checkbox" title=${t("adopt_hint")} .checked=${s.adopted}
                          @change=${(e: Event) => this.adopt(device, m.name, s, checked(e))} /></td>
                        <td>${s.name}</td>
                        <td class="val">${writing
                          ? this.writeControl(device, m.name, s, v)
                          : (s.platform === "binary_sensor" || s.platform === "switch") && (v === 0 || v === 1 || typeof v === "boolean")
                            ? (v === 1 || v === true ? t("state_on") : t("state_off"))
                            : formatValue(v, s.unit)}</td>
                        <td title=${s.entity_id ?? ""}>${s.entity_id
                          ? s.disabled
                            ? html`<span class="off-entity">${s.entity_id} · ${t("entity_disabled")}</span>`
                            : html`<a class="entity" @click=${() => this.moreInfo(s.entity_id as string)}>${s.entity_id}</a>`
                          : nothing}</td>
                        <td class="row">
                          ${numeric || this.charts.includes(chartKey)
                            ? html`<button class="link" @click=${() => this.toggleChart(chartKey)}>
                                ${this.charts.includes(chartKey) ? "✓ " : ""}${t("chart")}</button>`
                            : nothing}
                          ${s.adopted ? html`<button class="link" @click=${() => this.openSettings(device, m.name, s.name)}>${t("settings")}</button>` : nothing}
                        </td>
                      </tr>
                      ${this.settingsFor === chartKey
                        ? html`<tr><td colspan="5"><div class="inline">
                            ${(["min_interval", "tolerance", "timeout"] as const).map((k) => html`<label class="field">
                              ${t((k === "timeout" ? "timeout_s" : k) as Key)}
                              <input type="number" step="any" .value=${this.settings[k]}
                                @input=${(e: Event) => (this.settings = { ...this.settings, [k]: value(e) })} /></label>`)}
                            <button class="primary" @click=${() => this.applySettings(device, m.name, s.name)}>${t("apply")}</button>
                          </div></td></tr>`
                        : nothing}`;
                  })}
                </tbody>
              </table></div>
            </div>`)}
            <div class="row">
              <button class="link" @click=${() => this.run(() => this.api.download(`/api/woow_can/devices/${device.id}/dbc`))}>
                ${t("download_dbc")}</button>
              <span class="grow"></span>
              ${this.deleting === device.id
                ? html`<span>${t("delete_device_confirm", { name: device.name })}</span>
                    <button class="danger" @click=${() => this.run(async () => {
                      this.deleting = "";
                      await this.api.deleteDevice(device.id);
                    })}>${t("delete")}</button>
                    <button @click=${() => (this.deleting = "")}>${t("cancel")}</button>`
                : html`<button class="link danger" @click=${() => (this.deleting = device.id)}>${t("delete")}</button>`}
            </div>`
        : nothing}
    </div>`;
  }

  // ---- charts ----------------------------------------------------------------------------
  private renderCharts() {
    const t = this.t;
    if (!this.charts.length) return nothing;
    return html`<div class="card">
      <div class="row"><h2 class="grow">${t("charts_title")}</h2></div>
      <div class="charts">
        ${this.charts.map((key) => {
          const [deviceId, sigKey] = key.split("|");
          const device = this.devices.find((d) => d.id === deviceId);
          const points = this.history[key] ?? [];
          let unit = "";
          for (const m of device?.status ?? []) for (const s of m.signals) if (`${m.name}.${s.name}` === sigKey) unit = s.unit;
          const current = this.values[deviceId]?.[sigKey];
          const vals = points.map((p) => p[1]);
          const lo = vals.length ? Math.min(...vals) : 0;
          const hi = vals.length ? Math.max(...vals) : 1;
          const span = hi - lo || 1;
          const t0 = points.length ? points[0][0] : 0;
          const t1 = points.length ? points[points.length - 1][0] : 1;
          const tspan = t1 - t0 || 1;
          const xy = points.map(([tt, v]) => `${(((tt - t0) / tspan) * 300).toFixed(1)},${(56 - ((v - lo) / span) * 52).toFixed(1)}`);
          return html`<div class="chart">
            <div class="row"><span class="muted grow">${device?.name ?? "?"} · ${sigKey}</span>
              <button class="link" @click=${() => this.toggleChart(key)}>✕</button></div>
            <b>${formatValue(current, unit)}</b>
            <svg class="line" viewBox="0 0 300 60" preserveAspectRatio="none">
              ${svg`<line x1="0" y1="58" x2="300" y2="58"></line>`}
              ${xy.length > 1 ? svg`<polyline points=${xy.join(" ")}></polyline>` : nothing}
            </svg>
            <div class="muted">${vals.length ? `${formatValue(lo)} – ${formatValue(hi)}` : ""}</div>
          </div>`;
        })}
      </div>
    </div>`;
  }

  // ---- DBC files ------------------------------------------------------------------------
  private async upload(e: Event): Promise<void> {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = "";
    if (!file) return;
    const attach = this.preferredInterface && this.interfaces.some((i) => i.id === this.preferredInterface)
      ? [this.preferredInterface] : [];
    await this.run(async () => {
      const summary = await this.api.uploadDbc(file, attach);
      this.message = { ok: true, text: this.t("imported_dbc", { name: summary.name, m: summary.messages, s: summary.signals }) };
    });
  }

  private async setAttach(db: DatabaseSummary, id: string, on: boolean): Promise<void> {
    const next = on ? [...db.attached.filter((x) => x !== id), id] : db.attached.filter((x) => x !== id);
    await this.run(() => this.api.dbc("attach", db.name, { interfaces: next }));
  }

  private async createFromDbc(): Promise<void> {
    const d = this.dbcDevice;
    if (!d) return;
    const ok = await this.run(() => this.api.dbc("create_device", d.name, {
      entry_id: d.entryId, device_name: d.deviceName, messages: d.messages.length ? d.messages : undefined }));
    if (ok) this.dbcDevice = null;
  }

  private renderDatabases() {
    const t = this.t;
    return html`<div class="card">
      <div class="row">
        <h2 class="grow">${t("dbc_title")}</h2>
        <button @click=${() => (this.renderRoot.querySelector("#dbc") as HTMLInputElement)?.click()}>${t("import_dbc")}</button>
        <input id="dbc" type="file" accept=".dbc" @change=${this.upload} />
      </div>
      <div class="muted">${t("dbc_hint")}</div>
      ${this.databases.length === 0
        ? html`<div class="empty">${t("dbc_empty")}</div>`
        : this.databases.map((db) => html`<div class="device" style="margin-top:10px">
            <div class="row">
              <b class="mono">${db.name}</b>
              <span class="muted">${t("messages_n", { n: db.messages })} · ${db.signals}</span>
              ${db.warning_count ? html`<details><summary>${t("dbc_warnings", { n: db.warning_count })}</summary>
                <ul>${db.warnings.map((w) => html`<li class="mono">${w}</li>`)}</ul></details>` : nothing}
              <span class="grow"></span>
              <button class="link" @click=${() => this.api.download(`/api/woow_can/dbc/${encodeURIComponent(db.name)}`)}>${t("download")}</button>
              <button class="link" @click=${() => (this.dbcDevice = { name: db.name, entryId: this.preferredInterface || this.interfaces[0]?.id || "",
                deviceName: "", messages: [] })}>${t("make_device")}</button>
              <button class="link danger" @click=${() => this.run(() => this.api.dbc("delete", db.name))}>${t("delete")}</button>
            </div>
            <div class="row">
              <span class="muted">${t("dbc_attached_to")}:</span>
              <label class="row"><input type="checkbox" .checked=${db.attached.includes("*")}
                @change=${(e: Event) => this.setAttach(db, "*", checked(e))} />${t("all_interfaces")}</label>
              ${this.interfaces.map((i) => html`<label class="row"><input type="checkbox" .checked=${db.attached.includes(i.id)}
                @change=${(e: Event) => this.setAttach(db, i.id, checked(e))} />${i.name}</label>`)}
            </div>
            ${this.dbcDevice?.name === db.name
              ? html`<div class="inline">
                  <label class="field">${t("interface")}
                    <select @change=${(e: Event) => (this.dbcDevice = { ...this.dbcDevice!, entryId: value(e) })}>
                      ${this.interfaces.map((i) => html`<option value=${i.id} ?selected=${i.id === this.dbcDevice!.entryId}>${i.name}</option>`)}
                    </select></label>
                  <label class="field">${t("device_name")}<input .value=${this.dbcDevice.deviceName} placeholder=${db.name.replace(/\.dbc$/i, "")}
                    @input=${(e: Event) => (this.dbcDevice = { ...this.dbcDevice!, deviceName: value(e) })} /></label>
                  <div>
                    <div class="muted">${t("choose_messages")}</div>
                    ${db.message_names.map((n) => html`<label class="row"><input type="checkbox" .checked=${this.dbcDevice!.messages.includes(n)}
                      @change=${(e: Event) => (this.dbcDevice = { ...this.dbcDevice!, messages: checked(e)
                        ? [...this.dbcDevice!.messages, n] : this.dbcDevice!.messages.filter((x) => x !== n) })} />
                      <span class="mono">${n}</span></label>`)}
                  </div>
                  <button class="primary" ?disabled=${this.busy} @click=${() => this.createFromDbc()}>${t("create")}</button>
                  <button @click=${() => (this.dbcDevice = null)}>${t("cancel")}</button>
                </div>`
              : nothing}
          </div>`)}
    </div>`;
  }

  render() {
    const t = this.t;
    return html`<div class="card">
        <div class="row">
          <h2 class="grow">${t("tab_devices")}</h2>
          <button class="primary" ?disabled=${!this.templates.length || !this.interfaces.length} @click=${() => this.startTemplate()}>
            ${t("add_from_template")}</button>
        </div>
        <div class="muted">${t("devices_hint")}</div>
        ${this.message && !this.draft ? html`<div class="chip ${this.message.ok ? "ok" : "bad"}" style="margin-top:8px;white-space:normal">${this.message.text}</div>` : nothing}
        ${this.devices.length === 0
          ? html`<div class="empty">${t("devices_empty")}</div>`
          : html`<div class="devices" style="margin-top:12px">${this.devices.map((d) => this.renderDevice(d))}</div>`}
      </div>
      ${this.renderCharts()} ${this.renderDatabases()} ${this.renderTemplateDialog()}`;
  }
}

define("woow-can-devices", WoowCanDevices);
