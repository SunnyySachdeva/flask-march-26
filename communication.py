from smtplib import SMTP, SMTPException
from dotenv import load_dotenv
import os

load_dotenv()

class Email:
    def __init__(self):
        self.user = os.environ.get('SMTP_USER')
        self.password = os.environ.get('SMTP_PASSWORD')
        self.server = "smtp.hostinger.com"
        self.admin_url = os.environ.get('ADMIN_EMAIL')

    def send(self, message, user_email):
        try:
            with SMTP(self.server, 587) as connection:
                connection.starttls()
                connection.login(self.user, self.password)
                # admin mail
                connection.sendmail(from_addr=self.user, to_addrs=self.admin_url, msg=f"Subject:New request received\n\n{message}")
                # user mail
                connection.sendmail(from_addr=self.user, to_addrs=user_email, msg=f"Subject:Request Received\n\nWe have received your request. \nWe'll get back to you soon.\nTeam Blogggyyy")
        except SMTPException as e:
            print(e)
            return False
        except OSError as e:
            print(e)
            return False
        else:
            return True
