# WOOW CAN

[English](README.en.md)

把 Linux 的 SocketCAN 介面（CAN／CAN FD）接進 Home Assistant：每個介面一個裝置，還有一個管理面板，可以依 ID 監看整條匯流排、看匯流排健康、發送與週期發送、錄製紀錄檔。面板能做的事，AI 也能透過服務做，並記在活動紀錄裡。不需要安裝額外套件。

RS485／RS232 請改用 [WOOW Serial](https://github.com/WOOWTECH/Woow_ha_serial)。

## 管理面板

側邊欄的「WOOW CAN」（限管理員），有七個分頁：

| 分頁 | 內容 |
|---|---|
| 總覽 | 每個介面一張健康卡：狀態（正常／錯誤警告／錯誤被動／Bus off）、TEC／REC、匯流排負載（目前、峰值、1／5／15 分鐘，附最近幾分鐘的曲線）、收送筆數、控制器事件、丟包、最後一筆錯誤訊框的白話說明，以及「沒有人回 ACK」這類提示 |
| 監看 | 每個 ID 一列（像 cansniffer、SavvyCAN）：數值變了就上色再慢慢淡掉，上升青、下降紅，一直在跳的（計數器、校驗碼）灰紫；Notch 把一直在變的位元遮掉，只看你操作時新亮起來的；篩選、釘選、二進位顯示。暫停後切成依時間排列的紀錄，可以往回翻。手機上每個 ID 是一張卡片 |
| 分析 | 找出未知訊號：引導式擷取（某個動作改變了哪些位元）、依數值找訊號、單一 ID 的位元熱度圖；找到的欄位一鍵變成實體（見下方「找出未知訊號」） |
| 裝置 | 範本、DBC 檔、即時數值、實體設定與曲線（見下方「裝置、範本與 DBC」） |
| 發送 | 用 cansend 寫法送一筆（可等指定 ID 的回覆）；週期發送清單（週期、次數、開始／停止）。第一次從某個介面發送會先確認 |
| 擷取 | 把介面錄成 candump 紀錄檔；下載緩衝區（最近 20 萬筆）時可選 candump、Vector ASC、SavvyCAN CSV、pcap（Wireshark）；上傳紀錄檔（candump、ASC、CSV、PEAK TRC、OVMS CRTD、pcap）後用同一套監看畫面離線看；擷取檔可以轉成其他格式 |
| 活動 | AI（透過服務）和人（在面板）做的發送與變更，附使用者和備註 |

面板每 250 ms 收一批彙整，而且要回確認才會收下一批，所以匯流排很忙時，手機只會更新得慢一點，不會被 Home Assistant 斷線。

## 裝置、範本與 DBC

「裝置」分頁把訊框解成數值，選定的訊號會變成 Home Assistant 實體（感測器、二元感測器）：

- **內建範本**（都只監聽、不發送，每個都附出處、授權、驗證依據和可信度）：

| 範本 | 適用 | 主要實體 |
|---|---|---|
| 低壓電池 BMS（0x35x） | Pylontech、BYD LVS、Seplos、REC、JK（Pylon 模式）等 48 V 電池，接 SMA、Victron、Deye、Sofar、GoodWe 逆變器 | 電量、健康度、電壓、電流、功率、溫度、充放電限制、保護／告警、允許充放電；SMA 告警、Victron 電芯極值與累計電量依實際流量自動加入 |
| J1939 引擎與車輛 | 卡車、巴士、發電機組、農機、船用柴油引擎 | 轉速、扭矩、車速、冷卻液／機油／燃油溫度、機油壓力與油位、油耗、油門、電瓶電壓、運轉時數 |
| J1939 作用中故障碼（DM1） | 同上，含多封包 BAM | 四個警示燈、故障數、故障碼（SPN／FMI） |
| NMEA 2000 電池／直流狀態 | Victron VE.Can（Lynx Shunt、MPPT）、船、露營車 | 電壓、電流、功率、溫度、電量、健康度、剩餘時間 |
| CANopen 節點監看 | 任何 CiA 301 設備 | 在線／離線（heartbeat 停止就變離線）、NMT 狀態、緊急錯誤碼 |

- **DBC 檔**：匯入後附加到介面，監看會用它命名和解碼訊框；從裡面挑訊息就能建立裝置。只讀需要的部分（訊息、訊號、Intel／Motorola、有號、浮點、數值表、註解、週期、多工、J1939 PGN），看不懂的行會列在匯入報告。
- **每個實體各自節流**：數值最少 1 秒更新一次、變化小於半個解析度不寫；訊息超過「3 倍週期與 5 秒取大者」沒收到就變成無法使用。可以在面板或用 `set_signal` 調整。
- 每個數值訊號都可以按「曲線」看即時變化。
- 解碼不依賴外部套件；正確性用研究時驗證過的實機與範例訊框測試，並在 CI 跟 cantools 交叉比對。

## 找出未知訊號

設備沒有 DBC 也沒有範本時，「分析」分頁帶你找出訊號在哪裡（對象是「監看」分頁選的來源）：

- **引導式擷取**：按「開始」讓設備保持不動，按「下一步」後做動作（開門、按按鈕、開燈）並維持，再按「下一步」還原；重複兩三次後按「完成」。結果依差異排出 ID：每次都跟著動作改變的位元（開關、燈號）、數值整段改變的位元組、只在動作時出現的 ID。計數器會自動辨認並排除，人按下一步的時間差也不影響判斷。
- **依數值找訊號**：從設備螢幕讀一個數值（例如 52.3 V）開始，數值改變後輸入新數值篩選，重複到只剩一兩個欄位；會試位元組、字組、半位元組、位元，兩種位元組順序、有號無號，以及常見比例與偏移（0.1、0.01、−40、−273…）。不知道數值時，也可以只說「變大／變小／有變／沒變」來篩。
- **單一 ID 的位元**：每個位元最近變動的頻率用顏色顯示；點兩個位元就定出欄位，馬上看解出來的數值曲線。
- 找到的欄位按「加入裝置」就變成實體（1 位元是二元感測器，其他是感測器），可以加到既有裝置或建新裝置。
- 監看分頁每個 ID 展開後也有「位元分析」可以直接跳過來。

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
| `capture`、`convert_capture` | 開始或停止錄製；把擷取檔轉成 ASC、CSV 或 pcap |
| `clear_monitor` | 把介面的監看統計歸零 |
| `list_templates`、`create_from_template` | 列出範本；由範本建立裝置（不指定群組時依流量判斷） |
| `list_devices`、`get_device`、`save_device`、`delete_device` | 裝置的目前數值、完整定義；用 JSON 建立或修改裝置；刪除 |
| `set_signal` | 把訊號變成實體或取消，或調整最短間隔、容差、逾時 |
| `decode_frame`、`test_signal` | 用介面上的定義解一筆訊框；拿最近的訊框試算一段位元（找數值在哪） |
| `guided_capture`、`find_signal`、`bit_activity`、`add_signal` | 找出未知訊號：引導式擷取、依數值找訊號、位元活動；把找到的欄位加進裝置 |
| `import_dbc`、`list_databases`、`attach_dbc`、`create_from_dbc` | 匯入 DBC、附加到介面、從 DBC 建立裝置 |

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
- `tools/sim/can_sim.py`：在虛擬介面上模擬電池（Pylontech）、逆變器、J1939 引擎、NMEA 2000、CANopen 節點、OBD-II ECU，以及可以用 `6F0#01`（開門）、`6F0#02`（開燈）操作的車身控制器。
- `tools/can_live_check.py`：在 SSH add-on 裡對執行中的 Home Assistant 做端對端檢查（服務、面板 websocket、週期發送、事件、錄製）。
- `tools/template_check.py`：每個範本對照模擬器的實機檢查。
- `tools/analysis_check.py`：檔案格式和分析工具的端對端檢查（轉檔、上傳 ASC、依數值找電池電壓、引導式擷取找出車門位元、加入裝置）。

## 授權

MIT
