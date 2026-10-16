# WOOW CAN

[English](README.en.md)

把 Linux 的 SocketCAN 介面（CAN／CAN FD）接進 Home Assistant：每個介面一個裝置，還有一個管理面板，可以依 ID 監看整條匯流排、看匯流排健康、發送與週期發送、錄製紀錄檔。面板能做的事，AI 也能透過服務做，並記在活動紀錄裡。不需要安裝額外套件。

RS485／RS232 請改用 [WOOW Serial](https://github.com/WOOWTECH/Woow_ha_serial)。

## 管理面板

側邊欄的「WOOW CAN」（限管理員），有五個分頁：

| 分頁 | 內容 |
|---|---|
| 總覽 | 每個介面一張健康卡：狀態（正常／錯誤警告／錯誤被動／Bus off）、TEC／REC、匯流排負載（目前、峰值、1／5／15 分鐘，附最近幾分鐘的曲線）、收送筆數、控制器事件、丟包、最後一筆錯誤訊框的白話說明，以及「沒有人回 ACK」這類提示 |
| 監看 | 每個 ID 一列（像 cansniffer、SavvyCAN）：數值變了就上色再慢慢淡掉，上升青、下降紅，一直在跳的（計數器、校驗碼）灰紫；Notch 把一直在變的位元遮掉，只看你操作時新亮起來的；篩選、釘選、二進位顯示。暫停後切成依時間排列的紀錄，可以往回翻。手機上每個 ID 是一張卡片 |
| 發送 | 用 cansend 寫法送一筆（可等指定 ID 的回覆）；週期發送清單（週期、次數、開始／停止）。第一次從某個介面發送會先確認 |
| 擷取 | 把介面錄成 candump 紀錄檔、下載緩衝區（最近 20 萬筆）、上傳紀錄檔，開啟後用同一套監看畫面離線看 |
| 活動 | AI（透過服務）和人（在面板）做的發送與變更，附使用者和備註 |

面板每 250 ms 收一批彙整，而且要回確認才會收下一批，所以匯流排很忙時，手機只會更新得慢一點，不會被 Home Assistant 斷線。

## 介面設定

- 自動找出主機上的 CAN 介面，例如 MCP2515、MCP2518FD。
- 速率、CAN FD 和資料段速率（支援的控制器才會出現）、只監聽（新加入的介面預設開啟）、bus-off 後自動重啟、接收過濾（`123, 7E0/7F0, 18FF50E5`）。
  - HAOS 的 `ip` 指令不能設定 CAN 速率，這個整合直接透過 netlink 設定。
- **觸發事件的 ID**：只有這些 ID 會觸發 `woow_can_frame` 事件和事件實體，例如 `123, 7E0/7F0, 100-1FF`，`*`＝全部，空白＝都不觸發（預設）。改這一項會立即生效，不必重新啟動介面。
- **虛擬介面（vcan）**：新增整合時選「虛擬介面」，不接硬體也能試面板、自動化和 AI；主機重開機後會自動重建。

## 實體

| 實體 | 用途 |
|---|---|
| `text.<介面>_send_frame` | 輸入訊框就送出，寫法跟 cansend 一樣：`123#11223344`、`18FF50E5#0102`、`123#R`、`456##1AABB`（CAN FD） |
| `sensor.<介面>_bus_state` | 匯流排狀態：正常、錯誤警告、錯誤被動、Bus off、已停止、虛擬介面 |
| `event.<介面>_rx_frame` | 收到「觸發事件的 ID」時觸發 |
| `sensor.<介面>_last_frame`／`_last_sent_frame` | 最後收到／送出的訊框，每秒最多更新一次。新加入的介面預設停用 |
| `sensor.<介面>_bus_load` | 匯流排負載（1 分鐘平均）。預設停用 |
| 收發訊框數、匯流排錯誤 | 診斷用 |

## 服務（也給 AI 用）

| 服務 | 用途 |
|---|---|
| `describe`、`list_interfaces` | 整合說明；各介面的狀態、負載、錯誤計數 |
| `get_monitor` | 依 ID 的彙整：次數、頻率、週期、最新資料、變化次數 |
| `get_trace` | 依時間排列的訊框（新的在前），可依 ID、方向、最近幾秒篩選 |
| `get_activity`、`list_periodic`、`list_captures` | 活動紀錄、週期發送、擷取檔 |
| `send` | 送出一筆訊框，可等回覆（`wait_id`、`wait_ms`）；可用 `frame: 7DF#02010C` 或 `can_id` 加 `data` |
| `save_periodic`、`control_periodic` | 新增或修改週期發送；開始、停止、刪除 |
| `capture` | 開始或停止錄製 |
| `clear_monitor` | 把介面的監看統計歸零 |

- 介面可以用設定項目 ID、名稱（CAN0）或介面名稱（can0）指定。
- 發送和改設定限管理員；查詢不限。所有發送與變更都會記進活動紀錄，`note` 欄位可以寫原因。
- Home Assistant 內建的 MCP 伺服器：同一組服務也是 LLM API「WOOW CAN」的工具。AI 的使用說明在 [llms.txt](llms.txt)。

## 需求

- Home Assistant 2026.10 以上，主機要有 SocketCAN 介面（例如 Raspberry Pi 5 加 CAN HAT，在 HAOS 的 `config.txt` 啟用）。沒有硬體也可以用虛擬介面。

## 安裝

**HACS**：自訂存放庫填入 `https://github.com/WOOWTECH/Woow_ha_can`（類別「整合」），下載後重新啟動。

**手動**：把 `custom_components/woow_can` 複製到 `custom_components/` 後重新啟動。

然後到「設定 → 裝置與服務 → 新增整合 → WOOW CAN」，選「這台主機的 CAN 介面」並設定速率。第一次安裝時會自動加入「管理面板」項目。

## 範例

收到 ID 18FF50E5 時執行自動化（先在介面設定的「觸發事件的 ID」填 `18FF50E5`）：

```yaml
triggers:
  - trigger: event
    event_type: woow_can_frame
    event_data:
      name: CAN0
      id_hex: "18FF50E5"
```

送出 OBD-II 請求並等回覆：

```yaml
action: woow_can.send
data:
  interface: CAN0
  frame: "7DF#02010C"
  wait_id: "7E8"
  wait_ms: 500
response_variable: r   # r.reply.data
```

每秒送一次心跳，送 60 次後自動停止：

```yaml
action: woow_can.save_periodic
data:
  interface: CAN0
  name: 心跳
  frame: "305#0000000000000000"
  period_ms: 1000
  count: 60
  start: true
```

## 資料庫與效能

- 監看、時間序紀錄、負載都在記憶體裡，不寫資料庫，也不經過 Home Assistant 的事件匯流排。
- 只有「觸發事件的 ID」會產生事件，而每個事件都會寫進歷史資料庫。只想在面板看的話，保持空白即可。
- 如果要對很忙的 ID 發事件，建議把事件排除在 recorder 之外：

```yaml
recorder:
  exclude:
    event_types:
      - woow_can_frame
```

- 500 kbit/s 滿載時每個介面約 3,100–4,500 筆／秒；每筆只做固定成本的處理。

## 注意事項

- 匯流排上沒有其他節點時，送出的訊框沒有人回 ACK，狀態會變成「錯誤被動」並持續重送。重新載入這個介面就會清掉。
- 匯流排兩端各要有 120Ω 終端電阻，所有節點的速率要一致。
- 只監聽模式不回 ACK。如果匯流排上只有對方一個節點，它需要這台主機回 ACK，就要關掉只監聽。
- MCP2515 只有 2 個接收緩衝區，匯流排很忙時會漏收（總覽會顯示控制器溢位）；它也不回報匯流排錯誤，總覽會寫「這顆控制器不回報」。
- 週期發送在 Home Assistant 重新啟動後都會先停止，不會開機就自己開始送。

## 從 0.1 升級

- 既有介面的「觸發事件的 ID」自動設為 `*`，維持每筆都觸發事件（上限每秒 20 筆）。要減少資料庫寫入，可以改成需要的 ID 或留空。
- 最後收發訊框感測器不再帶 `time` 屬性，屬性也不寫進資料庫；每秒最多更新一次。

## 開發

```bash
pip install homeassistant==2026.10.1 pytest && pytest tests
cd frontend && npm install && npm run build   # 面板（Lit），輸出到 custom_components/woow_can/frontend
```

- `tools/check_can.py`：實機檢查，包含控制器內部迴路測試。
- `tools/sim/can_sim.py`：在虛擬介面上模擬電池（Pylontech）、逆變器、J1939 引擎和 OBD-II ECU。
- `tools/can_live_check.py`：在 SSH add-on 裡對執行中的 Home Assistant 做端對端檢查（服務、面板 websocket、週期發送、事件、錄製）。

## 授權

MIT
