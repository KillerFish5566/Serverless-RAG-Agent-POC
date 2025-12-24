import os
from dotenv import load_dotenv
from google import genai

# 載入 API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ 找不到 API Key，請檢查 .env 檔案！")
    exit()

print(f"🔑 使用 API Key: {api_key[:5]}... 進行檢測")
print("📡 正在連線至 Google 查詢可用模型清單...\n")

try:
    client = genai.Client(api_key=api_key)
    
    # 不檢查屬性了，直接印出名字！
    print(f"{'模型代號 (Model Name)':<40}")
    print("-" * 50)
    
    # 這裡會列出所有你帳號能看到的模型
    for model in client.models.list(config={"page_size": 100}):
        # 有些版本 model.name 包含 'models/' 前綴，有些沒有，我們直接印出來看
        print(f"👉 {model.name}")

except Exception as e:
    print(f"❌ 發生錯誤: {e}")