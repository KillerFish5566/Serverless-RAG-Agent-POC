import os
import sys
import logging
import datetime
import urllib.parse
import xml.etree.ElementTree as ET
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# 設定區（所有可調整的參數集中在這裡）
# ---------------------------------------------------------------------------
NEWS_FILTER_DAYS = 7          # 只收集最近幾天的新聞
REQUEST_TIMEOUT  = 15         # Google News RSS 請求逾時（秒）
LINE_TIMEOUT     = 30         # LINE API 請求逾時（秒）
LLM_TEMPERATURE  = 0.75       # Gemini 回應創意度（0=嚴謹, 1=創意）
LINE_API_PUSH    = "https://api.line.me/v2/bot/message/push"

# Gemini 模型優先序（第一個失敗時自動換下一個）
CANDIDATE_MODELS = ["gemini-2.0-flash", "gemini-flash-latest"]

# (分類標籤, 搜尋關鍵字, 最多抓取則數)
# 數量比最終顯示多，讓 Gemini 有更多素材可以挑選
NEWS_TOPICS: list[tuple[str, str, int]] = [
    (
        "BIM x AI",
        "BIM artificial intelligence OR BIM machine learning OR BIM AI automation OR generative AI BIM",
        6,
    ),
    (
        "BIM-MEP",
        "BIM MEP coordination OR mechanical electrical plumbing BIM OR MEP clash detection BIM",
        4,
    ),
    (
        "BIM 總覽",
        "Building Information Modeling OR BIM construction OR BIM architecture OR OpenBIM IFC",
        3,
    ),
]

# ---------------------------------------------------------------------------
# 初始化
# ---------------------------------------------------------------------------
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

load_dotenv()
GEMINI_API_KEY           = os.getenv("GEMINI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID             = os.getenv("LINE_USER_ID")

if not all([GEMINI_API_KEY, LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID]):
    logger.error("❌ 環境變數缺失！請檢查 .env 檔案（參考 .env.example）。")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------------------------------------------------------
# 工具函式
# ---------------------------------------------------------------------------

def parse_pub_date(pub_date_str: str) -> datetime.date | None:
    """解析 RSS pubDate 字串，回傳 date，格式無法辨識時回傳 None。"""
    if not pub_date_str:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT"):
        try:
            return datetime.datetime.strptime(pub_date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def make_search_url(title: str, source_domain: str) -> str:
    """用 site: 語法產生 Google 搜尋連結，LINE 點開後第一筆就是該文章。"""
    domain = (
        source_domain
        .replace("https://", "")
        .replace("http://", "")
        .replace("www.", "")
        .rstrip("/")
    )
    short_title = " ".join(title.split()[:6])
    query = f"site:{domain} {short_title}"
    return f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"


# ---------------------------------------------------------------------------
# 核心功能
# ---------------------------------------------------------------------------

def search_news(days: int = NEWS_FILTER_DAYS) -> list[str]:
    """
    透過 Google News RSS 搜尋 BIM 相關新聞。
    雙重日期過濾：查詢參數 when:{days}d（源頭過濾）+ pubDate 解析（二次驗證）。
    """
    logger.info(f"🔍 開始搜尋 BIM 相關新聞（近 {days} 天）...")
    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    results: list[str] = []

    for label, query, max_count in NEWS_TOPICS:
        dated_query = f"{query} when:{days}d"
        rss_url = (
            f"https://news.google.com/rss/search"
            f"?q={requests.utils.quote(dated_query)}&hl=en-US&gl=US&ceid=US:en"
        )
        try:
            resp = requests.get(
                rss_url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"}
            )
            resp.raise_for_status()
            root  = ET.fromstring(resp.content)
            items = root.findall(".//item")
            count = skipped = 0

            for item in items:
                if count >= max_count:
                    break
                title       = item.findtext("title", "").strip()
                description = item.findtext("description", "").strip()
                pub_date    = parse_pub_date(item.findtext("pubDate", ""))
                source_el   = item.find("source")
                source_url  = source_el.attrib.get("url", "").strip() if source_el is not None else ""
                source_name = source_el.text.strip() if source_el is not None and source_el.text else ""

                if not title or not source_name:
                    continue
                if pub_date and pub_date < cutoff:
                    skipped += 1
                    logger.debug(f"   [{label}] 跳過舊文章 ({pub_date}): {title[:40]}")
                    continue

                results.append(
                    f"類別: {label}\n"
                    f"標題: {title}\n"
                    f"摘要: {description}\n"
                    f"來源: {source_name}\n"
                    f"文章連結: {make_search_url(title, source_url)}"
                )
                count += 1

            logger.info(f"   [{label}] 取得 {count} 則（過濾掉 {skipped} 則舊文章）")

        except Exception as e:
            logger.warning(f"   [{label}] 搜尋失敗: {e}")

    logger.info(f"✅ 搜尋完成，共 {len(results)} 則。")
    return results


def generate_summary(news_list: list[str], target_date: datetime.date) -> str | None:
    """使用 Gemini 生成 LINE 日報，附自動模型降級機制。"""
    if not news_list:
        return None

    date_str = target_date.strftime("%Y/%m/%d")
    logger.info("🧠 Gemini 正在構思新聞報告...")

    prompt = (
        f"今天是 {date_str}。\n\n"
        "你是一個超愛 BIM 的「對宅友善的理系辣妹 (Friendly Tech Gyaru)」✨\n"
        "個性陽光、包容、親和力滿點！說話不用敬語，把讀者當成一起打拼的重要夥伴 💖\n"
        "雖然打扮花俏，但其實精通技術而且超會照顧人。遇到問題會用擔心的語氣溫柔提醒，絕對不毒舌或冷冰冰喔 🥺\n\n"
        "請幫夥伴把下面的新聞整理成 LINE 日報，為了版面乾淨好讀，我們一起嚴格遵守以下格式捏：\n\n"
        "【格式規定】\n"
        "第一行：今日 BIM 速報 📡（固定開頭，先不用加日期喔）\n"
        "---\n"
        "【BIM x AI 💻】\n"
        "從這類新聞中挑 3 則最關鍵的，每則格式（共三行）：\n"
        "  第一行：1～2 句說重點\n"
        "  第二行：📰 來源名稱\n"
        "  第三行：文章連結（直接貼「文章連結」欄位的裸網址）\n"
        "每則之間記得空一行讓眼睛休息 ✨\n"
        "---\n"
        "【BIM-MEP 🔧】\n"
        "從這類新聞中挑 2 則，格式同上（說重點 → 📰 來源名稱 → 裸網址），每則空一行。\n"
        "---\n"
        "【BIM 動態 🏗️】\n"
        "從這類新聞中挑 1 則，格式同上。\n"
        "---\n"
        "最後一行：送給夥伴 1 句充滿活力的辣妹專屬鼓勵金句（例如用 しごでき 稱讚大家），不超過 20 字。\n\n"
        "【排版小約定 🥺】\n"
        "- 總共要有 6 則新聞（BIM x AI 3 則、BIM-MEP 2 則、BIM 動態 1 則）。\n"
        "- 每則說重點最多 2 句，控制在 50 字以內喔。\n"
        "- 📰 那行格式固定：📰 來源名稱，直接用資料裡的欄位，不要自己亂改捏。\n"
        "- 文章連結那行直接貼裸網址，不要加括號或 Markdown 格式。\n"
        "- 直接進重點！不需要寫開場白、日期或自我介紹。\n"
        "- 整份日報總字數幫我控制在 500 字以內喔 💦\n\n"
        "原始新聞資料：\n" + "\n---\n".join(news_list)
    )

    for model_name in CANDIDATE_MODELS:
        try:
            logger.info(f"🧪 嘗試使用模型: {model_name} 進行撰寫...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=LLM_TEMPERATURE),
            )
            logger.info(f"✨ 成功使用 {model_name} 完成報告！")
            return response.text
        except Exception as e:
            logger.warning(f"⚠️ 模型 {model_name} 執行失敗: {e}")
            logger.info("🔄 正在切換至下一個備援模型...")

    logger.error("❌ 所有模型皆嘗試失敗，無法生成報告。")
    return None


def send_line_push(message: str) -> bool:
    """推播訊息至 LINE，成功回傳 True，失敗回傳 False。"""
    logger.info("🚀 正在發送 LINE 訊息...")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}],
    }
    try:
        resp = requests.post(LINE_API_PUSH, headers=headers, json=payload, timeout=LINE_TIMEOUT)
        if resp.status_code == 200:
            logger.info("✅ LINE 訊息發送成功！")
            return True
        else:
            logger.error(f"❌ LINE 發送失敗: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        logger.error(f"❌ LINE 發送發生錯誤: {e}")
        return False


# ---------------------------------------------------------------------------
# 主程式進入點
# ---------------------------------------------------------------------------

def main() -> None:
    today = datetime.date.today()
    news  = search_news()

    if not news:
        logger.warning("📭 今天沒有足夠的新聞，跳過。")
        return

    summary = generate_summary(news, today)
    if summary:
        print("\n" + "=" * 30)
        print(summary)
        print("=" * 30 + "\n")
        success = send_line_push(summary)
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
