// Overview tab: one health card per interface (state, load, error counters, drops, hints).

import { LitElement, css, html, nothing, svg } from "lit";
import { property } from "lit/decorators.js";

import { InterfaceInfo, define } from "../api";
import { Key, Translate, ago, clock, errorCode, isKey, percent } from "../i18n";
import { shared } from "../styles";

const STATE_CLASS: Record<string, string> = {
  error_active: "ok",
  error_warning: "warn",
  error_passive: "warn",
  bus_off: "bad",
  stopped: "",
  sleeping: "",
  virtual: "info",
};

export class WoowCanOverview extends LitElement {
  @property({ attribute: false }) interfaces: InterfaceInfo[] = [];
  @property({ attribute: false }) history: Record<string, number[]> = {};
  @property({ attribute: false }) t!: Translate;

  static styles = [
    shared,
    css`
      .cards {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(min(100%, 340px), 1fr));
        gap: 16px;
      }
      .card {
        margin: 0;
        display: grid;
        gap: 10px;
        align-content: start;
      }
      .head {
        display: flex;
        flex-wrap: wrap;
        align-items: baseline;
        gap: 6px 10px;
      }
      .head b {
        font-size: 1.15em;
      }
      .bar {
        height: 8px;
        border-radius: 99px;
        background: var(--secondary-background-color, #eee);
        overflow: hidden;
      }
      .bar i {
        display: block;
        height: 100%;
        background: var(--primary-color);
        transition: width 0.3s;
      }
      .bar.hot i {
        background: var(--warning-color, #ff9800);
      }
      dl {
        display: grid;
        grid-template-columns: auto 1fr;
        gap: 4px 12px;
        margin: 0;
        font-size: 0.92em;
      }
      dt {
        color: var(--secondary-text-color);
      }
      dd {
        margin: 0;
        text-align: right;
        font-variant-numeric: tabular-nums;
      }
      @media (max-width: 520px) {
        dl {
          grid-template-columns: 1fr;
          gap: 0;
        }
        dt {
          margin-top: 6px;
        }
        dd {
          text-align: left;
        }
      }
      .hint {
        font-size: 0.9em;
        line-height: 1.5;
        padding: 6px 10px;
        border-radius: 8px;
        background: rgba(255, 152, 0, 0.12);
      }
      .hint.bad {
        background: rgba(219, 68, 55, 0.12);
      }
      .hint.info {
        background: rgba(3, 169, 244, 0.1);
      }
      svg.spark {
        width: 100%;
        height: 36px;
        display: block;
      }
      .spark polyline {
        fill: none;
        stroke: var(--primary-color);
        stroke-width: 1.5;
      }
      .spark polygon {
        fill: var(--primary-color);
        opacity: 0.12;
      }
      .spark line {
        stroke: var(--divider-color, #ddd);
        stroke-width: 1;
      }
    `,
  ];

  private stateLabel(info: InterfaceInfo): string {
    if (!info.available) return this.t("unavailable");
    const state = String(info.status.state ?? "unknown");
    const key = `state_${state}`;
    return isKey(key) ? this.t(key as Key) : state;
  }

  private sparkline(points: number[]) {
    if (points.length < 2) return nothing;
    const max = Math.max(10, ...points);
    const w = 300;
    const h = 36;
    const step = w / (points.length - 1);
    const xy = points.map((v, i) => `${(i * step).toFixed(1)},${(h - 2 - (v / max) * (h - 4)).toFixed(1)}`);
    return html`<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" role="img" aria-label=${this.t("sparkline")}>
      ${svg`<line x1="0" y1=${h - 1} x2=${w} y2=${h - 1}></line>
        <polygon points=${`0,${h - 1} ${xy.join(" ")} ${w},${h - 1}`}></polygon>
        <polyline points=${xy.join(" ")}></polyline>`}
    </svg>`;
  }

  private hints(info: InterfaceInfo) {
    const t = this.t;
    const s = info.status;
    const out: { cls: string; text: string }[] = [];
    if (info.settings.listen_only && !info.virtual) out.push({ cls: "info", text: t("hint_listen_only") });
    if (s.state === "bus_off") {
      out.push({
        cls: "bad",
        text: info.settings.restart_ms ? t("hint_bus_off_auto", { ms: info.settings.restart_ms }) : t("hint_bus_off_manual"),
      });
    } else if (s.state === "error_passive" && Number(s.tx_error_counter ?? 0) >= 128) {
      out.push({ cls: "warn", text: t("hint_passive") });
    }
    if (Number(s.rx_over_errors ?? 0) > 0) out.push({ cls: "warn", text: t("hint_overflow", { n: Number(s.rx_over_errors) }) });
    if (Number(s.socket_drops ?? 0) > 0) out.push({ cls: "warn", text: t("hint_socket_drops", { n: Number(s.socket_drops) }) });
    return out;
  }

  private card(info: InterfaceInfo) {
    const t = this.t;
    const s = info.status;
    const load = info.load;
    const berr = s.berr_reporting
      ? `${s.bus_error ?? 0} · ${t("arbitration_lost")} ${s.arbitration_lost ?? 0}`
      : s.berr_supported
        ? t("reporting_off")
        : t("not_supported");
    const settings = info.virtual
      ? [t("virtual_iface")]
      : [
          t("kbps", { n: Math.round(info.settings.bitrate / 1000) }),
          ...(info.settings.fd ? [t("can_fd")] : []),
          ...(info.settings.listen_only ? [t("listen_only")] : []),
        ];
    const last = info.errors.last;
    const state = String(s.state ?? "");
    return html`<div class="card">
      <div class="head">
        <b>${info.name}</b>
        <span class="muted">${info.port} · ${info.driver || "?"} · ${settings.join(" · ")}</span>
        <span class="grow"></span>
        <button class="link" @click=${() => this.dispatchEvent(new CustomEvent("open-monitor", { detail: info.id }))}>
          ${t("open_monitor")}
        </button>
      </div>
      <div class="row">
        <span class="chip ${info.available ? (STATE_CLASS[state] ?? "") : "bad"}">${this.stateLabel(info)}</span>
        ${s.tx_error_counter != null
          ? html`<span class="muted">${t("tec_rec")} ${s.tx_error_counter} / ${s.rx_error_counter}</span>`
          : nothing}
        ${info.recording
          ? html`<span class="chip bad">● ${t("recording_now", { name: info.recording.name, n: info.recording.frames })}</span>`
          : nothing}
      </div>
      ${this.hints(info).map((h) => html`<div class="hint ${h.cls}">${h.text}</div>`)}
      ${info.virtual
        ? nothing
        : html`<div>
            <div class="row">
              <span>${t("load")}</span><span class="grow"></span>
              <b>${percent(load.now)}</b>
            </div>
            <div class="bar ${(load.now ?? 0) > 70 ? "hot" : ""}" title=${t("load_hint")}>
              <i style="width:${Math.min(100, load.now ?? 0)}%"></i>
            </div>
            <div class="muted" style="margin-top:4px">
              ${t("load_values", {
                now: percent(load.now),
                peak: percent(load.peak),
                a1: percent(load.avg[0]),
                a5: percent(load.avg[1]),
                a15: percent(load.avg[2]),
              })}
            </div>
            ${this.sparkline(this.history[info.id] ?? [])}
          </div>`}
      <dl>
        <dt>${t("traffic")}</dt>
        <dd>${t("rates", { rx: (load.rx_fps ?? 0).toFixed(1), tx: (load.tx_fps ?? 0).toFixed(1) })}</dd>
        <dt>${t("seen")}</dt>
        <dd>${t("ids_seen", { n: info.monitor.ids, f: info.monitor.frames.toLocaleString() })}</dd>
        ${info.virtual
          ? nothing
          : html`<dt>${t("controller_events")}</dt>
              <dd>${s.error_warning ?? "–"} / ${s.error_passive ?? "–"} / ${s.bus_off ?? "–"} / ${s.restarts ?? "–"}</dd>
              <dt>${t("bus_errors")}</dt>
              <dd>${berr}</dd>`}
        <dt>${t("drops")}</dt>
        <dd>${s.socket_drops ?? 0} / ${s.rx_over_errors ?? 0} / ${s.events_dropped ?? 0}</dd>
        <dt>${t("last_error")}</dt>
        <dd>
          ${last
            ? html`<span title=${`${clock(last.t)} · ${last.frame}`}
                >${last.codes.map((c) => errorCode(c, t)).join("、")} · ${ago(last.t, t)}</span
              >`
            : t("none")}
        </dd>
      </dl>
      <div class="muted">
        ${info.settings.event_filter ? t("events_filter", { x: info.settings.event_filter }) : t("events_none")}
        ${s.clock ? html` · ${t("clock_mhz", { n: Number(s.clock) / 1e6 })}` : nothing}
        ${s.sample_point ? html` · ${t("sample_point", { n: (Number(s.sample_point) * 100).toFixed(1) })}` : nothing}
      </div>
    </div>`;
  }

  render() {
    if (!this.interfaces.length) {
      return html`<div class="card"><div class="empty">${this.t("no_interfaces")}</div></div>`;
    }
    return html`<div class="cards">${this.interfaces.map((info) => this.card(info))}</div>`;
  }
}

define("woow-can-overview", WoowCanOverview);
