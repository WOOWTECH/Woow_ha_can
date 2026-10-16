// Types and websocket calls shared by the panel views (backend: websocket_api.py, views.py).

export interface HomeAssistant {
  connection: {
    subscribeMessage<T>(callback: (msg: T) => void, msg: Record<string, unknown>): Promise<() => Promise<void>>;
  };
  callWS<T>(msg: Record<string, unknown>): Promise<T>;
  fetchWithAuth(path: string, init?: Record<string, unknown>): Promise<Response>;
  hassUrl(path?: string): string;
  language: string;
  locale?: { language: string };
}

export interface Settings {
  bitrate: number;
  fd: boolean;
  dbitrate: number;
  listen_only: boolean;
  restart_ms: number;
  filters: string;
  event_filter: string;
  max_events_per_sec: number;
}

export interface Load {
  now: number | null;
  peak: number | null;
  avg: (number | null)[];
  rx_fps: number | null;
  tx_fps: number | null;
}

export interface ErrorInfo {
  total: number;
  counts: Record<string, number>;
  last: { t: number; codes: string[]; frame: string; tx_error_counter: number | null; rx_error_counter: number | null } | null;
}

export interface InterfaceInfo {
  id: string;
  name: string;
  port: string;
  driver: string;
  model: string;
  available: boolean;
  virtual: boolean;
  can_send: boolean;
  settings: Settings;
  status: Record<string, number | string | boolean | null>;
  load: Load;
  errors: ErrorInfo;
  monitor: { ids: number; frames: number; overflow: number; since: number };
  trace: { first: number; end: number; capacity: number };
  recording: { name: string; frames: number; bytes: number; full: boolean } | null;
  sent: number;
  started: number;
}

export interface OfflineInfo {
  id: string;
  name: string;
  file: string;
  port: string;
  offline: true;
  format?: string;
  frames: number;
  truncated: boolean;
  start: number | null;
  end: number | null;
  monitor: { ids: number; frames: number; overflow: number };
  trace: { first: number; end: number; capacity: number };
}

export interface Periodic {
  id: string;
  entry_id: string;
  name: string;
  frame: string;
  period_ms: number;
  count: number;
  running: boolean;
  sent: number;
  started: number | null;
  error: string | null;
  stopped_by: string | null;
}

export const FILE_FORMATS = ["log", "asc", "csv", "pcap"] as const;
export type FileFormat = (typeof FILE_FORMATS)[number];

export interface CaptureFile {
  name: string;
  size: number;
  modified: number;
  recording: boolean;
}

export interface Activity {
  t: number;
  channel: "service" | "panel" | "entity" | string;
  action: string;
  summary: string;
  ok: boolean;
  user: string | null;
  note: string;
  device_id: string | null;
  port_id: string | null;
  detail: Record<string, unknown>;
  msg?: string;
  args?: Record<string, string | number>;
}

/** [key, raw id, flags, data hex, count, period µs, min µs, max µs, changed bits hex, last, changed, changed before] */
export type MonitorRow = [number, number, number, string, number, number, number, number, string, number, number, number];

export interface MonitorBatch {
  seq: number;
  t: number;
  names?: Record<string, string>;
  rows?: MonitorRow[];
  overflow?: number;
  frames?: number;
  full?: boolean;
  clear?: boolean;
  gone?: boolean;
  error?: string;
  trace_end?: number;
  trace_first?: number;
}

/** [seq, time, raw id, flags, data hex] */
export type TraceFrame = [number, number, number, number, string];

export interface TracePage {
  frames: TraceFrame[];
  next: number | null;
  first: number;
  end: number;
  scanned: number;
}

export interface SignalStatus {
  name: string;
  value: unknown;
  unit: string;
  adopted: boolean;
  entity_id: string | null;
  platform: "sensor" | "binary_sensor";
  disabled: boolean;
}

export interface MessageStatus {
  name: string;
  id: string;
  seen_s_ago: number | null;
  fresh: boolean | null;
  signals: SignalStatus[];
}

export interface EntitySettings {
  name?: string | Record<string, string>;
  key?: string;
  platform?: string;
  enabled?: boolean;
  min_interval?: number;
  tolerance?: number;
  timeout?: number;
  [key: string]: unknown;
}

export interface SignalDef {
  name: string;
  start: number;
  length: number;
  byte_order: "little" | "big";
  signed: boolean;
  factor?: number;
  offset?: number;
  unit?: string;
  entity?: EntitySettings;
  comment?: string;
  [key: string]: unknown;
}

export interface MessageDef {
  name: string;
  can_id?: string;
  pgn?: number;
  signals: SignalDef[];
  [key: string]: unknown;
}

export interface DeviceView {
  id: string;
  name: string;
  interface: string;
  template: string | null;
  source: string;
  manufacturer: string;
  model: string;
  params: Record<string, unknown>;
  groups: string[];
  status: MessageStatus[];
  extra: Record<string, unknown>;
  definition?: { messages: MessageDef[]; [key: string]: unknown };
}

export interface TemplateSummary {
  id: string;
  name: string;
  category: string;
  description: string;
  notes: string;
  default_name: string;
  bitrate: number | null;
  transmits: boolean;
  source: string[];
  license: string;
  verified: string[];
  confidence: string;
  manufacturer: string;
  model: string;
  params: { key: string; default: unknown; description: string }[];
  groups: { id: string; name: string }[];
  messages: { name: string; id: string; group: string | null; entities: number }[];
  origin: string;
}

export interface DatabaseSummary {
  name: string;
  messages: number;
  signals: number;
  nodes: string[];
  skipped_statements: number;
  warnings: string[];
  warning_count: number;
  attached: string[];
  imported: number;
  message_names: string[];
}

export interface Decoded {
  source: string;
  message: string;
  signals: { name: string; value: unknown; unit: string; adopted: boolean; start: number; length: number; byte_order: string }[];
}

export type Values = Record<string, Record<string, unknown>>; // device id -> "Message.Signal" -> value

export interface Snapshot {
  interfaces: InterfaceInfo[];
  offline: OfflineInfo[];
  periodic: Periodic[];
  activity: Activity[];
  devices: DeviceView[];
  values: Values;
  templates: TemplateSummary[];
  databases: DatabaseSummary[];
  now: number;
}

export type FeedEvent =
  | { kind: "interfaces"; interfaces: InterfaceInfo[]; removed: string[] }
  | { kind: "periodic"; items: Periodic[]; removed: string[] }
  | { kind: "activity"; entries: Activity[] }
  | { kind: "captures"; changed: boolean }
  | { kind: "offline"; offline: OfflineInfo[] }
  | { kind: "devices"; devices: DeviceView[]; removed: string[] }
  | { kind: "values"; values: Values; t: number }
  | { kind: "databases"; databases: DatabaseSummary[] };

export interface FrameDict {
  frame: string;
  id: number;
  id_hex: string;
  data: string;
  length: number;
  extended: boolean;
  fd: boolean;
  brs: boolean;
  rtr: boolean;
}

export interface SendResult {
  sent: FrameDict;
  reply: FrameDict | null;
  timeout: boolean;
}

// Raw id and frame flags, as the kernel and the backend write them
// ---- reverse engineering ----
export interface BitActivity {
  id: string;
  key: number;
  frames: number;
  length: number;
  changes: number[]; // per bit (bit i = bit i % 8 of byte i / 8)
  ones: number[];
  bytes: { min: number; max: number; distinct: number }[];
  from: number | null;
  to: number | null;
}

export interface SignalSpec {
  name?: string;
  start: number;
  length: number;
  byte_order: "little" | "big";
  signed: boolean;
  factor: number;
  offset: number;
  unit?: string;
}

export interface Series {
  id: string;
  frames: number;
  distinct_values: number;
  changes: number;
  min: number | null;
  max: number | null;
  first: unknown;
  last: unknown;
  samples: { time: number; value: unknown }[];
}

export interface Candidate extends SignalSpec {
  id: string;
  key: number;
  value: number;
}

export interface FindResult {
  left: number;
  ids: number;
  truncated: boolean;
  steps: { mode: string; value: number | null; tolerance: number | null; left: number }[];
  candidates: Candidate[];
}

export interface GuidedPhase {
  label: string;
  start: number;
  end: number | null;
  seconds: number;
}

export interface GuidedRow {
  id: string;
  key: number;
  frames: number[];
  only_in?: string;
  confirmed?: boolean;
  flipped?: { byte: number; bit: number; start: number; idle: number; action: number; confirmed: boolean }[];
  moving?: { byte: number; bit: number; start: number }[];
  shifted_bytes?: { byte: number; idle: [number, number]; action: [number, number]; confirmed: boolean }[];
  counter_bits?: number[];
  score: number;
}

export interface GuidedResult {
  phases: GuidedPhase[];
  running: boolean;
  results?: GuidedRow[];
  frames?: number[];
  warning?: string;
}

export const FIND_MODES = ["equals", "increased", "decreased", "changed", "unchanged"] as const;
export type FindMode = (typeof FIND_MODES)[number];

/** The bits a field covers (bit i = bit i % 8 of byte i / 8), as the backend's signals count them. */
export function fieldBits(start: number, length: number, order: "little" | "big"): number[] {
  if (order === "little") return Array.from({ length }, (_, k) => start + k);
  const msb = Math.floor(start / 8) * 8 + (7 - (start % 8));
  return Array.from({ length }, (_, k) => {
    const lin = msb + k;
    return Math.floor(lin / 8) * 8 + (7 - (lin % 8));
  });
}

/** start / length of the field between two clicked bits, in the given byte order. */
export function fieldBetween(a: number, b: number, order: "little" | "big"): { start: number; length: number } {
  if (order === "little") return { start: Math.min(a, b), length: Math.abs(a - b) + 1 };
  const lin = (i: number) => Math.floor(i / 8) * 8 + (7 - (i % 8));
  const [first, last] = lin(a) <= lin(b) ? [a, b] : [b, a];
  return { start: first, length: lin(last) - lin(first) + 1 };
}

export const EFF = 0x80000000;
export const RTR = 0x40000000;
export const F_FD = 0x01;
export const F_BRS = 0x02;
export const F_OWN = 0x04;
export const F_LOCAL = 0x08;
export const F_ERR = 0x10;
export const TX_KEY = 2 ** 32;

// Flag bits sit above bit 29; raw ids (and monitor keys, which add 2^32) exceed 2^31, so test them
// with arithmetic: JavaScript's bit operators work on signed 32-bit numbers.
export function isExtended(raw: number): boolean {
  return Math.floor(raw / EFF) % 2 === 1;
}

export function isRemote(raw: number): boolean {
  return Math.floor(raw / RTR) % 2 === 1;
}

export function idHex(raw: number): string {
  const id = raw % 0x20000000;
  return isExtended(raw)
    ? id.toString(16).toUpperCase().padStart(8, "0")
    : (id % 0x800).toString(16).toUpperCase().padStart(3, "0");
}

/** candump notation of a frame from the trace or monitor. */
export function frameText(raw: number, flags: number, hex: string): string {
  if (flags & F_ERR) return `${(0x20000000 + (raw % 0x20000000)).toString(16).toUpperCase().padStart(8, "0")}#${hex}`;
  const id = idHex(raw);
  if (isRemote(raw) && !(flags & F_FD)) return `${id}#R`;
  if (flags & F_FD) return `${id}##${flags & F_BRS ? 1 : 0}${hex}`;
  return `${id}#${hex}`;
}

/** The same ID lists the backend accepts: 123, 18FF50E5, 7E0/7F0, 100-1FF, * (empty = everything here). */
export class IdFilter {
  readonly all: boolean;
  private readonly exact = new Set<string>();
  private readonly masks: [number, number, boolean][] = [];
  private readonly ranges: [number, number, boolean][] = [];
  readonly error: string = "";

  constructor(text: string) {
    let all = !text.trim();
    let error = "";
    for (const raw of text.split(/[,;]/)) {
      const item = raw.trim();
      if (!item) continue;
      if (item === "*") {
        all = true;
        continue;
      }
      try {
        if (item.includes("-")) {
          const [a, b] = item.split("-");
          const [lo, extA] = parseId(a);
          const [hi, extB] = parseId(b);
          if (hi < lo) throw new Error(item);
          this.ranges.push([lo, hi, extA || extB]);
        } else if (item.includes("/")) {
          const [a, b] = item.split("/");
          const [id, ext] = parseId(a);
          this.masks.push([id, parseId(b)[0], ext]);
        } else {
          const [id, ext] = parseId(item);
          this.exact.add(`${ext ? "x" : ""}${id}`);
        }
      } catch {
        error = item;
      }
    }
    this.all = all;
    this.error = error;
  }

  matches(raw: number): boolean {
    if (this.all) return true;
    const ext = isExtended(raw);
    const id = ext ? raw % 0x20000000 : raw % 0x800;
    if (this.exact.has(`${ext ? "x" : ""}${id}`)) return true;
    for (const [want, mask, wantExt] of this.masks) if (wantExt === ext && (id & mask) === (want & mask)) return true;
    for (const [lo, hi, wantExt] of this.ranges) if (wantExt === ext && id >= lo && id <= hi) return true;
    return false;
  }
}

/** Hex CAN ID -> [id, extended]; 1-3 digits = 11-bit, longer = 29-bit. */
export function parseId(text: string): [number, boolean] {
  let digits = text.trim();
  if (digits.toLowerCase().startsWith("0x")) digits = digits.slice(2);
  if (!/^[0-9a-fA-F]{1,8}$/.test(digits)) throw new Error(`bad CAN ID ${text}`);
  const id = parseInt(digits, 16);
  if (id > 0x1fffffff) throw new Error(`CAN ID ${text} is out of range`);
  return [id, digits.length > 3 || id > 0x7ff];
}

export class Api {
  constructor(private readonly hass: () => HomeAssistant) {}

  subscribe(callback: (event: FeedEvent) => void): Promise<() => Promise<void>> {
    return this.hass().connection.subscribeMessage<FeedEvent>(callback, { type: "woow_can/subscribe" });
  }

  snapshot(): Promise<Snapshot> {
    return this.hass().callWS({ type: "woow_can/snapshot" });
  }

  subscribeMonitor(source: string, token: string, callback: (batch: MonitorBatch) => void): Promise<() => Promise<void>> {
    return this.hass().connection.subscribeMessage<MonitorBatch>(callback, { type: "woow_can/monitor/subscribe", source, token });
  }

  ack(token: string, seq: number): Promise<void> {
    return this.hass().callWS({ type: "woow_can/monitor/ack", token, seq });
  }

  clearMonitor(source: string): Promise<void> {
    return this.hass().callWS({ type: "woow_can/monitor/clear", source });
  }

  trace(source: string, opts: { before?: number | null; limit?: number; ids?: string; direction?: string | null }): Promise<TracePage> {
    return this.hass().callWS({
      type: "woow_can/trace",
      source,
      limit: opts.limit ?? 200,
      ids: opts.ids ?? "",
      ...(opts.before != null ? { before: opts.before } : {}),
      ...(opts.direction ? { direction: opts.direction } : {}),
    });
  }

  send(entryId: string, frame: string, waitMs = 0, waitId = ""): Promise<SendResult> {
    return this.hass().callWS({
      type: "woow_can/send",
      entry_id: entryId,
      frame,
      wait_ms: waitMs,
      ...(waitId ? { wait_id: waitId } : {}),
    });
  }

  setEvents(entryId: string, eventFilter: string): Promise<void> {
    return this.hass().callWS({ type: "woow_can/interface/events", entry_id: entryId, event_filter: eventFilter });
  }

  savePeriodic(item: Partial<Periodic>): Promise<Periodic> {
    return this.hass().callWS({ type: "woow_can/periodic/save", item });
  }

  controlPeriodic(itemId: string, action: "start" | "stop" | "delete"): Promise<void> {
    return this.hass().callWS({ type: "woow_can/periodic/control", item_id: itemId, action });
  }

  captures(): Promise<{ captures: CaptureFile[]; offline: OfflineInfo[] }> {
    return this.hass().callWS({ type: "woow_can/capture/list" });
  }

  capture(
    action: "start" | "stop" | "delete" | "open" | "close" | "convert",
    args: { entry_id?: string; name?: string; source?: string; format?: string },
  ): Promise<{ name?: string; sources?: OfflineInfo[]; frames?: number }> {
    return this.hass().callWS({ type: "woow_can/capture/control", action, ...args });
  }

  analyzeBits(source: string, key: number, seconds?: number | null): Promise<BitActivity> {
    return this.hass().callWS({ type: "woow_can/analyze/bits", source, key, limit: 2000, ...(seconds ? { seconds } : {}) });
  }

  analyzeTry(source: string, key: number, signal: SignalSpec, seconds?: number | null): Promise<Series> {
    return this.hass().callWS({ type: "woow_can/analyze/try", source, key, signal, limit: 2000, ...(seconds ? { seconds } : {}) });
  }

  analyzeFind(
    source: string,
    action: "start" | "narrow" | "clear" | "status",
    args: { mode?: FindMode; value?: number | null; tolerance?: number | null } = {},
  ): Promise<FindResult> {
    const extra: Record<string, unknown> = {};
    if (args.mode) extra.mode = args.mode;
    if (args.value != null) extra.value = args.value;
    if (args.tolerance != null) extra.tolerance = args.tolerance;
    return this.hass().callWS({ type: "woow_can/analyze/find", source, action, limit: 30, ...extra });
  }

  analyzeGuided(source: string, action: "start" | "next" | "finish" | "cancel" | "status", label?: string): Promise<GuidedResult> {
    return this.hass().callWS({ type: "woow_can/analyze/guided", source, action, ...(label ? { label } : {}) });
  }

  addSignal(
    entryId: string,
    key: number,
    signal: SignalSpec,
    target: { device_id?: string; device_name?: string; message?: string },
    adopt = true,
  ): Promise<DeviceView> {
    return this.hass().callWS({ type: "woow_can/devices/add_signal", entry_id: entryId, key, signal, adopt, ...target });
  }

  saveDevice(device: Record<string, unknown>): Promise<DeviceView> {
    return this.hass().callWS({ type: "woow_can/devices/save", device });
  }

  deleteDevice(deviceId: string): Promise<void> {
    return this.hass().callWS({ type: "woow_can/devices/delete", device_id: deviceId });
  }

  setSignal(deviceId: string, message: string, signal: string, change: { adopted?: boolean; entity?: EntitySettings }): Promise<DeviceView> {
    return this.hass().callWS({ type: "woow_can/devices/signal", device_id: deviceId, message, signal, ...change });
  }

  createFromTemplate(template: string, entryId: string, name: string, params: Record<string, unknown>, groups: string[] | null): Promise<DeviceView> {
    return this.hass().callWS({ type: "woow_can/templates/create", template, entry_id: entryId, name, params, groups });
  }

  decode(source: string, raw: number, data: string): Promise<{ decoded: Decoded[] }> {
    return this.hass().callWS({ type: "woow_can/decode", source, raw, data });
  }

  dbc(action: "attach" | "delete" | "create_device", name: string, args: { interfaces?: string[]; entry_id?: string; device_name?: string; messages?: string[] } = {}): Promise<DeviceView | Record<string, never>> {
    return this.hass().callWS({ type: "woow_can/dbc/control", action, name, ...args });
  }

  async uploadDbc(file: File, attach: string[]): Promise<DatabaseSummary> {
    const query = `name=${encodeURIComponent(file.name)}${attach.length ? `&attach=${encodeURIComponent(attach.join(","))}` : ""}`;
    const res = await this.hass().fetchWithAuth(`/api/woow_can/dbc?${query}`, { method: "POST", body: file });
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    return (await res.json()) as DatabaseSummary;
  }

  /** Let the browser save a file served by the backend: a short-lived signed URL, no token in it. */
  async download(path: string): Promise<void> {
    const signed = await this.hass().callWS<{ path: string }>({ type: "auth/sign_path", path, expires: 60 });
    const link = document.createElement("a");
    link.href = this.hass().hassUrl(signed.path);
    link.download = "";
    document.body.appendChild(link);
    link.click();
    link.remove();
  }

  async upload(file: File): Promise<string> {
    const res = await this.hass().fetchWithAuth(`/api/woow_can/captures?name=${encodeURIComponent(file.name)}`, {
      method: "POST",
      body: file,
    });
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    return ((await res.json()) as { name: string }).name;
  }
}

export function errorText(err: unknown): string {
  if (err && typeof err === "object" && "message" in err) {
    return String((err as { message: unknown }).message);
  }
  return String(err);
}

export function randomToken(): string {
  return Math.random().toString(36).slice(2, 12) + Date.now().toString(36);
}

/** Define a custom element once, so a reloaded bundle does not throw on the second define. */
export function define(name: string, cls: CustomElementConstructor): void {
  if (!customElements.get(name)) {
    customElements.define(name, cls);
  }
}

export function storageGet<T>(key: string, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

export function storageSet(key: string, value: unknown): void {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* private mode or storage disabled: not remembered */
  }
}
