"""Write translations/en.json and zh-Hant.json for WOOW CAN 0.2.0 (both languages side by side)."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "custom_components" / "woow_can" / "translations"


def T(en, zh):
    return (en, zh)


CAN_DATA = {
    "name": T("Name", "名稱"),
    "bitrate": T("Bitrate", "速率"),
    "fd": T("CAN FD", "CAN FD"),
    "dbitrate": T("CAN FD data bitrate", "CAN FD 資料段速率"),
    "listen_only": T("Listen only", "只監聽"),
    "restart_ms": T("Restart after bus-off", "Bus-off 後自動重啟"),
    "filters": T("Receive filter", "接收過濾"),
    "event_filter": T("IDs that fire events", "觸發事件的 ID"),
    "max_events_per_sec": T("Max events per second", "每秒最多事件數"),
}
CAN_DESC = {
    "listen_only": T("Never acknowledge or send: watch an existing bus without touching it. Turn it off to send, "
                     "and on a bus where the only other node needs this host's acknowledgement.",
                     "不回 ACK 也不發送，用來監看既有匯流排而不干擾。要發送時請關掉；匯流排上如果只有對方一個節點，"
                     "它需要這台主機回 ACK，也要關掉。"),
    "restart_ms": T("0 = stay in bus-off until the entry is reloaded.", "0＝不自動重啟，要重新載入才會恢復。"),
    "filters": T("Only receive these IDs, comma separated: 123 (11-bit), 18FF50E5 (29-bit), 7E0/7F0 (ID/mask). "
                 "Empty = everything.",
                 "只接收這些 ID，用逗號分隔：123（11-bit）、18FF50E5（29-bit）、7E0/7F0（ID/遮罩）。空白＝全部接收。"),
    "event_filter": T("Received frames with these IDs fire woow_can_frame events and the event entity: 123, "
                      "18FF50E5, 7E0/7F0, 100-1FF, * = all. Empty = none (the panel's monitor still shows "
                      "everything). Each event is written to the history database.",
                      "收到這些 ID 的訊框時，才觸發 woow_can_frame 事件和事件實體：123、18FF50E5、7E0/7F0、100-1FF，"
                      "*＝全部。空白＝都不觸發（管理面板的監看仍會顯示全部）。每個事件都會寫進歷史資料庫。"),
    "max_events_per_sec": T("Events beyond this rate are counted but not fired.",
                            "超過這個速率的事件只計數、不觸發，避免拖慢 HA。"),
}


def pick(d, i):
    if isinstance(d, tuple):
        return d[i]
    if isinstance(d, dict):
        return {k: pick(v, i) for k, v in d.items()}
    if isinstance(d, list):
        return [pick(v, i) for v in d]
    return d


ERRORS = {
    "bad_filter": T("Invalid filter. Use hex IDs, optionally ID/MASK, separated by commas.",
                    "過濾格式錯誤。請用十六進位 ID，可加 /遮罩，以逗號分隔。"),
    "bad_event_filter": T("Invalid ID list. Use hex IDs, ID/MASK, FROM-TO ranges or *, separated by commas.",
                          "ID 清單格式錯誤。請用十六進位 ID、ID/遮罩、起-迄範圍或 *，以逗號分隔。"),
    "bad_vcan_name": T("Use vcan followed by a number, e.g. vcan0.", "請用 vcan 加數字，例如 vcan0。"),
    "vcan_failed": T("Could not create the virtual interface (the host kernel needs the vcan module).",
                     "無法建立虛擬介面（主機的 kernel 需要 vcan 模組）。"),
}

data = {
    "config": {
        "step": {
            "user": {
                "title": T("Add to WOOW CAN", "新增 WOOW CAN"),
                "menu_options": {
                    "interface": T("CAN interface on this host", "這台主機的 CAN 介面"),
                    "virtual": T("Virtual interface (vcan, for testing)", "虛擬介面（vcan，測試用）"),
                    "hub": T("Admin panel", "管理面板"),
                },
            },
            "interface": {
                "title": T("Add a CAN interface", "新增 CAN 介面"),
                "description": T("Pick the CAN interface to add. Interfaces that are already added are not listed.",
                                 "選擇要加入的 CAN 介面。已加入的介面不會列出。"),
                "data": {"port": T("Interface", "介面")},
            },
            "can": {
                "title": T("CAN interface {port}", "CAN 介面 {port}"),
                "description": T("Driver: {driver}. Every node on the bus must use the same bitrate. New interfaces "
                                 "start in listen-only mode.",
                                 "驅動程式：{driver}。同一條匯流排上的設備速率要一致。新加入的介面預設只監聽。"),
                "data": CAN_DATA,
                "data_description": CAN_DESC,
            },
            "virtual": {
                "title": T("Create a virtual interface", "建立虛擬介面"),
                "description": T("A CAN interface without hardware (vcan), for trying the panel, automations and "
                                 "agents. Frames sent on it by any program on this host are seen by all others. It is "
                                 "re-created after the host restarts and deleted with the entry.",
                                 "不接硬體的 CAN 介面（vcan），用來試管理面板、自動化和 AI。這台主機上任何程式在它上面送出的訊框，"
                                 "其他程式都收得到。主機重開機後會自動重建，刪除這個項目時一併刪除。"),
                "data": {"port": T("Interface name", "介面名稱")},
                "data_description": {"port": T("vcan followed by a number, e.g. vcan0.", "vcan 加數字，例如 vcan0。")},
            },
        },
        "error": ERRORS,
        "abort": {
            "already_configured": T("This interface is already added.", "這個介面已經加入過了。"),
            "no_interfaces": T("No free CAN interface found. To try WOOW CAN without hardware, add a virtual interface.",
                               "找不到還沒加入的 CAN 介面。沒有硬體也想試用的話，可以新增虛擬介面。"),
        },
    },
    "options": {
        "step": {
            "init": {
                "title": T("Interface settings", "介面設定"),
                "description": T("{port}. Changing only the event IDs or the event rate applies at once; other "
                                 "settings restart the interface.",
                                 "{port}。只改觸發事件的 ID 或事件速率會立即生效；改其他設定會重新啟動介面。"),
                "data": {k: v for k, v in CAN_DATA.items() if k != "name"},
                "data_description": CAN_DESC,
            }
        },
        "error": ERRORS,
    },
    "entity": {
        "text": {"send_frame": {"name": T("Send frame", "發送訊框")}},
        "sensor": {
            "last_frame": {"name": T("Last received frame", "最後接收訊框")},
            "last_sent_frame": {"name": T("Last sent frame", "最後發送訊框")},
            "bus_state": {
                "name": T("Bus state", "匯流排狀態"),
                "state": {
                    "error_active": T("Error active (normal)", "正常（Error active）"),
                    "error_warning": T("Error warning", "錯誤警告"),
                    "error_passive": T("Error passive", "錯誤被動"),
                    "bus_off": T("Bus off", "Bus off（已離線）"),
                    "stopped": T("Stopped", "已停止"),
                    "sleeping": T("Sleeping", "休眠"),
                    "virtual": T("Virtual interface", "虛擬介面"),
                },
            },
            "rx_frames": {"name": T("Frames received", "接收訊框數")},
            "tx_frames": {"name": T("Frames sent", "發送訊框數")},
            "bus_errors": {"name": T("Bus errors", "匯流排錯誤")},
            "bus_load": {"name": T("Bus load", "匯流排負載")},
        },
        "event": {
            "rx_frame": {"name": T("Frame received", "收到訊框"),
                         "state_attributes": {"event_type": {"state": {"frame": T("Frame", "訊框")}}}}
        },
    },
    "services": {
        "describe": {
            "name": T("Describe WOOW CAN", "說明 WOOW CAN"),
            "description": T("For AI agents: what this integration does, the frame notation, the workflow and the "
                             "interfaces with their health. Call it first. Call it with return_response: true.",
                             "給 AI 用：說明這個整合的用途、訊框寫法、操作流程，並列出各介面與健康狀態。請先呼叫這個。"
                             "要加 return_response: true。"),
        },
        "list_interfaces": {
            "name": T("List CAN interfaces", "列出 CAN 介面"),
            "description": T("The interfaces with state (error_active = healthy), bus load, error counters, drops "
                             "and the last error frame. Call it with return_response: true.",
                             "列出各介面的狀態（error_active＝正常）、匯流排負載、錯誤計數、丟包與最後一筆錯誤訊框。"
                             "要加 return_response: true。"),
        },
        "get_monitor": {
            "name": T("Get the per-ID monitor", "讀取依 ID 監看"),
            "description": T("One row per CAN ID and direction: count, rate, period, latest data and how often the "
                             "data changed. Call it with return_response: true.",
                             "每個 CAN ID（分收發方向）一列：次數、頻率、週期、最新資料、資料變化次數。要加 return_response: true。"),
            "fields": {
                "interface": {"name": T("Interface", "介面"),
                              "description": T("Name (CAN0), interface (can0) or config entry id; empty = all.",
                                               "名稱（CAN0）、介面（can0）或設定項目 ID；空白＝全部。")},
                "ids": {"name": T("IDs", "ID"),
                        "description": T("Only these IDs: 123, 18FF50E5, 7E0/7F0, 100-1FF.",
                                         "只看這些 ID：123、18FF50E5、7E0/7F0、100-1FF。")},
                "limit": {"name": T("Limit", "筆數上限"), "description": T("Rows per interface.", "每個介面最多幾列。")},
            },
        },
        "get_trace": {
            "name": T("Get the frame trace", "讀取時間序紀錄"),
            "description": T("Frames in time order, newest first, from the interface's buffer of recent frames. "
                             "Call it with return_response: true.",
                             "依時間排列的訊框（新的在前），取自介面最近訊框的緩衝。要加 return_response: true。"),
            "fields": {
                "interface": {"name": T("Interface", "介面"),
                              "description": T("Name (CAN0), interface (can0) or config entry id.",
                                               "名稱（CAN0）、介面（can0）或設定項目 ID。")},
                "ids": {"name": T("IDs", "ID"),
                        "description": T("Only these IDs: 123, 18FF50E5, 7E0/7F0, 100-1FF.",
                                         "只看這些 ID：123、18FF50E5、7E0/7F0、100-1FF。")},
                "direction": {"name": T("Direction", "方向"),
                              "description": T("rx = received, tx = sent from this host.", "rx＝收到，tx＝這台主機送出。")},
                "limit": {"name": T("Limit", "筆數上限"), "description": T("Frames to return.", "最多傳回幾筆。")},
                "before": {"name": T("Before", "更早於"),
                           "description": T("Continue an earlier call: its next_before.", "接續上一次呼叫：填它傳回的 next_before。")},
                "seconds": {"name": T("Last seconds", "最近幾秒"),
                            "description": T("Only frames from the last this many seconds.", "只看最近這幾秒的訊框。")},
            },
        },
        "get_activity": {
            "name": T("Get the activity log", "讀取活動紀錄"),
            "description": T("Who sent what or changed what, newest first. Call it with return_response: true.",
                             "誰送了什麼、改了什麼（新的在前）。要加 return_response: true。"),
            "fields": {"limit": {"name": T("Limit", "筆數上限"), "description": T("Entries to return.", "最多傳回幾筆。")}},
        },
        "list_periodic": {
            "name": T("List periodic sends", "列出週期發送"),
            "description": T("The periodic sends with their state. Call it with return_response: true.",
                             "列出週期發送與執行狀態。要加 return_response: true。"),
        },
        "list_captures": {
            "name": T("List recordings", "列出擷取檔"),
            "description": T("Recorded candump log files. Call it with return_response: true.",
                             "列出錄好的 candump 紀錄檔。要加 return_response: true。"),
        },
        "send": {
            "name": T("Send CAN frame", "發送 CAN 訊框"),
            "description": T("Send one CAN / CAN FD frame, optionally waiting for a reply ID. Admin only; the "
                             "interface must not be listen-only.",
                             "送出一筆 CAN／CAN FD 訊框，可以等待指定 ID 的回覆。限管理員；介面不能是只監聽。"),
            "fields": {
                "config_entry_id": {"name": T("Interface", "介面"), "description": T("The CAN interface to send on.", "要從哪個 CAN 介面送出。")},
                "interface": {"name": T("Interface name", "介面名稱"),
                              "description": T("Instead of the entry: name (CAN0) or interface (can0).",
                                               "也可以不選介面，改填名稱（CAN0）或介面（can0）。")},
                "frame": {"name": T("Frame", "訊框"),
                          "description": T("The whole frame in cansend notation: 123#11223344, 18FF50E5#01, 456##1AABB "
                                           "(CAN FD). Instead of CAN ID and data.",
                                           "用 cansend 寫法填整筆訊框：123#11223344、18FF50E5#01、456##1AABB（CAN FD）。"
                                           "可取代 CAN ID 和資料。")},
                "can_id": {"name": T("CAN ID", "CAN ID"),
                           "description": T("Hex. 1-3 digits = 11-bit, longer = 29-bit.", "十六進位。1–3 位數＝11-bit，更長＝29-bit。")},
                "data": {"name": T("Data", "資料"),
                         "description": T("Hex bytes: up to 8 (classic) or 64 (CAN FD).", "十六進位資料：一般 CAN 最多 8 byte，CAN FD 最多 64 byte。")},
                "extended": {"name": T("Extended ID", "擴充 ID"),
                             "description": T("Force a 29-bit ID (default: decided by the ID length).", "強制使用 29-bit ID（預設依 ID 長度判斷）。")},
                "fd": {"name": T("CAN FD", "CAN FD"),
                       "description": T("Send as a CAN FD frame (CAN FD must be on for the interface).", "以 CAN FD 訊框送出（介面要先開啟 CAN FD）。")},
                "brs": {"name": T("Bit rate switch", "切換速率（BRS）"),
                        "description": T("CAN FD: send the data phase at the data bitrate.", "CAN FD：資料段用資料段速率傳送。")},
                "rtr": {"name": T("Remote frame", "遠端訊框"), "description": T("Send a remote (RTR) frame.", "送出遠端請求（RTR）訊框。")},
                "wait_id": {"name": T("Reply ID", "回覆 ID"),
                            "description": T("Return the first received frame with this ID (waits 1 s unless wait_ms is set).",
                                             "傳回第一筆收到的這個 ID 的訊框（沒填等待時間就等 1 秒）。")},
                "wait_ms": {"name": T("Wait for reply", "等待回覆"),
                            "description": T("0 = do not wait; without a reply ID any received frame counts.",
                                             "0＝不等；沒填回覆 ID 時，收到任何訊框都算。")},
                "note": {"name": T("Note", "備註"),
                         "description": T("Why, in a few words; shown in the activity log.", "為什麼要送，簡短說明；會顯示在活動紀錄。")},
            },
        },
        "save_periodic": {
            "name": T("Save a periodic send", "儲存週期發送"),
            "description": T("Add or change a frame that is sent every period_ms. Saved sends are stopped after a "
                             "restart. Admin only.",
                             "新增或修改每隔 period_ms 送一次的訊框。重新啟動後都會先停止。限管理員。"),
            "fields": {
                "interface": {"name": T("Interface", "介面"),
                              "description": T("Name (CAN0), interface (can0) or config entry id.", "名稱（CAN0）、介面（can0）或設定項目 ID。")},
                "frame": {"name": T("Frame", "訊框"), "description": T("cansend notation, e.g. 305#0000000000000000.", "cansend 寫法，例如 305#0000000000000000。")},
                "period_ms": {"name": T("Period", "週期"), "description": T("10 ms or more.", "10 ms 以上。")},
                "count": {"name": T("Count", "次數"), "description": T("Stop after this many sends; 0 = until stopped.", "送幾次後自動停止；0＝直到手動停止。")},
                "name": {"name": T("Name", "名稱"), "description": T("Shown in the panel; default: the frame.", "面板上顯示的名稱；預設是訊框本身。")},
                "item": {"name": T("Existing send", "既有項目"), "description": T("Name or id of a send to change.", "要修改的項目名稱或 ID。")},
                "start": {"name": T("Start now", "立即開始"), "description": T("Start sending right after saving.", "存好後立刻開始送。")},
                "note": {"name": T("Note", "備註"), "description": T("Why, in a few words; shown in the activity log.", "為什麼要做，簡短說明；會顯示在活動紀錄。")},
            },
        },
        "control_periodic": {
            "name": T("Start, stop or delete a periodic send", "開始、停止或刪除週期發送"),
            "description": T("Admin only.", "限管理員。"),
            "fields": {
                "item": {"name": T("Periodic send", "週期發送"), "description": T("Its name or id.", "名稱或 ID。")},
                "action": {"name": T("Action", "動作"), "description": T("start, stop or delete.", "start（開始）、stop（停止）或 delete（刪除）。")},
                "note": {"name": T("Note", "備註"), "description": T("Why, in a few words; shown in the activity log.", "為什麼要做，簡短說明；會顯示在活動紀錄。")},
            },
        },
        "capture": {
            "name": T("Start or stop a recording", "開始或停止擷取"),
            "description": T("Record an interface's frames to a candump log file in the woow_can/captures folder of "
                             "the configuration directory. Admin only.",
                             "把介面的訊框錄成 candump 紀錄檔，存在設定資料夾的 woow_can/captures。限管理員。"),
            "fields": {
                "interface": {"name": T("Interface", "介面"), "description": T("Name (CAN0), interface (can0) or config entry id.", "名稱（CAN0）、介面（can0）或設定項目 ID。")},
                "action": {"name": T("Action", "動作"), "description": T("start or stop.", "start（開始）或 stop（停止）。")},
                "note": {"name": T("Note", "備註"), "description": T("Why, in a few words; shown in the activity log.", "為什麼要做，簡短說明；會顯示在活動紀錄。")},
            },
        },
        "clear_monitor": {
            "name": T("Clear the monitor", "清除監看"),
            "description": T("Start the per-ID statistics of an interface over. Admin only.", "把介面的依 ID 統計歸零重來。限管理員。"),
            "fields": {
                "interface": {"name": T("Interface", "介面"), "description": T("Name (CAN0), interface (can0) or config entry id.", "名稱（CAN0）、介面（can0）或設定項目 ID。")},
                "note": {"name": T("Note", "備註"), "description": T("Why, in a few words; shown in the activity log.", "為什麼要做，簡短說明；會顯示在活動紀錄。")},
            },
        },
    },
    "exceptions": {
        "not_loaded": {"message": T("{entry} is not a loaded WOOW CAN interface.", "{entry} 不是已載入的 WOOW CAN 介面。")},
        "not_available": {"message": T("{name} is not available right now.", "{name} 目前無法使用。")},
        "send_failed": {"message": T("{name}: sending failed: {error}", "{name}：發送失敗：{error}")},
        "tx_queue_full": {"message": T("{name}: the CAN transmit queue is full. Usually nothing on the bus acknowledges "
                                       "the frames: check wiring, termination and bitrate.",
                                       "{name}：CAN 發送佇列已滿。通常是匯流排上沒有其他節點回 ACK，請檢查接線、終端電阻和速率。")},
        "bad_frame": {"message": T("Invalid CAN frame: {error}", "CAN 訊框格式錯誤：{error}")},
        "listen_only": {"message": T("{name} is set to listen only and cannot send. Turn listen-only off in the "
                                     "interface settings first.",
                                     "{name} 設定為只監聽，不能發送。請先在介面設定關閉只監聽。")},
        "fd_off": {"message": T("{name}: CAN FD is off for this interface.", "{name}：這個介面沒有開啟 CAN FD。")},
        "bad_input": {"message": T("Invalid input: {error}", "輸入有誤：{error}")},
        "panel_not_loaded": {"message": T("The WOOW CAN admin panel entry is not loaded; add it under Settings › "
                                          "Devices & services › WOOW CAN.",
                                          "WOOW CAN 的管理面板項目沒有載入；請到「設定 › 裝置與服務 › WOOW CAN」新增。")},
        "unknown_interface": {"message": T("No WOOW CAN interface {interface}. Interfaces: {interfaces}.",
                                           "沒有叫 {interface} 的 WOOW CAN 介面。現有介面：{interfaces}。")},
        "no_interface": {"message": T("Give the interface: config_entry_id or interface.", "請指定介面：config_entry_id 或 interface。")},
        "no_frame": {"message": T("Give the frame: frame (123#1122) or can_id with data.", "請指定訊框：frame（123#1122）或 can_id 加 data。")},
        "bad_ids": {"message": T("Invalid ID list: {error}", "ID 清單格式錯誤：{error}")},
        "unknown_periodic": {"message": T("No periodic send {item}. Periodic sends: {items}.", "沒有叫 {item} 的週期發送。現有項目：{items}。")},
        "bad_periodic": {"message": T("Invalid periodic send: {error}", "週期發送設定有誤：{error}")},
    },
}

for i, lang in ((0, "en"), (1, "zh-Hant")):
    (OUT / f"{lang}.json").write_text(json.dumps(pick(data, i), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", lang)
