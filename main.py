import os
import sys
import logging
import datetime
import xml.etree.ElementTree as ET
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 設定日誌系統 ---
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- 載入環境變數 ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

if not all([GEMINI_API_KEY, LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID]):
    logger.error("❌ 環境變數缺失！請檢查 .env 檔案。")
    sys.exit(1)

# --- 初始化 Google GenAI Client ---
client = genai.Client(api_key=GEMINI_API_KEY)

def get_target_date():
    return datetime.date.today()

def search_news():
    """
    透過 Google News RSS 搜尋 BIM 相關新聞（不受 GitHub Actions IP 封鎖）
    權重：BIM-AI(5則) > BIM-MEP(3則) > BIM總體(2則)
    """
    logger.info("🔍 開始搜尋 BIM 相關新聞...")

    # (分類標籤, 搜尋關鍵字, 最多幾則)
    topics = [
        ("BIM x AI",  "BIM artificial intelligence OR BIM machine learning OR BIM AI automation OR generative AI BIM",  5),
        ("BIM-MEP",   "BIM MEP coordination OR mechanical electrical plumbing BIM OR MEP clash detection BIM",          3),
        ("BIM 總覽",  "Building Information Modeling OR BIM construction OR BIM architecture OR OpenBIM IFC",           2),
    ]

    results = []

    for label, query, max_count in topics:
        rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en"
        try:
            resp = requests.get(rss_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")
            count = 0
            for item in items:
                if count >= max_count:
                    break
                title = item.findtext("title", "").strip()
                description = item.findtext("description", "").strip()
                # 用 source url（出版商網域）取代無法追蹤的 Google News redirect URL
                source_el = item.find("source")
                source_url = source_el.attrib.get("url", "").strip() if source_el is not None else ""
                source_name = source_el.text.strip() if source_el is not None and source_el.text else ""
                if title and source_url:
                    results.append(f"類別: {label}\n標題: {title}\n摘要: {description}\n來源: {source_name}\n網址: {source_url}")
                    count += 1
            logger.info(f"   [{label}] 取得 {count} 則新聞")
        except Exception as e:
            logger.warning(f"   [{label}] 搜尋失敗: {e}")

    logger.info(f"✅ 搜尋完成，共 {len(results)} 則。")
    return results

def generate_summary(news_list, target_date):
    """
    使用 Gemini 生成專業報告 (包含自動降級機制)
    """
    if not news_list:
        return None

    date_str = target_date.strftime("%Y/%m/%d")
    logger.info("🧠 Gemini 正在構思新聞報告...")

    prompt = (
        f"今天是 {date_str}。\n\n"
        "你是一個超愛 BIM 的辣妹，講話直接、有點嗆、偶爾毒舌，但每句話都有料。\n\n"
        "請把下面的新聞整理成 LINE 日報，嚴格遵守以下格式，不可多也不可少：\n\n"
        "【格式規定】\n"
        "第一行：今日 BIM 速報 📡（固定開頭，不要加日期）\n"
        "---\n"
        "【BIM x AI】\n"
        "從這類新聞中挑 2～3 則最重要的，每則：1～2 句說重點 + 換行 + 📰 來源名稱。每則之間空一行。\n"
        "---\n"
        "【BIM-MEP】\n"
        "從這類新聞中挑 1～2 則，每則：1～2 句說重點 + 換行 + 📰 來源名稱。每則之間空一行。\n"
        "---\n"
        "【BIM 動態】\n"
        "從這類新聞中挑 1 則，1～2 句說重點 + 換行 + 📰 來源名稱。\n"
        "---\n"
        "最後一行：1 句辣妹金句，不超過 20 字。\n\n"
        "【硬性限制】\n"
        "- 每則說重點最多 2 句，不超過 50 字\n"
        "- 來源格式固定：📰 加上資料裡的「來源」欄位文字，不要自己亂改\n"
        "- 不要寫開場白、不要寫日期、不要寫自我介紹\n"
        "- 整份日報總字數控制在 400 字以內\n\n"
        "原始新聞資料：\n" + "\n---\n".join(news_list)
    )

    candidate_models = ['gemini-2.0-flash', 'gemini-flash-latest']

    for model_name in candidate_models:
        try:
            logger.info(f"🧪 嘗試使用模型: {model_name} 進行撰寫...")
            
            response = client.models.generate_content(
                model=model_name, 
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.75
                )
            )
            logger.info(f"✨ 成功使用 {model_name} 完成報告！")
            return response.text
            
        except Exception as e:
            logger.warning(f"⚠️ 模型 {model_name} 執行失敗 (可能是額度不足或不支援): {e}")
            logger.info("🔄 正在切換至下一個備援模型...")
            continue # 繼續迴圈，試下一個模型

    logger.error("❌ 所有模型皆嘗試失敗，無法生成報告。")
    return None

def send_line_push(message):
    logger.info("🚀 正在發送 LINE 訊息...")

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }

    payload = {
        'to': LINE_USER_ID,
        'messages': [{'type': 'text', 'text': message}]
    }

    target_url = 'https://api.line.me/v2/bot/message/push'

    try:
        # 設定 30 秒逾時
        logger.info(f"📡 正在連線至: {target_url}")
        resp = requests.post(
            target_url,
            headers=headers,
            json=payload,
            timeout=30
        )

        if resp.status_code == 200:
            logger.info("✅ LINE 訊息發送成功！")
        else:
            logger.error(f"❌ LINE 發送失敗: {resp.status_code} - {resp.text}")

    except Exception as e:
        logger.error(f"❌ LINE 發送發生錯誤: {e}")

def main():
    today = get_target_date()
    news = search_news()

    if not news:
        logger.warning("📭 今天沒有足夠的新聞，跳過。")
        return

    summary = generate_summary(news, today)
    
    if summary:
        print("\n" + "="*30)
        print(summary)
        print("="*30 + "\n")
        send_line_push(summary)


if __name__ == "__main__":
    main()
