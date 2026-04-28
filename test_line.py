"""
LINE API 診斷腳本
執行方式: python test_line.py
需要 .env 檔案含有 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_USER_ID
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")

print("=" * 50)
print("LINE API 診斷工具")
print("=" * 50)

# --- 1. 檢查環境變數 ---
print("\n[1/4] 檢查環境變數...")

if not TOKEN:
    print("  ❌ LINE_CHANNEL_ACCESS_TOKEN 未設定")
    sys.exit(1)
else:
    print(f"  ✅ TOKEN 已載入 (前10碼: {TOKEN[:10]}...)")

if not USER_ID:
    print("  ❌ LINE_USER_ID 未設定")
    sys.exit(1)
else:
    print(f"  ✅ USER_ID 已載入: {USER_ID}")
    if not USER_ID.startswith("U"):
        print("  ⚠️  警告：LINE User ID 通常以大寫 'U' 開頭，請確認這不是 Channel ID 或 Group ID")

# --- 2. 驗證 Token (呼叫 LINE Bot Info API) ---
print("\n[2/4] 驗證 Channel Access Token 是否有效...")

try:
    r = requests.get(
        "https://api.line.me/v2/bot/info",
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=10
    )
    if r.status_code == 200:
        bot_info = r.json()
        print(f"  ✅ Token 有效！Bot 名稱: {bot_info.get('displayName', 'N/A')}")
        print(f"     Bot UserID: {bot_info.get('userId', 'N/A')}")
    else:
        print(f"  ❌ Token 驗證失敗: HTTP {r.status_code}")
        print(f"     回應內容: {r.text}")
        print("  → 請至 LINE Developers Console 重新產生 Channel Access Token")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ 無法連線至 LINE API: {e}")
    sys.exit(1)

# --- 3. 嘗試發送測試訊息 ---
print("\n[3/4] 嘗試發送測試訊息...")

test_payload = {
    "to": USER_ID,
    "messages": [{"type": "text", "text": "🤖 LINE 診斷測試訊息 - 如果你看到這則訊息，代表設定正確！"}]
}

try:
    r = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}"
        },
        json=test_payload,
        timeout=15
    )

    print(f"  HTTP 狀態碼: {r.status_code}")
    print(f"  回應內容: {r.text}")

    if r.status_code == 200:
        print("  ✅ 訊息發送成功！請確認你的 LINE 是否收到測試訊息。")
    elif r.status_code == 400:
        print("  ❌ 請求格式錯誤 (400) — USER_ID 格式可能有誤")
    elif r.status_code == 401:
        print("  ❌ 授權失敗 (401) — Token 無效或已過期")
    elif r.status_code == 403:
        print("  ❌ 禁止存取 (403) — 此 Channel 可能未開啟 Push Message 權限")
        print("     → 請至 LINE Developers Console 確認 Messaging API 已啟用")
    elif r.status_code == 429:
        print("  ❌ 超過發送限制 (429) — 免費方案每月有 200 則上限")
    else:
        try:
            err = r.json()
            print(f"  ❌ 錯誤代碼: {err.get('message', '未知')}")
        except Exception:
            pass
except Exception as e:
    print(f"  ❌ 發送時發生例外: {e}")

# --- 4. 常見問題提示 ---
print("\n[4/4] 常見問題排查清單：")
print("  □ LINE_USER_ID 是否為你的個人 UID（以 'U' 開頭，非群組或頻道 ID）？")
print("    → 取得方式：在 LINE 官方帳號的 Webhook 事件中查看 source.userId")
print("  □ 你是否已將此 Bot 加為好友？未加好友無法接收 push 訊息")
print("  □ Token 是否為『長效 Token』(Long-lived)？短效 Token 會過期")
print("  □ GitHub Actions Secrets 的值是否與本地 .env 一致？")
print("\n" + "=" * 50)
