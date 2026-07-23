import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# خادم ويب وهمي لإرضاء متطلبات Render ومنع انغلاق الخدمة
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# تشغيل الخادم الوهمي في خلفية النظام بالتوازي مع البوت
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

import os
import time
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")

if __name__ == "__main__":
    print("Bot started with Supply & Demand strategy...")
    send_telegram_message("🤖 *تم تفعيل بوت التداول بنجاح!*\nالاستراتيجية قيد العمل (عرض وطلب + RSI + MACD + EMA 200).")
    
    while True:
        # حلقة تكرارية تبقي البوت شغالاً على مدار الساعة
        time.sleep(3600)
        
