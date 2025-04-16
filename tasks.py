from celery import Celery
from celery.schedules import crontab
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import io
import csv
from flask import Response
import time
import datetime
import sqlite3

app=Celery('tasks',broker='redis://localhost',backend='redis://localhost')

app.conf.enable_utc= False
app.conf.timezone='Asia/Kolkata'

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour=20, minute=0),  # 8 PM every day
        send_daily_emails.s()
    )

@app.task
def send_daily_emails():
    conn = sqlite3.connect('eventvisa.db')
    cursor = conn.cursor()

    # Calculate the time range for the past day
    past_day = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)

    # Query to retrieve email addresses of users who haven't booked in a day
    query = '''
        SELECT DISTINCT u.Email
        FROM user u
        LEFT JOIN bookings b ON u.Email = b.user_email
        WHERE b.date IS NULL OR b.date < ?
    '''

    cursor.execute(query, (past_day,))
    email_addresses = [row[0] for row in cursor.fetchall()]


    # Close the database connection
    conn.close()
    
    smtp_server='smtp.gmail.com'
    smtp_port=587
    smtp_username='help.eventvisa@gmail.com'
    smtp_password='jxvpxpvbvphmhqnr'

    
    for email in email_addresses:
        try:
            subject = 'Reminder: Make a Booking'
            message = "Dear user, you haven't made a booking in the past day. Why Don't You Book A Movie Now?!"
            msg=MIMEMultipart()
            msg['From']="help.eventvisa@gmail.com"
            msg['To']=email
            msg['Subject']=subject
            msg.attach(MIMEText(message))

            with smtplib.SMTP(smtp_server,smtp_port) as server:
                server.starttls()
                server.login(smtp_username,smtp_password)
                server.sendmail('help.eventvisa@gmail.com',email,msg.as_string())
                print(f"Email sent to: {email}")
        except Exception as e:
            print(f"Failed to send email to {email}: {e}")


if __name__ == '__main__':
    app.run(debug=True)
