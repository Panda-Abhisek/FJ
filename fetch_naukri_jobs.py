import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import telegram

# --- Configurable Filters ---
FILTERS = {
    "keywords": "java",
    "experience": 0,
    "posted_within_hours": 1,
    "location": ["Remote", "Bengaluru", "Hyderabad", "India"],
    "job_type": ["Internship", "Full Time", "Job"],
}

NAUKRI_URL = f"https://www.naukri.com/{FILTERS['keywords']}-jobs?experience={FILTERS['experience']}&jobAge=1"
CSV_FILE = "jobs.csv"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
}

def fetch_jobs():
    response = requests.get(NAUKRI_URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    jobs = []
    for job_card in soup.select(".jobTuple"):
        title = job_card.select_one(".title.fw500").get_text(strip=True)
        company = job_card.select_one(".subTitle.ellipsis.fleft").get_text(strip=True)
        location = job_card.select_one(".locWdth").get_text(strip=True)
        posted = job_card.select_one(".type.br2.fleft.grey").get_text(strip=True)
        link = job_card.select_one("a.title.fw500")['href']

        if any(loc.lower() in location.lower() for loc in FILTERS["location"]):
            jobs.append({
                "Title": title,
                "Company": company,
                "Location": location,
                "Posted": posted,
                "Link": link
            })

    return jobs

def save_to_csv(jobs):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["Title", "Company", "Location", "Posted", "Link"])
        writer.writeheader()
        for job in jobs:
            writer.writerow(job)

def send_email():
    from_addr = os.environ['EMAIL_USER']
    to_addr = os.environ['EMAIL_TO']
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = "Daily Java Jobs for Freshers"

    with open(CSV_FILE, "rb") as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={CSV_FILE}')
        msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(from_addr, os.environ['EMAIL_PASS'])
        server.send_message(msg)

def send_telegram(jobs):
    bot = telegram.Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    message = "\U0001F4CC *Today's Java Jobs (Freshers)*\n\n"

    for job in jobs[:10]:
        message += f"\n[{job['Title']}]({job['Link']}) - {job['Company']} ({job['Location']})\nPosted: {job['Posted']}\n"

    bot.send_message(chat_id=chat_id, text=message, parse_mode=telegram.ParseMode.MARKDOWN)

if __name__ == "__main__":
    jobs = fetch_jobs()
    if jobs:
        save_to_csv(jobs)
        send_email()
        send_telegram(jobs)
    else:
        print("No jobs found matching the filters.")
