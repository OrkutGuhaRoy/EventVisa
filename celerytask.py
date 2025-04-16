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

app=Celery('celerytask',broker='redis://localhost',backend='redis://localhost')

@app.task
def send_email(sender,reciever,subject,message):
    msg=MIMEMultipart()
    msg['From']=sender
    msg['To']=reciever
    msg['Subject']=subject
    msg.attach(MIMEText(message))
    smtp_server='smtp.gmail.com'
    smtp_port=587
    smtp_username=sender
    smtp_password='your_password_here'  # Replace with your actual password

    with smtplib.SMTP(smtp_server,smtp_port) as server:
        server.starttls()
        server.login(smtp_username,smtp_password)
        server.sendmail(sender,reciever,msg.as_string())


@app.task
def download_csv(theater_data):
        csv_data = []
        for value in theater_data:
            csv_data.append(value)

        csv_output = io.StringIO()
        csv_writer = csv.writer(csv_output)
        csv_writer.writerow(csv_data)

        response = Response(csv_output.getvalue(), content_type='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename={theater_data[1]}_details.csv'
        return response
    