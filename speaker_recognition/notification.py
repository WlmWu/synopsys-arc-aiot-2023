from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

from datetime import datetime
import pytz

from .database import DBMananger
from .config import TIME_FORMAT, EMAIL_SENDER, GMAIL_APP_PASSWORD

class Notifier:
    def __init__(self) -> None:
        self._dbm = DBMananger()

    def send_email(self, sender: str, sender_app_pwd: str, content: MIMEMultipart):
        with smtplib.SMTP(host="smtp.gmail.com", port="587") as smtp:
            try:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(sender, sender_app_pwd)
                smtp.send_message(content)
                print(f"Sent Email to {content['to']}")
            except Exception as e:
                print("Error message: ", e)

    def send_clocked_in_out_email(self, eid: int, timestamp: str):
        employee = self._dbm.get_employee(eid)
        if employee == {}:
            return

        content = MIMEMultipart() 
        content["subject"] = "Clocked In/Out Notification"
        content["from"] = 'No Reply'
        content["to"] = employee['email']

        try:
            timestamp = datetime.strptime(timestamp, TIME_FORMAT).strftime('%m/%d/%Y %H:%M:%S')
        except ValueError:
            pass
        message = f"Successfully clocked in/out at {timestamp}"
        content.attach(MIMEText(message))

        self.send_email(EMAIL_SENDER, GMAIL_APP_PASSWORD, content)

if __name__ == '__main__':
    current_time = datetime.now(pytz.timezone('Asia/Taipei')).strftime(TIME_FORMAT)

    notifier = Notifier()
    notifier.send_clocked_in_out_email(1, current_time)