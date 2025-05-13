# scheduler.py
import schedule
import time
from main import main
from email_notifier import send_email
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

receiver_email = os.getenv('RECEIVER_EMAIL')
def job():
    print("🔁 Running scheduled task...")
    result = main()
    send_email(
        subject="✅ ODK Summary Updated",
        body=result,
        to_email=receiver_email
    )

if __name__ == "__main__":
    # Run once at startup
    job()

    # Schedule to run every day at 5:30 PM
    schedule.every().day.at("17:30").do(job)

    print("🕒 Scheduler started. Will run daily at 5:30 PM...")
    while True:
        schedule.run_pending()
        time.sleep(60)
