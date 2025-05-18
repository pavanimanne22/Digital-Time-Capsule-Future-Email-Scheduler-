

import os
import mysql.connector
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

# Database connection
def connect_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Change this in production
            database=""
        )
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY, 
                to_emails TEXT, 
                cc_emails TEXT, 
                bcc_emails TEXT,
                subject VARCHAR(255), 
                message_text TEXT, 
                scheduled_date DATETIME, 
                status ENUM('pending', 'sent') DEFAULT 'pending',
                attachment_path VARCHAR(500) NULL
            )
        """)
        conn.commit()
        return conn
    except mysql.connector.Error as e:
        print(f"❌ Database Connection Error: {e}")
        return None

# Your Gmail account
EMAIL_ADDRESS = ""
EMAIL_PASSWORD = ""  # Use App Password



import smtplib
from email.message import EmailMessage


def send_email(to_emails, cc_emails, bcc_emails, subject, message_text, attachment_paths=None):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_emails
    if cc_emails:
        msg['Cc'] = cc_emails

    all_recipients = []
    all_recipients.extend(to_emails.split(','))
    if cc_emails:
        all_recipients.extend(cc_emails.split(','))
    if bcc_emails:
        all_recipients.extend(bcc_emails.split(','))

    msg.set_content(message_text)

    # Attach multiple files if any
    if attachment_paths:
        paths = [p.strip() for p in attachment_paths.split(',') if p.strip()]
        for path in paths:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    file_data = f.read()
                    file_name = os.path.basename(path)
                msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg, from_addr=EMAIL_ADDRESS, to_addrs=all_recipients)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False



def check_scheduled_messages():
    print("🔎 Checking scheduled messages...")

    conn = connect_db()
    if conn is None:
        print("❌ Could not connect to database.")
        return

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, to_emails, cc_emails, bcc_emails, subject, message_text, scheduled_date, attachment_path 
            FROM messages 
            WHERE status = 'pending'
        """)
        messages = cursor.fetchall()

        if not messages:
            print("✅ No pending messages.")
            return

        for msg in messages:
            msg_id, to_emails, cc_emails, bcc_emails, subject, message_text, scheduled_date, attachment_paths = msg
            if datetime.now() >= scheduled_date:
                print(f"📨 Sending message ID {msg_id}...")

                if send_email(to_emails, cc_emails or "", bcc_emails or "", subject, message_text, attachment_paths):
                    cursor.execute("UPDATE messages SET status = 'sent' WHERE id = %s", (msg_id,))
                    conn.commit()
                    print(f"✅ Message ID {msg_id} marked as sent.")
    except Exception as e:
        print(f"❌ Error checking messages: {e}")
    finally:
        cursor.close()
        conn.close()





# Scheduler to run every minute
scheduler = BlockingScheduler()
scheduler.add_job(check_scheduled_messages, "interval", minutes=1)

if __name__ == "__main__":
    print("📨 Email scheduler is running...")
    check_scheduled_messages()  # Initial check
    scheduler.start()

