from flask import Flask, request
import requests
import json
from config import VERIFY_TOKEN, ACCESS_TOKEN, GRAPH_URL, INSTAGRAM_ID

app = Flask(__name__)

# Load product mapping
with open("post_map.json", "r") as f:
    post_map = json.load(f)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return challenge
        return "Verification failed", 403

    if request.method == 'POST':
        data = request.get_json()
        print("📩 Received:", json.dumps(data, indent=2))

        try:
            entry = data["entry"][0]

            if "changes" in entry:  # Reel comment
                change = entry["changes"][0]
                value = change["value"]
                comment_text = value.get("text", "")
                commenter_id = value.get("from", {}).get("id")
                post_id = value.get("post_id")

                if "link" in comment_text.lower():
                    product_url = post_map.get(post_id)
                    if product_url and commenter_id:
                        send_dm(commenter_id, product_url)
            else:
                print("⚠️ Skipping non-comment event")

        except Exception as e:
            print(f"❌ Error handling webhook: {e}")

        return "ok", 200

def send_dm(user_id, text):
    url = f"{GRAPH_URL}/{INSTAGRAM_ID}/messages"
    headers = {"Content-Type": "application/json"}
    payload = {
        "recipient": {"id": user_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE",
        "access_token": ACCESS_TOKEN
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f"📬 DM Sent: {response.status_code} - {response.text}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
