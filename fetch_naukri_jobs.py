import requests
from bs4 import BeautifulSoup
import csv
import os
import smtplib
from email.message import EmailMessage
import telegram

# === CONFIG ===
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === SCRAPE LOGIC ===
def fetch_java_jobs():
    url = "https://www.naukri.com/java-jobs?k=java&experience=0"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    job_cards = soup.find_all("article", class_="jobTuple")

    jobs = []
    for card in job_cards:
        title = card.find("a", class_="title")
        company = card.find("a", class_="subTitle")
        location = card.find("li", class_="location")
        posted = card.find("span", class_="fleft postedDate")
        link = title["href"] if title else ""

        jobs.append({
            "Title": title.text.strip() if title else "",
            "Company": company.text.strip() if company else "",
            "Location": location.text.strip() if location else "",
            "Posted": posted.text.strip() if posted else "",
            "Link": link
        })

    return jobs

# === CSV CREATOR ===
def save_to_csv(jobs, filename="jobs.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=jobs[0].keys())
        writer.writeheader()
        writer.writerows(jobs)
    print(f"[INFO] Saved {len(jobs)} jobs to {filename}")

# === EMAIL SENDER ===
def send_email(filename):
    msg = EmailMessage()
    msg["Subject"] = "Daily Java Fresher Jobs - Naukri"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    msg.set_content("Find attached the latest Java fresher jobs from Naukri.")

    with open(filename, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="octet-stream", filename=filename)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)
    print(f"[INFO] Sent CSV to {EMAIL_TO}")

# === TELEGRAM BOT ===
def send_telegram_links(jobs):
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    for job in jobs[:10]:  # Send top 10 to avoid spam
        msg = f"{job['Title']} at {job['Company']}\n{job['Location']} | {job['Posted']}\n{job['Link']}"
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    print(f"[INFO] Sent job links via Telegram")

# === MAIN ===
if __name__ == "__main__":
    jobs = fetch_java_jobs()
    if jobs:
        save_to_csv(jobs)
        send_email("jobs.csv")
        send_telegram_links(jobs)
    else:
        print("No jobs found matching the filters.")
