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

        if not data:
            print("⚠️ No JSON data received")
            return "No data", 400

        try:
            entry = data.get("entry", [])[0]

            if "changes" in entry:
                change = entry["changes"][0]
                value = change.get("value", {})
                comment_text = value.get("text", "")
                commenter_id = value.get("from", {}).get("id")
                post_id = value.get("post_id")

                if not (comment_text and commenter_id and post_id):
                    print("⚠️ Missing required fields in webhook payload")
                    return "Missing fields", 400

                if "link" in comment_text.lower():
                    product_url = post_map.get(post_id)
                    if product_url:
                        send_dm(commenter_id, product_url)
                    else:
                        print(f"🔍 No mapping found for post_id: {post_id}")
                else:
                    print("📌 Comment doesn't contain 'link', skipping.")
            else:
                print("⚠️ No 'changes' found in entry, skipping.")

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

    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"📬 DM Sent: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Failed to send DM: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
