// Analyze tab: reverse engineering on the source picked on the Monitor tab.
// - Guided capture: idle / action phases (repeatable), then the bits and bytes that follow the action.
// - Find a signal by its value: a scan over every ID's fields, narrowed step by step (like a memory scanner).
// - Bits of one ID: how often each bit changes (heat map); tap two bits to try a field, then add it to a device.

import { LitElement, css, html, nothing, svg } from "lit";
import { property, state } from "lit/decorators.js";

import {
  Api,
  BitActivity,
  Candidate,
  DeviceView,
  FindMode,
  FindResult,
  GuidedResult,
  GuidedRow,
  InterfaceInfo,
  OfflineInfo,
  Series,
  SignalSpec,
  TX_KEY,
  define,
  errorText,
  fieldBetween,
  fieldBits,
  idHex,
  parseId,
} from "../api";
import { Translate, isKey } from "../i18n";
import { shared } from "../styles";
import { formatValue } from "./devices";

const num = (e: Event) => (e.target as HTMLInputElement).value;
const keyText = (key: number) => idHex(key % TX_KEY) + (key >= TX_KEY ? " (tx)" : "");

interface AddForm {
  key: number;
  spec: SignalSpec;
  name: string;
  unit: string;
  entryId: string;
  deviceId: string; // "" = new device
  deviceName: string;
}

export class WoowCanAnalyze extends LitElement {
  @property({ attribute: false }) interfaces: InterfaceInfo[] = [];
  @property({ attribute: false }) offline: OfflineInfo[] = [];
  @property({ attribute: false }) devices: DeviceView[] = [];
  @property({ attribute: false }) source = "";
  @property({ attribute: false }) focusId: { key: number; n: number } | null = null;
  @property({ attribute: false }) t!: Translate;
  @property({ attribute: false }) api!: Api;

  @state() private message: { ok: boolean; text: string } | null = null;
  @state() private busy = false;
  // guided capture
  @state() private guided: GuidedResult | null = null;
  @state() private tick = 0;
  // value search
  @state() private find: FindResult | null = null;
  @state() private findValue = "";
  @state() private findTol = "";
  // bits of one ID
  @state() private idText = "";
  @state() private tx = false;
  @state() private bits: BitActivity | null = null;
  @state() private spec: SignalSpec = { start: 0, length: 8, byte_order: "little", signed: false, factor: 1, offset: 0 };
  @state() private ends: [number, number] | null = null;
  @state() private anchor: number | null = null;
  @state() private trial: Series | null = null;
  // adding a field to a device
  @state() private add: AddForm | null = null;

  private timer?: number;
  private lastFocus = 0;
  private trialTimer?: number;

  static styles = [
    shared,
    css`
      .phase {
        font-size: 1.3em;
        margin: 10px 0 4px;
      }
      .steps {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin: 8px 0;
      }
      .hint-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
        margin: 4px 0;
      }
      .result {
        border-top: 1px solid var(--divider-color, #eee);
        padding: 8px 0;
      }
      .wrap {
        overflow-x: auto;
      }
      .cand {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 4px 14px;
        padding: 6px 0;
        border-bottom: 1px solid var(--divider-color, #eee);
      }
      .cand .val {
        min-width: 60px;
      }
      .grid {
        display: inline-grid;
        grid-template-columns: auto repeat(8, minmax(22px, 30px)) auto;
        gap: 2px;
        align-items: center;
        margin: 8px 0;
      }
      .grid .lbl {
        font-size: 0.75em;
        color: var(--secondary-text-color);
        padding-right: 4px;
        white-space: nowrap;
      }
      .cell {
        height: 28px;
        border: 1px solid var(--divider-color, #ddd);
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75em;
        cursor: pointer;
        user-select: none;
        font-variant-numeric: tabular-nums;
      }
      .cell.sel {
        outline: 2px solid var(--primary-color);
        outline-offset: -2px;
        font-weight: 600;
      }
      .cell.anchor {
        outline: 2px dashed var(--primary-color);
      }
      .form {
        display: flex;
        flex-wrap: wrap;
        gap: 8px 12px;
        align-items: end;
        margin: 8px 0;
      }
      .form label {
        display: flex;
        flex-direction: column;
        font-size: 0.85em;
        color: var(--secondary-text-color);
        gap: 2px;
      }
      .form input[type="number"] {
        width: 90px;
      }
      svg.line {
        width: 100%;
        height: 70px;
        display: block;
      }
      svg.line polyline {
        fill: none;
        stroke: var(--primary-color);
        stroke-width: 1.5;
        vector-effect: non-scaling-stroke;
      }
      .addbox {
        border: 1px solid var(--primary-color);
        border-radius: 8px;
        padding: 10px 12px;
        margin: 10px 0;
      }
    `,
  ];

  // ---- lifecycle ---------------------------------------------------------------------------
  connectedCallback(): void {
    super.connectedCallback();
    this.timer = window.setInterval(() => {
      if (this.guided?.running) this.tick++;
    }, 250);
    void this.refresh();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    window.clearInterval(this.timer);
    window.clearTimeout(this.trialTimer);
  }

  protected willUpdate(changed: Map<string, unknown>): void {
    if (changed.has("source") && changed.get("source") !== undefined) {
      this.guided = null;
      this.find = null;
      this.bits = null;
      this.trial = null;
      void this.refresh();
    }
    if (changed.has("focusId") && this.focusId && this.focusId.n !== this.lastFocus) {
      this.lastFocus = this.focusId.n;
      this.idText = idHex(this.focusId.key % TX_KEY);
      this.tx = this.focusId.key >= TX_KEY;
      void this.loadBits();
    }
  }

  private get live(): boolean {
    return this.interfaces.some((i) => i.id === this.source);
  }

  private get sourceName(): string {
    const iface = this.interfaces.find((i) => i.id === this.source);
    if (iface) return `${iface.name} · ${iface.port}`;
    return this.offline.find((o) => o.id === this.source)?.name ?? "?";
  }

  private async refresh(): Promise<void> {
    if (!this.source) return;
    try {
      this.find = await this.api.analyzeFind(this.source, "status");
      if (this.find.steps.length === 0) this.find = null;
      if (this.live) {
        const g = await this.api.analyzeGuided(this.source, "status");
        this.guided = g.phases.length ? g : null;
      }
    } catch {
      /* the tools show their own errors when used */
    }
  }

  private async run(task: () => Promise<unknown>): Promise<void> {
    this.busy = true;
    this.message = null;
    try {
      await task();
    } catch (err) {
      this.message = { ok: false, text: this.t("error", { msg: errorText(err) }) };
    } finally {
      this.busy = false;
    }
  }

  // ---- guided capture ----------------------------------------------------------------------
  private guidedStep(action: "start" | "next" | "finish" | "cancel"): Promise<void> {
    return this.run(async () => {
      const count = this.guided?.phases.length ?? 0;
      const label = action === "start" ? this.t("g_label_idle")
        : action === "next" ? this.t(count % 2 ? "g_label_action" : "g_label_idle") : undefined; // phase `count` is next
      const res = await this.api.analyzeGuided(this.source, action, label);
      this.guided = action === "cancel" ? null : res;
    });
  }

  private renderGuided() {
    const t = this.t;
    const g = this.guided;
    const running = !!g?.running;
    const phases = g?.phases ?? [];
    const current = running ? phases[phases.length - 1] : null;
    void this.tick;
    const elapsed = current ? Math.max(0, Date.now() / 1000 - current.start) : 0;
    const acting = phases.length % 2 === 0; // phase 1, 3 ... (0-based odd) are actions
    return html`<div class="card">
      <h2>${t("g_title")}</h2>
      <div class="muted">${t("g_hint")}</div>
      ${!this.live
        ? html`<div class="chip warn" style="margin-top:8px">${t("g_live_only")}</div>`
        : running
          ? html`<div class="phase">${t("g_phase", { n: phases.length, label: current!.label, s: elapsed.toFixed(1) })}</div>
              <div>${acting ? t("g_do_action") : t("g_do_idle")}</div>
              <div class="steps">
                <button class="primary" ?disabled=${this.busy || phases.length >= 9} @click=${() => this.guidedStep("next")}>
                  ${acting ? t("g_next_idle") : t("g_next_action")}</button>
                <button ?disabled=${this.busy || phases.length < 2} @click=${() => this.guidedStep("finish")}>${t("g_finish")}</button>
                <button class="link" ?disabled=${this.busy} @click=${() => this.guidedStep("cancel")}>${t("g_cancel")}</button>
              </div>`
          : html`<div class="steps">
              <button class="primary" ?disabled=${this.busy} @click=${() => this.guidedStep("start")}>${t("g_start")}</button>
            </div>`}
      ${g && !running && g.results ? this.renderGuidedResults(g) : nothing}
    </div>`;
  }

  private renderGuidedResults(g: GuidedResult) {
    const t = this.t;
    const rows = g.results ?? [];
    return html`<h2 style="margin-top:12px">${t("g_results")}</h2>
      <div class="muted">${g.phases.map((p) => `${p.label} ${p.seconds} s`).join(" → ")}
        ${g.frames ? html` · ${t("g_frames", { n: g.frames.join(" / ") })}` : nothing}</div>
      ${g.warning ? html`<div class="chip warn" style="white-space:normal">${g.warning}</div>` : nothing}
      ${rows.length === 0 ? html`<div class="empty">${t("g_none")}</div>` : rows.map((r) => this.renderGuidedRow(r))}`;
  }

  private renderGuidedRow(r: GuidedRow) {
    const t = this.t;
    const ranges = (pair: [number, number]) => (pair[0] === pair[1] ? `${pair[0]}` : `${pair[0]}–${pair[1]}`);
    return html`<div class="result">
      <div class="row"><b class="mono">${r.id}</b>
        <button class="link" @click=${() => this.openBits(r.key)}>${t("f_open_bits")}</button></div>
      ${r.only_in ? html`<div class="hint-row"><span class="chip info">${t("g_only")}</span></div>` : nothing}
      ${(r.flipped ?? []).map((f) => html`<div class="hint-row">
        <span class="chip ok">${t("g_flip", { byte: f.byte, bit: f.bit, a: f.idle, b: f.action })}</span>
        ${f.confirmed ? html`<span class="muted">✓ ${t("g_confirmed")}</span>` : nothing}
        <button class="link" @click=${() => this.openAdd(r.key, { start: f.start, length: 1, byte_order: "little", signed: false, factor: 1, offset: 0 })}>
          ${t("g_make_switch")}</button>
      </div>`)}
      ${(r.shifted_bytes ?? []).map((b) => html`<div class="hint-row">
        <span class="chip info">${t("g_shift", { byte: b.byte, a: ranges(b.idle), b: ranges(b.action) })}</span>
        ${b.confirmed ? html`<span class="muted">✓ ${t("g_confirmed")}</span>` : nothing}
        <button class="link" @click=${() => this.openBits(r.key, { start: b.byte * 8, length: 8, byte_order: "little", signed: false, factor: 1, offset: 0 })}>
          ${t("g_try_byte")}</button>
      </div>`)}
      ${r.moving?.length ? html`<div class="muted">${t("g_moving", { bits: r.moving.map((m) => m.start).join(", ") })}</div>` : nothing}
      ${r.counter_bits?.length ? html`<div class="muted">${t("g_counter", { bits: this.spans(r.counter_bits) })}</div>` : nothing}
    </div>`;
  }

  private spans(bits: number[]): string {
    const out: string[] = [];
    let a = bits[0];
    let b = bits[0];
    for (const x of bits.slice(1).concat([NaN])) {
      if (x === b + 1) {
        b = x;
        continue;
      }
      out.push(a === b ? `${a}` : `${a}–${b}`);
      a = b = x;
    }
    return out.join(", ");
  }

  // ---- value search --------------------------------------------------------------------------
  private parse(text: string): number | null {
    const v = parseFloat(text.replace(",", "."));
    return Number.isFinite(v) ? v : null;
  }

  private findStep(action: "start" | "narrow" | "clear", mode?: FindMode, withValue = true): Promise<void> {
    return this.run(async () => {
      const value = withValue ? this.parse(this.findValue) : null;
      const tolerance = this.parse(this.findTol);
      const res = await this.api.analyzeFind(this.source, action, { mode, value, tolerance });
      this.find = action === "clear" ? null : res;
    });
  }

  private renderFind() {
    const t = this.t;
    const f = this.find;
    const value = this.parse(this.findValue);
    return html`<div class="card">
      <h2>${t("f_title")}</h2>
      <div class="muted">${t("f_hint")}</div>
      <div class="form">
        <label>${t("f_value")}<input type="number" step="any" .value=${this.findValue}
          @input=${(e: Event) => (this.findValue = num(e))} /></label>
        <label>${t("f_tolerance")}<input type="number" step="any" min="0" .value=${this.findTol} placeholder="auto"
          @input=${(e: Event) => (this.findTol = num(e))} /></label>
        ${f
          ? html`<button class="primary" ?disabled=${this.busy || value === null} @click=${() => this.findStep("narrow", "equals")}>
                ${t("f_equals")}</button>
              ${(["increased", "decreased", "changed", "unchanged"] as FindMode[]).map((m) => html`<button ?disabled=${this.busy}
                @click=${() => this.findStep("narrow", m, false)}>${t(`f_${m}`)}</button>`)}
              <button class="link" ?disabled=${this.busy} @click=${() => this.findStep("clear")}>${t("f_clear")}</button>`
          : html`<button class="primary" ?disabled=${this.busy || value === null} @click=${() => this.findStep("start")}>${t("f_start")}</button>
              <button ?disabled=${this.busy} @click=${() => this.findStep("start", undefined, false)}>${t("f_start_blank")}</button>`}
      </div>
      ${f ? this.renderCandidates(f) : nothing}
    </div>`;
  }

  private modeName(mode: string): string {
    const key = `f_${mode}`;
    return isKey(key) ? this.t(key) : mode;
  }

  private renderCandidates(f: FindResult) {
    const t = this.t;
    const step = (s: FindResult["steps"][number]) =>
      `${s.mode === "start" ? t("f_step_start") : s.mode === "equals" ? `= ${s.value}` : this.modeName(s.mode)} → ${s.left}`;
    const scale = (c: Candidate) => {
      const parts = [];
      if (c.factor !== 1) parts.push(`× ${c.factor}`);
      if (c.offset) parts.push(`${c.offset > 0 ? "+" : "−"} ${Math.abs(c.offset)}`);
      return parts.join(" ") || "—";
    };
    return html`<div><b>${t("f_left", { n: f.left.toLocaleString(), ids: f.ids })}</b>
        ${f.truncated ? html`<span class="muted">· ${t("f_truncated")}</span>` : nothing}</div>
      <div class="muted">${f.steps.map(step).join(" · ")}</div>
      ${f.candidates.map((c) => html`<div class="cand">
        <b class="mono">${c.id}</b>
        <span>${t("f_field", { start: c.start, length: c.length })} · ${c.byte_order === "big" ? "BE" : "LE"}${c.signed ? ` · ${t("f_signed")}` : ""}</span>
        <span class="muted">${scale(c)}</span>
        <b class="val">${formatValue(c.value)}</b>
        <span class="grow"></span>
        <button class="link" @click=${() => this.openBits(c.key, c)}>${t("f_open_bits")}</button>
        <button class="link" @click=${() => this.openAdd(c.key, c)}>${t("f_add")}</button>
      </div>`)}`;
  }

  // ---- bits of one ID --------------------------------------------------------------------------
  private currentKey(): number | null {
    try {
      const [id, extended] = parseId(this.idText);
      return (extended ? id + 0x80000000 : id) + (this.tx ? TX_KEY : 0);
    } catch {
      return null;
    }
  }

  private openBits(key: number, spec?: SignalSpec): void {
    this.idText = idHex(key % TX_KEY);
    this.tx = key >= TX_KEY;
    if (spec) {
      this.spec = { start: spec.start, length: spec.length, byte_order: spec.byte_order, signed: spec.signed,
        factor: spec.factor, offset: spec.offset };
      this.ends = null;
      this.anchor = null;
    }
    void this.loadBits().then(() => this.renderRoot.querySelector("#bits")?.scrollIntoView({ behavior: "smooth" }));
  }

  private async loadBits(): Promise<void> {
    const key = this.currentKey();
    if (key === null) return;
    await this.run(async () => {
      this.bits = await this.api.analyzeBits(this.source, key, 60);
    });
    this.scheduleTrial(0);
  }

  private scheduleTrial(delay = 300): void {
    window.clearTimeout(this.trialTimer);
    this.trialTimer = window.setTimeout(() => void this.tryField(), delay);
  }

  private async tryField(): Promise<void> {
    const key = this.currentKey();
    if (key === null || !this.bits?.frames) return;
    try {
      this.trial = await this.api.analyzeTry(this.source, key, this.spec, 60);
    } catch (err) {
      this.trial = null;
      this.message = { ok: false, text: this.t("error", { msg: errorText(err) }) };
    }
  }

  private setSpec(change: Partial<SignalSpec>): void {
    this.spec = { ...this.spec, ...change };
    if ("byte_order" in change && this.ends) {
      this.spec = { ...this.spec, ...fieldBetween(this.ends[0], this.ends[1], this.spec.byte_order) };
    }
    this.scheduleTrial();
  }

  private tapBit(i: number): void {
    if (this.anchor === null) {
      this.anchor = i;
      this.ends = [i, i];
      this.spec = { ...this.spec, start: i, length: 1 };
    } else {
      this.ends = [this.anchor, i];
      this.spec = { ...this.spec, ...fieldBetween(this.anchor, i, this.spec.byte_order) };
      this.anchor = null;
    }
    this.scheduleTrial();
  }

  private renderBits() {
    const t = this.t;
    const b = this.bits;
    const key = this.currentKey();
    return html`<div class="card" id="bits">
      <h2>${t("b_title")}</h2>
      <div class="muted">${t("b_hint")}</div>
      <div class="form">
        <label>${t("b_id")}<input class="mono" style="width:110px" .value=${this.idText}
          @input=${(e: Event) => (this.idText = num(e).trim())} @change=${() => this.loadBits()} /></label>
        <label class="toggle" style="flex-direction:row;align-items:center"><input type="checkbox" .checked=${this.tx}
          @change=${(e: Event) => { this.tx = (e.target as HTMLInputElement).checked; void this.loadBits(); }} />${t("b_tx")}</label>
        <button ?disabled=${this.busy || key === null} @click=${() => this.loadBits()}>${t("b_show")}</button>
        ${b ? html`<span class="muted">${t("b_frames", { n: b.frames })}</span>` : nothing}
      </div>
      ${b && b.frames === 0 ? html`<div class="empty">${t("b_no_frames")}</div>` : nothing}
      ${b && b.frames ? this.renderGrid(b) : nothing}
      ${b && b.frames ? this.renderField() : nothing}
    </div>`;
  }

  private renderGrid(b: BitActivity) {
    const t = this.t;
    const selected = new Set(fieldBits(this.spec.start, this.spec.length, this.spec.byte_order));
    const pairs = Math.max(1, b.frames - 1);
    const cells = [];
    for (let byte = 0; byte < b.length; byte++) {
      cells.push(html`<span class="lbl">${t("b_byte", { n: byte })}</span>`);
      for (let bit = 7; bit >= 0; bit--) {
        const i = byte * 8 + bit;
        const rate = b.changes[i] / pairs;
        const ones = b.ones[i] / b.frames;
        const alpha = b.changes[i] ? Math.round(15 + 70 * Math.min(1, rate)) : 0;
        const style = alpha ? `background: color-mix(in srgb, #00bbff ${alpha}%, transparent)` : "";
        const title = t("b_bit_title", { i, c: b.changes[i], p: Math.round(rate * 100), o: Math.round(ones * 100) });
        cells.push(html`<span class="cell ${selected.has(i) ? "sel" : ""} ${this.anchor === i ? "anchor" : ""}" style=${style}
          title=${title} @click=${() => this.tapBit(i)}>${ones >= 0.5 ? "1" : "0"}</span>`);
      }
      const r = b.bytes[byte];
      cells.push(html`<span class="lbl mono">${r.min === r.max ? r.min.toString(16).toUpperCase().padStart(2, "0")
        : `${r.min.toString(16).toUpperCase().padStart(2, "0")}–${r.max.toString(16).toUpperCase().padStart(2, "0")}`}</span>`);
    }
    return html`<div class="wrap"><div class="grid">
      <span></span>${[7, 6, 5, 4, 3, 2, 1, 0].map((n) => html`<span class="lbl" style="text-align:center">${n}</span>`)}<span></span>
      ${cells}
    </div></div>`;
  }

  private renderField() {
    const t = this.t;
    const s = this.spec;
    const tr = this.trial;
    const numbers = (tr?.samples ?? []).filter((p) => typeof p.value === "number") as { time: number; value: number }[];
    let chart: unknown = nothing;
    if (numbers.length > 1) {
      const vals = numbers.map((p) => p.value);
      const lo = Math.min(...vals);
      const hi = Math.max(...vals);
      const span = hi - lo || 1;
      const t0 = numbers[0].time;
      const tspan = numbers[numbers.length - 1].time - t0 || 1;
      const xy = numbers.map((p) => `${(((p.time - t0) / tspan) * 300).toFixed(1)},${(66 - ((p.value - lo) / span) * 62).toFixed(1)}`);
      chart = html`<svg class="line" viewBox="0 0 300 70" preserveAspectRatio="none">${svg`<polyline points=${xy.join(" ")}></polyline>`}</svg>`;
    }
    const key = this.currentKey();
    return html`<div class="form">
        <label>${t("b_start")}<input type="number" min="0" max="511" .value=${String(s.start)}
          @change=${(e: Event) => this.setSpec({ start: Math.max(0, parseInt(num(e)) || 0) })} /></label>
        <label>${t("b_length")}<input type="number" min="1" max="64" .value=${String(s.length)}
          @change=${(e: Event) => this.setSpec({ length: Math.min(64, Math.max(1, parseInt(num(e)) || 1)) })} /></label>
        <label>&nbsp;<select @change=${(e: Event) => this.setSpec({ byte_order: num(e) as "little" | "big" })}>
          <option value="little" ?selected=${s.byte_order === "little"}>${t("b_little")}</option>
          <option value="big" ?selected=${s.byte_order === "big"}>${t("b_big")}</option>
        </select></label>
        <label class="toggle" style="flex-direction:row;align-items:center"><input type="checkbox" .checked=${s.signed}
          @change=${(e: Event) => this.setSpec({ signed: (e.target as HTMLInputElement).checked })} />${t("b_signed")}</label>
        <label>${t("b_factor")}<input type="number" step="any" .value=${String(s.factor)}
          @change=${(e: Event) => this.setSpec({ factor: this.parse(num(e)) ?? 1 })} /></label>
        <label>${t("b_offset")}<input type="number" step="any" .value=${String(s.offset)}
          @change=${(e: Event) => this.setSpec({ offset: this.parse(num(e)) ?? 0 })} /></label>
        <button class="primary" ?disabled=${key === null} @click=${() => key !== null && this.openAdd(key, s)}>${t("f_add")}</button>
      </div>
      ${tr
        ? html`<div class="muted">${t("b_try", {
            n: tr.frames, d: tr.distinct_values, c: tr.changes, min: formatValue(tr.min), max: formatValue(tr.max),
            last: formatValue(tr.last),
          })}</div>${chart}`
        : nothing}`;
  }

  // ---- adding a field to a device -------------------------------------------------------------
  private openAdd(key: number, spec: SignalSpec): void {
    const entryId = this.live ? this.source : this.interfaces[0]?.id ?? "";
    const iface = this.interfaces.find((i) => i.id === entryId);
    this.add = {
      key,
      spec: { start: spec.start, length: spec.length, byte_order: spec.byte_order, signed: spec.signed,
        factor: spec.factor, offset: spec.offset },
      name: "",
      unit: spec.unit ?? "",
      entryId,
      deviceId: "",
      deviceName: `${iface?.name ?? ""} ${keyText(key % TX_KEY)}`.trim(),
    };
    void this.updateComplete.then(() => this.renderRoot.querySelector(".addbox")?.scrollIntoView({ behavior: "smooth" }));
  }

  private async submitAdd(): Promise<void> {
    const a = this.add;
    if (!a) return;
    if (!a.name.trim()) {
      this.message = { ok: false, text: this.t("a_name_needed") };
      return;
    }
    await this.run(async () => {
      const target = a.deviceId ? { device_id: a.deviceId } : { device_name: a.deviceName };
      const device = await this.api.addSignal(a.entryId, a.key, { ...a.spec, name: a.name.trim(), unit: a.unit.trim() }, target);
      this.add = null;
      this.message = { ok: true, text: this.t("a_added", { signal: a.name.trim(), device: device.name }) };
    });
  }

  private renderAdd() {
    const t = this.t;
    const a = this.add;
    if (!a) return nothing;
    const set = (change: Partial<AddForm>) => (this.add = { ...a, ...change });
    const devices = this.devices.filter((d) => d.interface === a.entryId);
    return html`<div class="card addbox">
      <h2>${t("a_title")}</h2>
      <div class="muted mono">${keyText(a.key)} · ${t("f_field", { start: a.spec.start, length: a.spec.length })}
        · ${a.spec.byte_order === "big" ? "BE" : "LE"}${a.spec.signed ? ` · ${t("f_signed")}` : ""}
        ${a.spec.factor !== 1 ? ` · × ${a.spec.factor}` : ""}${a.spec.offset ? ` · + ${a.spec.offset}` : ""}</div>
      <div class="form">
        <label>${t("a_name")}<input .value=${a.name} @input=${(e: Event) => set({ name: num(e) })} /></label>
        <label>${t("b_unit")}<input style="width:70px" .value=${a.unit} @input=${(e: Event) => set({ unit: num(e) })} /></label>
        <label>${t("a_interface")}<select @change=${(e: Event) => set({ entryId: num(e), deviceId: "" })}>
          ${this.interfaces.map((i) => html`<option value=${i.id} ?selected=${i.id === a.entryId}>${i.name}</option>`)}
        </select></label>
        <label>${t("a_device")}<select @change=${(e: Event) => set({ deviceId: num(e) })}>
          <option value="" ?selected=${!a.deviceId}>${t("a_new_device")}</option>
          ${devices.map((d) => html`<option value=${d.id} ?selected=${d.id === a.deviceId}>${d.name}</option>`)}
        </select></label>
        ${a.deviceId ? nothing : html`<label>${t("a_device_name")}<input .value=${a.deviceName}
          @input=${(e: Event) => set({ deviceName: num(e) })} /></label>`}
        <button class="primary" ?disabled=${this.busy || !a.entryId} @click=${() => this.submitAdd()}>${t("a_add")}</button>
        <button class="link" @click=${() => (this.add = null)}>${t("cancel")}</button>
      </div>
    </div>`;
  }

  render() {
    const t = this.t;
    return html`
      <div class="muted" style="margin:0 4px 8px">${t("an_source", { name: this.sourceName })}</div>
      ${this.message
        ? html`<div class="card"><div class="chip ${this.message.ok ? "ok" : "bad"}" style="white-space:normal">${this.message.text}</div></div>`
        : nothing}
      ${this.renderAdd()}
      ${this.renderGuided()}
      ${this.renderFind()}
      ${this.renderBits()}`;
  }
}

define("woow-can-analyze", WoowCanAnalyze);
