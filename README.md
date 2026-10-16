# WOOW CAN

[English](README.en.md)

把 Linux 的 SocketCAN 介面（CAN／CAN FD）接進 Home Assistant：每個介面一個裝置，可以收發訊框、看匯流排狀態，收到的訊框能觸發自動化。不需要安裝額外套件。

RS485／RS232 請改用 [WOOW Serial](https://github.com/WOOWTECH/Woow_ha_serial)。

## 功能

- 自動找出主機上的 CAN 介面，例如 MCP2515、MCP2518FD。
- 介面設定：速率、CAN FD 和資料段速率（支援的控制器才會出現）、只監聽、bus-off 後自動重啟、接收過濾（`123, 7E0/7F0, 18FF50E5`）、每秒最多事件數。
  - HAOS 的 `ip` 指令不能設 CAN 速率，這個整合直接透過 netlink 設定。
- 每個介面的實體：

| 實體 | 用途 |
|---|---|
| `text.<介面>_send_frame` | 輸入訊框就送出，寫法跟 cansend 一樣：`123#11223344`、`18FF50E5#0102`、`123#R`、`456##1AABB`（CAN FD） |
| `sensor.<介面>_last_frame`／`_last_sent_frame` | 最後收到／送出的訊框，屬性裡有 ID、資料、長度 |
| `sensor.<介面>_bus_state` | 匯流排狀態：正常、錯誤警告、錯誤被動、Bus off、已停止 |
| `event.<介面>_rx_frame` | 每收到一筆觸發一次 |
| 收發訊框數、匯流排錯誤 | 診斷用 |

- 服務 `woow_can.send`：送出一筆訊框，可以等指定 ID 的回覆（`wait_id`、`wait_ms`），回覆會放在服務回應裡。
- 事件 `woow_can_frame`：每收到一筆送出一次，資料有 `name`、`interface`、`id`、`id_hex`、`data`、`length`、`extended`、`fd`、`brs`、`rtr`。

## 需求

- Home Assistant 2026.10 以上，主機要有 SocketCAN 介面（例如 Raspberry Pi 5 加 CAN HAT，在 HAOS 的 `config.txt` 啟用）。

## 安裝

**HACS**：自訂存放庫填入 `https://github.com/WOOWTECH/Woow_ha_can`（類別「整合」），下載後重新啟動。

**手動**：把 `custom_components/woow_can` 複製到 `custom_components/` 後重新啟動。

然後到「設定 → 裝置與服務 → 新增整合 → WOOW CAN」，選介面並設定速率。

## 範例

```yaml
triggers:
  - trigger: event
    event_type: woow_can_frame
    event_data:
      name: CAN0
      id_hex: "18FF50E5"
```

```yaml
action: woow_can.send
data:
  config_entry_id: <介面>
  can_id: "7DF"
  data: "02 01 0C"
  wait_id: "7E8"
  wait_ms: 500
response_variable: r   # r.reply.data
```

## 注意事項

- 匯流排上沒有其他節點時，送出的訊框沒有人回 ACK，狀態會變成「錯誤被動」並持續重送。重新載入這個介面就會清掉。
- 匯流排兩端各要有 120Ω 終端電阻，所有節點的速率要一致。
- 流量大的匯流排請設定接收過濾，並調整每秒最多事件數；超過的只計數，不會更新實體也不會觸發事件。

## 開發

```bash
pip install homeassistant==2026.10.1 pytest && pytest tests
```

`tools/check_can.py` 是在實機上用的檢查腳本，包含控制器內部迴路測試。

## 授權

MIT
