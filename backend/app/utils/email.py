import os
import smtplib
from email.mime.text import MIMEText
from ..models.models import Employee, Test

def send_assignment_email(db, user_id, test_id, due_date):
    employee = db.query(Employee).filter_by(user_id=user_id).first()
    test = db.query(Test).filter_by(id=test_id).first()
    subject = f"New Test Assigned: {test.test_name}"
    body = f"Dear {employee.name},\nYou have been assigned the test '{test.test_name}'. Please complete it by {due_date}."
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = os.getenv("FROM_EMAIL", "noreply@yourdomain.com")
    msg['To'] = employee.email

    smtp_server = os.getenv("SMTP_SERVER", "smtp.example.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_feedback_email(db, user_id, test_id):
    """
    Send an email to the user notifying them that feedback for their test is available.
    """
    employee = db.query(Employee).filter_by(user_id=user_id).first()
    test = db.query(Test).filter_by(quiz_id=test_id).first()
    if not employee or not test:
        print("Employee or Test not found for feedback email.")
        return False
    subject = f"Your Feedback for Test: {test.test_name} is Ready"
    body = f"Dear {employee.name},\nYour feedback for the test '{test.test_name}' is now available. Please log in to view your feedback and results."
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = os.getenv("FROM_EMAIL", "noreply@yourdomain.com")
    msg['To'] = employee.email

    smtp_server = os.getenv("SMTP_SERVER", "smtp.example.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send feedback email: {e}")
        return False
