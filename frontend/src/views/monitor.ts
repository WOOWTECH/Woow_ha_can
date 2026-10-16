// Monitor tab: one row per ID and direction, live (like cansniffer / SavvyCAN / cabana); paused, the frames in
// time order, paged from the backend's buffer.
//
// The backend sends a batch every 250 ms with the rows that changed and the bits that changed since the
// previous batch; each batch is acknowledged, so a slow viewer gets fewer batches instead of a backlog.
// Highlights follow cabana: a byte that changes after a quiet spell (10 periods) or keeps moving the same
// way (more than 8 times) is cyan when rising and red when falling; a byte that keeps jumping back and
// forth (counter, checksum, noise) is grey-violet and fainter. Highlights fade over 2 s.

import { LitElement, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";

import {
  Api,
  Decoded,
  F_ERR,
  F_LOCAL,
  F_OWN,
  IdFilter,
  InterfaceInfo,
  MonitorBatch,
  MonitorRow,
  OfflineInfo,
  TX_KEY,
  TraceFrame,
  define,
  errorText,
  frameText,
  idHex,
  isExtended,
  randomToken,
  storageGet,
  storageSet,
} from "../api";
import { Translate, ago, clock, duration } from "../i18n";
import { bytesCss, shared } from "../styles";
import { formatValue } from "./devices";

const FADE_MS = 2000;
const NOTCH_WINDOW_MS = 2000;
const COLORS = { rise: "#00bbff", fall: "#ff3b30", churn: "#6656a9" } as const;
type Kind = "" | keyof typeof COLORS;

interface ByteState {
  t: number; // performance.now() of the last highlighted change
  dir: number;
  same: number;
  kind: Kind;
  bitT: number[]; // when each bit last changed
  notch: number; // bits that no longer highlight
}

interface RowState {
  key: number;
  raw: number;
  flags: number;
  hex: string;
  bytes: number[];
  count: number;
  period: number; // s
  pmin: number;
  pmax: number;
  last: number; // server time
  changed: number;
  changedPrev: number;
  born: number; // performance.now() when the row appeared (0 = in the first snapshot)
  b: ByteState[];
}

const newByte = (): ByteState => ({ t: -1e9, dir: 0, same: 0, kind: "", bitT: new Array(8).fill(-1e9), notch: 0 });

function hexBytes(hex: string): number[] {
  const out: number[] = [];
  for (let i = 0; i + 1 < hex.length; i += 2) out.push(parseInt(hex.slice(i, i + 2), 16));
  return out;
}

const value = (e: Event) => (e.target as HTMLInputElement).value;

export class WoowCanMonitor extends LitElement {
  @property({ attribute: false }) interfaces: InterfaceInfo[] = [];
  @property({ attribute: false }) offline: OfflineInfo[] = [];
  @property({ attribute: false }) source = "";
  @property({ attribute: false }) t!: Translate;
  @property({ attribute: false }) api!: Api;

  @state() private paused = false;
  @state() private bin = false;
  @state() private filterText = "";
  @state() private changingOnly = false;
  @state() private hideInactive = false;
  @state() private expanded = -1;
  @state() private message = "";
  @state() private trace: TraceFrame[] = [];
  @state() private traceNext: number | null = null;
  @state() private traceBusy = false;
  @state() private traceDir = "";
  @state() private frames = 0;
  @state() private overflow = 0;
  @state() private tick = 0;
  @state() private narrow = false;
  @state() private decoded: Decoded[] | null = null;

  private rows = new Map<number, RowState>();
  private names = new Map<number, string>();
  private decodedAt = 0;
  private decodedKey = -1;
  private order: number[] = [];
  private orderDirty = true;
  private pins = new Set<number>();
  private unsub?: () => Promise<void>;
  private token = "";
  private subscribed = "";
  private serverOffset = 0; // server clock minus this browser's, s
  private traceEnd: number | null = null;
  private timer?: number;
  private retry?: number;
  private readonly resize = new ResizeObserver((entries) => {
    const width = entries[0]?.contentRect.width ?? 1000;
    if ((width < 640) !== this.narrow) this.narrow = width < 640;
  });
  private readonly onVisibility = () => {
    if (document.hidden) void this.stop();
    else if (!this.paused) void this.start();
  };

  static styles = [
    shared,
    bytesCss,
    css`
      .toolbar {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }
      .toolbar input[type="search"] {
        flex: 1 1 14em;
      }
      label.toggle {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.92em;
        white-space: nowrap;
      }
      .wrap {
        overflow-x: auto;
      }
      table {
        border-collapse: collapse;
        width: 100%;
        font-size: 0.92em;
      }
      th,
      td {
        text-align: left;
        padding: 4px 8px;
        border-bottom: 1px solid var(--divider-color, #eee);
        white-space: nowrap;
        vertical-align: middle;
      }
      th {
        color: var(--secondary-text-color);
        font-weight: 500;
        font-size: 0.9em;
      }
      td.num {
        text-align: right;
        font-variant-numeric: tabular-nums;
      }
      td.id {
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        font-weight: 600;
        cursor: pointer;
      }
      td.id.stale {
        color: var(--error-color, #db4437);
      }
      tr.inactive td {
        opacity: 0.45;
      }
      tr.new td {
        background: rgba(3, 169, 244, 0.08);
      }
      tr.detail td {
        white-space: normal;
        background: var(--secondary-background-color, #f5f5f5);
      }
      .pin {
        border: none;
        background: none;
        padding: 0 2px;
        color: var(--secondary-text-color);
      }
      .pin.on {
        color: var(--warning-color, #ff9800);
      }
      .tag {
        font-size: 0.75em;
        padding: 0 6px;
        border-radius: 8px;
        background: rgba(3, 169, 244, 0.14);
        color: var(--info-color, #039be5);
        margin-left: 4px;
        font-weight: 400;
      }
      td.id .name {
        font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
        font-weight: 400;
        font-size: 0.8em;
        color: var(--secondary-text-color);
      }
      .decoded {
        display: flex;
        flex-wrap: wrap;
        gap: 4px 14px;
        margin: 4px 0;
      }
      .decoded .sig {
        font-variant-numeric: tabular-nums;
      }
      .tag.muted-tag {
        background: var(--secondary-background-color, #eee);
        color: var(--secondary-text-color);
      }
      .tag.err {
        background: rgba(219, 68, 55, 0.12);
        color: var(--error-color, #db4437);
      }
      .msg {
        margin: 6px 0;
      }
      .cards {
        display: grid;
        gap: 6px;
      }
      .mrow {
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 8px;
        padding: 6px 8px;
        display: grid;
        gap: 4px;
      }
      .mrow.inactive {
        opacity: 0.5;
      }
      .mrow.new {
        background: rgba(3, 169, 244, 0.08);
      }
      .mhead {
        display: flex;
        align-items: center;
        gap: 6px;
        cursor: pointer;
      }
      .mhead .id {
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        font-weight: 600;
      }
      .mhead .id.stale {
        color: var(--error-color, #db4437);
      }
      .wrapbytes {
        flex-wrap: wrap;
      }
      .mdetail {
        padding-top: 6px;
        border-top: 1px solid var(--divider-color, #eee);
        font-size: 0.92em;
      }
      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 6px;
      }
    `,
  ];

  connectedCallback(): void {
    super.connectedCallback();
    document.addEventListener("visibilitychange", this.onVisibility);
    this.resize.observe(this);
    this.timer = window.setInterval(() => {
      if (!this.paused && !document.hidden) {
        this.tick++;
        if (this.expanded >= 0 && performance.now() - this.decodedAt > 1000) void this.refreshDecode();
      }
    }, 200);
    this.loadPins();
    if (this.source && !this.paused) void this.start();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    document.removeEventListener("visibilitychange", this.onVisibility);
    this.resize.disconnect();
    window.clearInterval(this.timer);
    window.clearTimeout(this.retry);
    void this.stop();
  }

  protected updated(changed: Map<string, unknown>): void {
    if (changed.has("source") && this.source !== this.subscribed) {
      this.paused = false;
      this.trace = [];
      this.loadPins();
      void this.start();
    }
  }

  private get live(): boolean {
    return this.interfaces.some((i) => i.id === this.source);
  }

  private get iface(): InterfaceInfo | undefined {
    return this.interfaces.find((i) => i.id === this.source);
  }

  private loadPins(): void {
    this.pins = new Set(storageGet<number[]>(`woow_can.pins.${this.source}`, []));
    this.orderDirty = true;
  }

  private savePins(): void {
    storageSet(`woow_can.pins.${this.source}`, [...this.pins]);
  }

  // ---- live subscription -------------------------------------------------------------
  private async start(): Promise<void> {
    await this.stop();
    if (!this.source || document.hidden) return;
    const source = this.source;
    this.rows.clear();
    this.orderDirty = true;
    this.token = randomToken();
    const token = this.token;
    this.subscribed = source;
    try {
      const unsub = await this.api.subscribeMonitor(source, token, (batch) => this.onBatch(batch, token));
      if (this.token !== token) {
        void unsub();
        return;
      }
      this.unsub = unsub;
    } catch (err) {
      this.message = errorText(err);
    }
  }

  private async stop(): Promise<void> {
    const unsub = this.unsub;
    this.unsub = undefined;
    this.token = "";
    if (unsub) {
      try {
        await unsub();
      } catch {
        /* the connection may already be gone */
      }
    }
  }

  private onBatch(batch: MonitorBatch, token: string): void {
    if (token !== this.token) return;
    if (batch.gone) {
      this.message = batch.error ?? this.t("gone");
      window.clearTimeout(this.retry);
      this.retry = window.setTimeout(() => !this.paused && void this.start(), 1500);
      return;
    }
    const now = performance.now();
    this.serverOffset = batch.t - Date.now() / 1000;
    if (batch.full || batch.clear) {
      this.rows.clear();
      this.orderDirty = true;
    }
    if (batch.full) this.names.clear();
    for (const [key, name] of Object.entries(batch.names ?? {})) this.names.set(Number(key) % TX_KEY, name);
    for (const row of batch.rows ?? []) this.applyRow(row, now, !!batch.full);
    if (batch.frames !== undefined) this.frames = batch.frames;
    if (batch.overflow !== undefined) this.overflow = batch.overflow;
    if (batch.trace_end !== undefined) this.traceEnd = batch.trace_end;
    if (this.message === this.t("gone")) this.message = "";
    if (batch.seq > 0) void this.api.ack(token, batch.seq).catch(() => undefined);
  }

  private applyRow(r: MonitorRow, now: number, snapshot: boolean): void {
    const [key, raw, flags, hex, count, periodUs, pminUs, pmaxUs, maskHex, last, changed, changedPrev] = r;
    const bytes = hexBytes(hex);
    let row = this.rows.get(key);
    if (!row) {
      row = {
        key, raw, flags, hex, bytes, count, period: 0, pmin: 0, pmax: 0, last, changed, changedPrev,
        born: snapshot ? 0 : now,
        b: bytes.map(() => newByte()),
      };
      this.rows.set(key, row);
      this.orderDirty = true;
    } else if (maskHex) {
      const period = periodUs ? periodUs / 1e6 : 1;
      for (let i = 0; i < bytes.length; i++) {
        const mask = parseInt(maskHex.slice(2 * i, 2 * i + 2) || "0", 16);
        if (!mask) continue;
        const b = (row.b[i] ??= newByte());
        for (let k = 0; k < 8; k++) if ((mask >> k) & 1) b.bitT[k] = now;
        if (!(mask & ~b.notch & 0xff)) continue;
        const old = row.bytes[i] ?? 0;
        const dir = bytes[i] > old ? 1 : bytes[i] < old ? -1 : 0;
        const quiet = now - b.t > 10 * period * 1000;
        b.same = dir !== 0 && dir === b.dir ? b.same + 1 : 1;
        b.dir = dir;
        b.kind = dir === 0 ? "churn" : quiet || b.same > 8 ? (dir > 0 ? "rise" : "fall") : "churn";
        b.t = now;
      }
      if (row.b.length !== bytes.length) row.b = bytes.map((_, i) => row!.b[i] ?? newByte());
    }
    Object.assign(row, {
      raw, flags, hex, bytes, count, last, changed, changedPrev,
      period: periodUs / 1e6, pmin: pminUs / 1e6, pmax: pmaxUs / 1e6,
    });
  }

  private serverNow(): number {
    return Date.now() / 1000 + this.serverOffset;
  }

  // ---- toolbar ---------------------------------------------------------------------------
  private notch(): void {
    const now = performance.now();
    let n = 0;
    for (const row of this.rows.values()) {
      for (const b of row.b) {
        b.bitT.forEach((t, k) => {
          if (now - t < NOTCH_WINDOW_MS && !((b.notch >> k) & 1)) {
            b.notch |= 1 << k;
            n++;
          }
        });
      }
    }
    this.message = n ? this.t("notch_added", { n }) : this.t("notch_none");
  }

  private clearNotch(): void {
    for (const row of this.rows.values()) for (const b of row.b) b.notch = 0;
    this.message = "";
  }

  private async clear(): Promise<void> {
    try {
      await this.api.clearMonitor(this.source);
    } catch (err) {
      this.message = errorText(err);
    }
  }

  private async pause(filter?: string): Promise<void> {
    if (filter !== undefined) this.filterText = filter;
    this.paused = true;
    await this.stop();
    this.trace = [];
    this.traceNext = this.traceEnd;
    await this.loadTrace(true);
  }

  private resume(): void {
    this.paused = false;
    this.trace = [];
    void this.start();
  }

  private async loadTrace(first = false): Promise<void> {
    if (this.traceBusy) return;
    this.traceBusy = true;
    try {
      const filter = new IdFilter(this.filterText);
      const page = await this.api.trace(this.source, {
        before: first ? this.traceEnd : this.traceNext,
        limit: 200,
        ids: filter.error || filter.all ? "" : this.filterText,
        direction: this.traceDir || null,
      });
      this.trace = first ? page.frames : [...this.trace, ...page.frames];
      this.traceNext = page.next;
    } catch (err) {
      this.message = errorText(err);
    } finally {
      this.traceBusy = false;
    }
  }

  private async refreshDecode(): Promise<void> {
    const row = this.rows.get(this.expanded);
    this.decodedAt = performance.now();
    if (!row || (row.flags & F_ERR)) {
      this.decoded = null;
      return;
    }
    if (this.decodedKey !== row.key) this.decoded = null;
    this.decodedKey = row.key;
    try {
      const res = await this.api.decode(this.source, row.raw, row.hex);
      if (this.expanded === row.key) this.decoded = res.decoded;
    } catch {
      this.decoded = null;
    }
  }

  private toggleRow(key: number): void {
    this.expanded = this.expanded === key ? -1 : key;
    this.decoded = null;
    this.decodedAt = 0;
    if (this.expanded >= 0) void this.refreshDecode();
  }

  // ---- row actions -------------------------------------------------------------------------
  private togglePin(key: number): void {
    if (this.pins.has(key)) this.pins.delete(key);
    else this.pins.add(key);
    this.pins = new Set(this.pins);
    this.savePins();
    this.orderDirty = true;
    this.requestUpdate();
  }

  private sendAgain(row: RowState): void {
    this.dispatchEvent(new CustomEvent("send-frame", {
      detail: { frame: frameText(row.raw, row.flags, row.hex), entryId: this.live ? this.source : "" },
    }));
  }

  private async fireEvents(row: RowState): Promise<void> {
    const iface = this.iface;
    if (!iface) return;
    const id = idHex(row.raw);
    const current = iface.settings.event_filter.trim();
    try {
      await this.api.setEvents(iface.id, current ? `${current}, ${id}` : id);
      this.message = this.t("events_added", { id });
    } catch (err) {
      this.message = errorText(err);
    }
  }

  private notchRow(row: RowState): void {
    for (const b of row.b) b.notch = 0xff;
    this.requestUpdate();
  }

  // ---- rendering ---------------------------------------------------------------------------
  private sorted(): RowState[] {
    if (this.orderDirty) {
      this.order = [...this.rows.values()]
        .sort((a, b) => {
          const pa = this.pins.has(a.key) ? 0 : 1;
          const pb = this.pins.has(b.key) ? 0 : 1;
          if (pa !== pb) return pa - pb;
          const ea = isExtended(a.raw) ? 1 : 0;
          const eb = isExtended(b.raw) ? 1 : 0;
          if (ea !== eb) return ea - eb;
          const ia = a.raw % 0x20000000;
          const ib = b.raw % 0x20000000;
          return ia !== ib ? ia - ib : a.key - b.key;
        })
        .map((r) => r.key);
      this.orderDirty = false;
    }
    return this.order.map((k) => this.rows.get(k)).filter((r): r is RowState => !!r);
  }

  private byteCells(row: RowState, now: number) {
    return row.bytes.map((v, i) => {
      const b = row.b[i];
      let style = "";
      if (b?.kind) {
        const alpha = Math.max(0, 1 - (now - b.t) / FADE_MS) * (b.kind === "churn" ? 0.4 : 0.65);
        if (alpha > 0.01) style = `background: color-mix(in srgb, ${COLORS[b.kind]} ${Math.round(alpha * 100)}%, transparent)`;
      }
      const text = this.bin ? v.toString(2).padStart(8, "0") : v.toString(16).toUpperCase().padStart(2, "0");
      return html`<span class="byte ${this.bin ? "bin" : ""} ${b?.notch ? "notched" : ""}" style=${style}>${text}</span>`;
    });
  }

  private detailRow(row: RowState, serverNow: number) {
    return html`<tr class="detail"><td colspan="9">${this.detail(row, serverNow)}</td></tr>`;
  }

  private detail(row: RowState, serverNow: number) {
    const t = this.t;
    const pinned = this.pins.has(row.key);
    const iface = this.iface;
    const filter = iface ? new IdFilter(iface.settings.event_filter) : null;
    const firesEvents = !!(iface && iface.settings.event_filter.trim() && filter && !filter.error && filter.matches(row.raw));
    const decoded = this.decodedKey === row.key ? this.decoded : null;
    return html`
        <div class="mono">${frameText(row.raw, row.flags, row.hex)}</div>
        ${decoded === null
          ? nothing
          : decoded.length === 0
            ? html`<div class="muted">${t("no_definition")}</div>`
            : decoded.map((d) => html`<div class="decoded">
                <span class="muted">${d.source} · ${d.message}</span>
                ${d.signals.map((sg) => html`<span class="sig">${sg.name} <b>${formatValue(sg.value, sg.unit)}</b></span>`)}
              </div>`)}
        <div class="muted">
          ${row.period
            ? html`${t("detail_period", {
                avg: (row.period * 1000).toFixed(row.period < 0.1 ? 2 : 1),
                min: (row.pmin * 1000).toFixed(1),
                max: (row.pmax * 1000).toFixed(1),
              })} · ${t("detail_rate", { hz: (1 / row.period).toFixed(2) })}`
            : nothing}
        </div>
        ${row.changedPrev
          ? html`<div class="muted">
              ${t("detail_changed", { ago: ago(row.changed, t, serverNow), gap: duration(row.changed - row.changedPrev) })}
            </div>`
          : nothing}
        <div class="actions">
          <button @click=${() => this.togglePin(row.key)}>${pinned ? t("row_unpin") : t("row_pin")}</button>
          <button @click=${() => this.sendAgain(row)}>${t("row_send")}</button>
          ${iface
            ? html`<button ?disabled=${firesEvents} @click=${() => this.fireEvents(row)}>
                ${firesEvents ? t("row_events_on") : t("row_events")}
              </button>`
            : nothing}
          <button @click=${() => this.pause(idHex(row.raw))}>${t("row_trace")}</button>
          <button @click=${() => this.notchRow(row)}>${t("row_notch")}</button>
        </div>`;
  }

  private renderLive() {
    const t = this.t;
    const now = performance.now();
    const serverNow = this.serverNow();
    const filter = new IdFilter(this.filterText);
    const rows = this.sorted().filter((row) => {
      if (!filter.error && !filter.matches(row.raw)) return false;
      if (this.changingOnly && !(row.changedPrev > 0 && serverNow - row.changed < 5)) return false;
      if (this.hideInactive && serverNow - row.last > 5) return false;
      return true;
    });
    if (!this.rows.size) return html`<div class="empty">${t("monitor_empty")}</div>`;
    if (this.narrow) return this.renderCards(rows, now, serverNow);
    return html`<div class="wrap">
      <table>
        <thead>
          <tr>
            <th></th>
            <th>${t("col_id")}</th>
            <th>${t("col_len")}</th>
            <th>${t("col_data")}</th>
            <th class="num">${t("col_count")}</th>
            <th class="num">${t("col_hz")}</th>
            <th class="num">${t("col_period")}</th>
            <th class="num">${t("col_dchg")}</th>
            <th class="num">${t("col_age")}</th>
          </tr>
        </thead>
        <tbody>
          ${repeat(
            rows,
            (row) => row.key,
            (row) => {
              const age = serverNow - row.last;
              // silent for 5 periods (plus the 250 ms between batches), or 1.5 s when the period is unknown
              const inactive = age > (row.period ? 5 * row.period + 0.5 : 1.75);
              const tx = row.key >= TX_KEY;
              const local = !tx && !!(row.flags & F_LOCAL) && !this.iface?.virtual;
              return html`<tr class="${inactive ? "inactive" : ""} ${row.born && now - row.born < FADE_MS ? "new" : ""}">
                  <td><button class="pin ${this.pins.has(row.key) ? "on" : ""}" title=${t("row_pin")}
                    @click=${() => this.togglePin(row.key)}>${this.pins.has(row.key) ? "★" : "☆"}</button></td>
                  <td class="id ${age > 4 ? "stale" : ""}" @click=${() => this.toggleRow(row.key)}>
                    ${idHex(row.raw)}${tx ? html`<span class="tag">${t("dir_tx")}</span>` : nothing}${local
                      ? html`<span class="tag muted-tag">${t("dir_local")}</span>`
                      : nothing}${this.names.has(row.key % TX_KEY)
                      ? html`<div class="name">${this.names.get(row.key % TX_KEY)}</div>`
                      : nothing}
                  </td>
                  <td class="num">${row.bytes.length}</td>
                  <td><div class="bytes">${this.byteCells(row, now)}</div></td>
                  <td class="num">${row.count.toLocaleString()}</td>
                  <td class="num">${row.period ? (1 / row.period).toFixed(1) : "–"}</td>
                  <td class="num">${row.period ? duration(row.period) : "–"}</td>
                  <td class="num">${row.changedPrev ? duration(row.changed - row.changedPrev) : "–"}</td>
                  <td class="num">${duration(Math.max(0, age))}</td>
                </tr>
                ${this.expanded === row.key ? this.detailRow(row, serverNow) : nothing}`;
            },
          )}
        </tbody>
      </table>
    </div>`;
  }

  /** Phones: one card per row, the bytes on their own line. */
  private renderCards(rows: RowState[], now: number, serverNow: number) {
    const t = this.t;
    return html`<div class="cards">
      ${repeat(
        rows,
        (row) => row.key,
        (row) => {
          const age = serverNow - row.last;
          const inactive = age > (row.period ? 5 * row.period + 0.5 : 1.75);
          const tx = row.key >= TX_KEY;
          return html`<div class="mrow ${inactive ? "inactive" : ""} ${row.born && now - row.born < FADE_MS ? "new" : ""}">
            <div class="mhead" @click=${() => this.toggleRow(row.key)}>
              <button class="pin ${this.pins.has(row.key) ? "on" : ""}" @click=${(e: Event) => {
                e.stopPropagation();
                this.togglePin(row.key);
              }}>${this.pins.has(row.key) ? "★" : "☆"}</button>
              <span class="id ${age > 4 ? "stale" : ""}">${idHex(row.raw)}</span>
              ${tx ? html`<span class="tag">${t("dir_tx")}</span>` : nothing}
              ${this.names.has(row.key % TX_KEY) ? html`<span class="muted">${this.names.get(row.key % TX_KEY)}</span>` : nothing}
              <span class="grow"></span>
              <span class="muted">${row.period ? `${(1 / row.period).toFixed(1)} Hz · ` : ""}${duration(Math.max(0, age))}</span>
            </div>
            <div class="bytes wrapbytes">${this.byteCells(row, now)}</div>
            ${this.expanded === row.key ? html`<div class="mdetail">${this.detail(row, serverNow)}</div>` : nothing}
          </div>`;
        },
      )}
    </div>`;
  }

  private renderTrace() {
    const t = this.t;
    const frames = this.trace;
    return html`<div class="row msg">
        <b class="grow">${t("paused_title")}</b>
        <select @change=${(e: Event) => {
          this.traceDir = value(e);
          void this.loadTrace(true);
        }}>
          <option value="" ?selected=${!this.traceDir}>${t("trace_all_dirs")}</option>
          <option value="rx" ?selected=${this.traceDir === "rx"}>${t("dir_rx")}</option>
          <option value="tx" ?selected=${this.traceDir === "tx"}>${t("dir_tx")}</option>
        </select>
      </div>
      ${frames.length === 0
        ? html`<div class="empty">${this.traceBusy ? t("loading") : t("trace_empty")}</div>`
        : html`<div class="wrap">
            <table>
              <thead>
                <tr>
                  <th>${t("trace_time")}</th>
                  ${this.narrow ? nothing : html`<th class="num">${t("trace_delta")}</th>`}
                  <th>${t("col_dir")}</th>
                  <th>${t("col_id")}</th>
                  ${this.narrow ? nothing : html`<th>${t("col_len")}</th>`}
                  <th>${t("col_data")}</th>
                </tr>
              </thead>
              <tbody>
                ${frames.map(([seq, time, raw, flags, hex], i) => {
                  const older = frames[i + 1];
                  const err = !!(flags & F_ERR);
                  const tx = !!(flags & F_OWN);
                  return html`<tr title=${`#${seq}`}>
                    <td class="num">${clock(time)}</td>
                    ${this.narrow ? nothing : html`<td class="num">${older ? duration(time - older[1]) : ""}</td>`}
                    <td>${tx ? t("dir_tx") : t("dir_rx")}</td>
                    <td class="id">${err ? html`<span class="tag err">ERR</span>` : idHex(raw)}</td>
                    ${this.narrow ? nothing : html`<td class="num">${hex.length / 2}</td>`}
                    <td><div class="bytes">
                      ${err
                        ? html`<span class="muted">${t("trace_error", { x: frameText(raw, flags, hex) })}</span>`
                        : hexBytes(hex).map((v) => html`<span class="byte ${this.bin ? "bin" : ""}">${
                            this.bin ? v.toString(2).padStart(8, "0") : v.toString(16).toUpperCase().padStart(2, "0")}</span>`)}
                    </div></td>
                  </tr>`;
                })}
              </tbody>
            </table>
          </div>`}
      <div class="row msg">
        ${this.traceNext !== null
          ? html`<button ?disabled=${this.traceBusy} @click=${() => this.loadTrace()}>${t("trace_older")}</button>`
          : frames.length
            ? html`<span class="muted">${t("trace_start")}</span>`
            : nothing}
      </div>`;
  }

  render() {
    const t = this.t;
    void this.tick; // re-render on the ticker so highlights fade and ages count up
    const offline = this.offline.find((o) => o.id === this.source);
    const filter = new IdFilter(this.filterText);
    return html`<div class="card">
      <div class="toolbar">
        <select title=${t("source")} @change=${(e: Event) =>
          this.dispatchEvent(new CustomEvent("source-changed", { detail: value(e) }))}>
          ${this.interfaces.map((i) => html`<option value=${i.id} ?selected=${i.id === this.source}>${i.name} · ${i.port}</option>`)}
          ${this.offline.map((o) => html`<option value=${o.id} ?selected=${o.id === this.source}>${t("file_source", { name: o.name })}</option>`)}
        </select>
        ${this.paused
          ? html`<button class="primary" @click=${() => this.resume()}>${t("resume")}</button>`
          : html`<button @click=${() => this.pause()}>${t("pause")}</button>`}
        ${this.live && !this.paused ? html`<button @click=${() => this.clear()}>${t("clear")}</button>` : nothing}
        ${this.paused
          ? nothing
          : html`<button @click=${() => this.notch()}>${t("notch")}</button>
              <button @click=${() => this.clearNotch()}>${t("notch_clear")}</button>
              <label class="toggle"><input type="checkbox" .checked=${this.changingOnly}
                @change=${(e: Event) => (this.changingOnly = (e.target as HTMLInputElement).checked)} />${t("changing_only")}</label>
              <label class="toggle"><input type="checkbox" .checked=${this.hideInactive}
                @change=${(e: Event) => (this.hideInactive = (e.target as HTMLInputElement).checked)} />${t("hide_inactive")}</label>`}
        <label class="toggle"><input type="checkbox" .checked=${this.bin}
          @change=${(e: Event) => (this.bin = (e.target as HTMLInputElement).checked)} />${t("view_bin")}</label>
        <input type="search" placeholder=${t("filter_ph")} .value=${this.filterText}
          @input=${(e: Event) => (this.filterText = value(e))}
          @change=${() => this.paused && this.loadTrace(true)} />
      </div>
      ${filter.error ? html`<div class="chip bad">${t("filter_bad", { x: filter.error })}</div>` : nothing}
      <div class="muted">
        ${t("frames_total", { ids: this.rows.size, n: this.frames.toLocaleString() })}
        ${this.overflow ? html` · ${t("overflow", { n: this.overflow })}` : nothing}
        ${offline ? html` · ${t("offline_note", { file: offline.file, n: offline.frames })}` : nothing}
      </div>
      ${this.message ? html`<div class="msg chip info" style="white-space:normal">${this.message}</div>` : nothing}
      ${this.paused ? this.renderTrace() : this.renderLive()}
      ${this.paused ? nothing : html`<p class="muted">${t("monitor_hint")}</p>`}
    </div>`;
  }
}

define("woow-can-monitor", WoowCanMonitor);
