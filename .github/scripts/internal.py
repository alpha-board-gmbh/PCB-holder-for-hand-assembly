import os
import requests
import matplotlib.pyplot as plt
import smtplib
import csv
from datetime import datetime
from email.message import EmailMessage

# ==== Konfigurationsdaten aus GitHub Secrets ====

USERNAME = "alpha-board-gmbh"
TOKEN = os.environ["TOKEN_PERSONAL"]  # dein klassischer GitHub-Token
REPO = "alpha-board-gmbh/PCB-holder-for-hand-assembly"

MAIL_FROM = os.environ["SMTP_USER"]
MAIL_TO = os.environ["MAIL_TO"]
SMTP_SERVER = os.environ["SMTP_SERVER"]
SMTP_PORT = int(os.environ["SMTP_PORT"])
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]

# ==== GitHub API-Endpunkte für Trafficdaten ====

CLONES_URL = f"https://api.github.com/repos/{REPO}/traffic/clones"
VIEWS_URL = f"https://api.github.com/repos/{REPO}/traffic/views"
CSV_FILE = ".github/data/traffic.csv"  # Speicherort für die Langzeitdaten

headers = {"Accept": "application/vnd.github+json"}
auth = (USERNAME, TOKEN)

# ==== Holt die Trafficdaten über die GitHub API ====
def fetch_data(url):
    r = requests.get(url, headers=headers, auth=auth)
    r.raise_for_status()  # Fehler bei ungültigem Token oder Zugriff
    return r.json()

# ==== Speichert Tagesdaten dauerhaft in einer CSV-Datei ====
def save_to_csv(views, clones):
    existing_dates = set()

    # Bestehende Einträge lesen
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r") as f:
            reader = csv.reader(f)
            next(reader, None)  # Überschrift überspringen
            for row in reader:
                existing_dates.add(row[0])  # Nur das Datum merken

    rows = []
    for v in views["views"]:
        date = v["timestamp"][:10]
        if date not in existing_dates:
            # Finde passenden Klon-Zähler für das Datum
            clone_count = next((c["count"] for c in clones["clones"] if c["timestamp"][:10] == date), 0)
            rows.append([date, v["count"], clone_count])
            existing_dates.add(date)

    # Neue Zeilen schreiben
    if rows:
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            if os.stat(CSV_FILE).st_size == 0:
                writer.writerow(["Date", "Views", "Clones"])  # Kopfzeile, falls Datei leer
            writer.writerows(rows)

# ==== Erstellt den bekannten Plot der letzten 14 Tage ====
def plot_daily(views, clones):
    view_dates = [v["timestamp"][:10] for v in views["views"]]
    view_counts = [v["count"] for v in views["views"]]

    clone_dates = [c["timestamp"][:10] for c in clones["clones"]]
    clone_counts = [c["count"] for c in clones["clones"]]

    plt.figure(figsize=(10, 5))
    plt.plot(view_dates, view_counts, label="Views", marker="o")
    plt.plot(clone_dates, clone_counts, label="Clones", marker="x")
    plt.title("GitHub Traffic – letzte 14 Tage")
    plt.xlabel("Datum")
    plt.ylabel("Zugriffe")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    filename = f"traffic_daily_{datetime.now().strftime('%Y-%m-%d')}.png"
    plt.savefig(filename)
    plt.close()
    return filename

# ==== Erstellt kumulierten Plot aus der CSV-Datei ====
def plot_cumulative():
    dates = []
    view_sums = []
    clone_sums = []
    total_views = 0
    total_clones = 0

    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        # Zeilen nach Datum sortieren
        for row in sorted(reader, key=lambda r: r["Date"]):
            dates.append(row["Date"])
            total_views += int(row["Views"])
            total_clones += int(row["Clones"])
            view_sums.append(total_views)
            clone_sums.append(total_clones)

    plt.figure(figsize=(10, 5))
    plt.plot(dates, view_sums, label="Kumulierte Views", marker="o")
    plt.plot(dates, clone_sums, label="Kumulierte Clones", marker="x")
    plt.title("Kumulierte GitHub-Zugriffe")
    plt.xlabel("Datum")
    plt.ylabel("Gesamt")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    filename = f"traffic_total_{datetime.now().strftime('%Y-%m-%d')}.png"
    plt.savefig(filename)
    plt.close()
    return filename

# ==== Sendet beide Plots als E-Mail ====
def send_mail(image1, image2):
    msg = EmailMessage()
    msg["Subject"] = "GitHub Traffic Report (aktuell + kumuliert)"
    msg["From"] = MAIL_FROM
    msg["To"] = MAIL_TO
    msg.set_content("Siehe Anhang: GitHub-Zugriffe der letzten 14 Tage + Langzeitverlauf.")

    # Beide Bilder anhängen
    for img in [image1, image2]:
        with open(img, "rb") as f:
            msg.add_attachment(f.read(), maintype="image", subtype="png", filename=os.path.basename(img))

    # E-Mail per SMTP senden
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(MAIL_FROM, SMTP_PASSWORD)
        smtp.send_message(msg)

# ==== Hauptlogik ====
def main():
    views = fetch_data(VIEWS_URL)
    clones = fetch_data(CLONES_URL)
    save_to_csv(views, clones)
    daily_plot = plot_daily(views, clones)
    total_plot = plot_cumulative()
    send_mail(daily_plot, total_plot)

if __name__ == "__main__":
    main()
