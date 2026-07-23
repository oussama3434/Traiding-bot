import requests

TOKEN = "8250531737:AAGyXgGThfPV-7UmA_skpmP4J6de-e0e7rk"
CHAT_ID = "-1004367810810"

def main():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": "🚀 تم تشغيل البوت بنجاح عبر منصة Render!"}
    res = requests.post(url, data=payload)
    print("Response:", res.text)

if __name__ == "__main__":
    main()
