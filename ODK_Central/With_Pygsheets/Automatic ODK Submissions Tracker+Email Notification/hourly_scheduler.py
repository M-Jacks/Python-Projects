import schedule
import time
from main import main
from email_notifier import send_email
from dotenv import load_dotenv
import os

load_dotenv()

receiver_email = os.getenv('RECEIVER_EMAIL')

def job():
    print("🔁 Updating Image submissions summary...")
    result = main()
    send_email(
        subject="✅ ODK Summary Update",
        body=result,
        to_email=receiver_email
    )

if __name__ == "__main__":
    job()

    schedule.every(1).hours.do(job)

    print("🕒 Scheduler started. Will run every 1 hour...")
    while True:
        schedule.run_pending()
        time.sleep(60)
