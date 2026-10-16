// Recordings tab: record interfaces to candump log files, download / upload / open / convert them, export the buffer.

import { LitElement, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import { Api, CaptureFile, FILE_FORMATS, FileFormat, InterfaceInfo, OfflineInfo, define, errorText } from "../api";
import { Translate, ago, bytes, isKey } from "../i18n";
import { shared } from "../styles";

export class WoowCanCapture extends LitElement {
  @property({ attribute: false }) interfaces: InterfaceInfo[] = [];
  @property({ attribute: false }) offline: OfflineInfo[] = [];
  @property({ attribute: false }) files: CaptureFile[] = [];
  @property({ attribute: false }) t!: Translate;
  @property({ attribute: false }) api!: Api;

  @state() private message: { ok: boolean; text: string } | null = null;
  @state() private deleting = "";
  @state() private busy = false;
  @state() private format: FileFormat = "log";

  static styles = [
    shared,
    css`
      .ifaces {
        display: grid;
        gap: 10px;
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
      td.num {
        text-align: right;
        font-variant-numeric: tabular-nums;
      }
      input[type="file"] {
        display: none;
      }
    `,
  ];

  private async run(task: () => Promise<unknown>, ok?: string): Promise<void> {
    this.busy = true;
    try {
      await task();
      this.message = ok ? { ok: true, text: ok } : null;
    } catch (err) {
      this.message = { ok: false, text: this.t("error", { msg: errorText(err) }) };
    } finally {
      this.busy = false;
    }
  }

  private changed(): void {
    this.dispatchEvent(new CustomEvent("captures-changed"));
  }

  private async upload(e: Event): Promise<void> {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = "";
    if (!file) return;
    await this.run(async () => {
      const name = await this.api.upload(file);
      this.message = { ok: true, text: this.t("uploaded", { name }) };
      this.changed();
    });
  }

  private ext(name: string): string {
    const dot = name.lastIndexOf(".");
    return dot < 0 ? "" : name.slice(dot + 1).toLowerCase();
  }

  private formatName(format: string): string {
    const key = `fmt_${format}`;
    return isKey(key) ? this.t(key) : format;
  }

  private async convert(name: string): Promise<void> {
    await this.run(async () => {
      const res = await this.api.capture("convert", { name, format: this.format });
      this.message = { ok: true, text: this.t("converted", { name: res.name ?? "", n: (res.frames ?? 0).toLocaleString() }) };
      this.changed();
    });
  }

  private formatPicker() {
    const t = this.t;
    return html`<label class="row" style="gap:6px">
      <span class="muted">${t("file_format")}</span>
      <select .value=${this.format} @change=${(e: Event) => (this.format = (e.target as HTMLSelectElement).value as FileFormat)}>
        ${FILE_FORMATS.map((f) => html`<option value=${f} ?selected=${f === this.format}>${t(`fmt_${f}`)}</option>`)}
      </select>
    </label>`;
  }

  private async open(name: string): Promise<void> {
    await this.run(async () => {
      const res = await this.api.capture("open", { name });
      const source = res.sources?.[0];
      if (source) this.dispatchEvent(new CustomEvent("open-source", { detail: source.id }));
    }, this.t("opened"));
  }

  render() {
    const t = this.t;
    return html`<div class="card">
        <div class="row">
          <h2 class="grow">${t("capture_title")}</h2>
          ${this.formatPicker()}
        </div>
        <div class="muted">${t("capture_hint")}</div>
        ${this.format === "csv" ? html`<div class="muted" style="margin-top:4px">${t("csv_note")}</div>` : nothing}
        <div class="ifaces" style="margin-top:12px">
          ${this.interfaces.map((i) => html`<div class="row">
            <b>${i.name}</b><span class="muted">${i.port}</span>
            <span class="grow"></span>
            ${i.recording
              ? html`<span class="chip bad">● ${t("recording", { n: i.recording.frames.toLocaleString(), size: bytes(i.recording.bytes) })}</span>
                  <button ?disabled=${this.busy} @click=${() =>
                    this.run(async () => {
                      await this.api.capture("stop", { entry_id: i.id });
                      this.changed();
                    })}>${t("stop_record")}</button>`
              : html`<button class="primary" ?disabled=${this.busy} @click=${() =>
                  this.run(async () => {
                    await this.api.capture("start", { entry_id: i.id });
                    this.changed();
                  })}>${t("record")}</button>`}
            <button title=${t("export_hint", { n: (i.trace.end - i.trace.first).toLocaleString() })}
              @click=${() => this.run(() => this.api.download(`/api/woow_can/export/${i.id}?format=${this.format}`))}>${t("export")}</button>
          </div>`)}
        </div>
        ${this.message
          ? html`<div class="chip ${this.message.ok ? "ok" : "bad"}" style="margin-top:10px;white-space:normal">${this.message.text}</div>`
          : nothing}
      </div>
      <div class="card">
        <div class="row">
          <h2 class="grow">${t("files_title")}</h2>
          <label><button title=${t("upload_hint")} @click=${() => (this.renderRoot.querySelector("#upload") as HTMLInputElement)?.click()}>
            ${t("upload")}</button></label>
          <input id="upload" type="file" accept=".log,.txt,.asc,.csv,.trc,.crtd,.pcap" @change=${this.upload} />
        </div>
        ${this.files.length === 0
          ? html`<div class="empty">${t("files_empty")}</div>`
          : html`<div class="wrap"><table>
              <tbody>
                ${this.files.map((f) => html`<tr>
                  <td class="mono">${f.recording ? html`<span class="chip bad">●</span> ` : nothing}${f.name}</td>
                  <td class="num">${bytes(f.size)}</td>
                  <td class="muted">${ago(f.modified, t)}</td>
                  <td class="row">
                    <button class="link" @click=${() =>
                      this.run(() => this.api.download(`/api/woow_can/captures/${encodeURIComponent(f.name)}`))}>${t("download")}</button>
                    <button class="link" ?disabled=${f.recording} @click=${() => this.open(f.name)}>${t("open")}</button>
                    <button class="link" ?disabled=${f.recording || this.busy || this.ext(f.name) === this.format}
                      title=${t("convert_hint", { fmt: t(`fmt_${this.format}`) })}
                      @click=${() => this.convert(f.name)}>${t("convert")} → ${this.format.toUpperCase()}</button>
                    ${this.deleting === f.name
                      ? html`<span>${t("delete_confirm", { name: f.name })}</span>
                          <button class="danger" @click=${() =>
                            this.run(async () => {
                              this.deleting = "";
                              await this.api.capture("delete", { name: f.name });
                              this.changed();
                            })}>${t("delete")}</button>
                          <button @click=${() => (this.deleting = "")}>${t("cancel")}</button>`
                      : html`<button class="link danger" ?disabled=${f.recording} @click=${() => (this.deleting = f.name)}>
                          ${t("delete")}</button>`}
                  </td>
                </tr>`)}
              </tbody>
            </table></div>`}
        ${this.offline.length
          ? html`<h2 style="margin-top:16px">${t("offline_title")}</h2>
              ${this.offline.map((o) => html`<div class="row">
                <span class="mono grow">${o.name}</span>
                <span class="muted">${o.format && o.format !== "log" ? `${this.formatName(o.format)} · ` : ""}${o.frames.toLocaleString()}${o.truncated ? ` · ${t("truncated", { n: o.frames })}` : ""}</span>
                <button class="link" @click=${() => this.dispatchEvent(new CustomEvent("open-source", { detail: o.id }))}>
                  ${t("tab_monitor")}</button>
                <button class="link" @click=${() => this.run(() => this.api.capture("close", { source: o.id }))}>${t("close")}</button>
              </div>`)}`
          : nothing}
      </div>`;
  }
}

define("woow-can-capture", WoowCanCapture);
