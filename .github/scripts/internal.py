# Datei: .github/scripts/internal.py

import os
import requests
import matplotlib.pyplot as plt
import smtplib
from datetime import datetime
from email.message import EmailMessage

# GitHub & Mail-Konfiguration über Umgebungsvariablen
USERNAME = "alpha-board-gmbh"
TOKEN = os.environ["TOKEN_PERSONAL"]
REPO = "alpha-board-gmbh/PCB-holder-for-hand-assembly"
MAIL_FROM = os.environ["SMTP_USER"]
MAIL_TO = os.environ["MAIL_TO"]
SMTP_SERVER = os.environ["SMTP_SERVER"]
SMTP_PORT = int(os.environ["SMTP_PORT"])
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]

CLONES_URL = f"https://api.github.com/repos/{REPO}/traffic/clones"
VIEWS_URL = f"https://api.github.com/repos/{REPO}/traffic/views"
headers = {"Accept": "application/vnd.github+json"}
auth = (USERNAME, TOKEN)

def fetch_data(url):
    r = requests.get(url, headers=headers, auth=auth)
    try:
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {r.status_code} - {r.text}")
        return {}

def plot_traffic(views, clones):
    view_dates = [v["timestamp"][:10] for v in views["views"]]
    view_counts = [v["count"] for v in views["views"]]

    clone_dates = [c["timestamp"][:10] for c in clones["clones"]]
    clone_counts = [c["count"] for c in clones["clones"]]

    plt.figure(figsize=(10, 5))
    plt.plot(view_dates, view_counts, label="Views", marker="o")
    plt.plot(clone_dates, clone_counts, label="Clones", marker="x")
    plt.title("GitHub Traffic")
    plt.xlabel("Date")
    plt.ylabel("Count")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    filename = f"traffic_{datetime.now().strftime('%Y-%m-%d')}.png"
    plt.savefig(filename)
    plt.close()
    return filename

def send_mail(image_path):
    msg = EmailMessage()
    msg["Subject"] = "GitHub Traffic Report"
    msg["From"] = MAIL_FROM
    msg["To"] = MAIL_TO
    msg.set_content("Hier ist der aktuelle GitHub-Traffic-Plot im Anhang.")

    with open(image_path, "rb") as img:
        msg.add_attachment(img.read(), maintype="image", subtype="png", filename=image_path)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(MAIL_FROM, SMTP_PASSWORD)
        smtp.send_message(msg)

def main():
    views = fetch_data(VIEWS_URL)
    clones = fetch_data(CLONES_URL)

    print("VIEWS:", views)
    print("CLONES:", clones)

    if views and clones:
        plot_path = plot_traffic(views, clones)
        send_mail(plot_path)

if __name__ == "__main__":
    main()
