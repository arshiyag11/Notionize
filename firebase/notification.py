import requests

def send_discord_notification(message, webhook_url):
    payload = {"content": message}
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print("Notification sent successfully.")
        else:
            print(f"Error sending notification: {response.status_code}")
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
