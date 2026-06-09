import logging
import os
import requests

def main(myblob: bytes, name: str):
    logging.info(f"Blob uploaded: {name}")
    send_email(name)

def send_email(filename):
    api_key = os.environ["SENDGRID_API_KEY"]

    requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        json={
            "personalizations": [
                {"to": [{"email": "you@example.com"}]}
            ],
            "from": {"email": "noreply@functionapp.com"},
            "subject": f"New file uploaded: {filename}",
            "content": [
                {
                    "type": "text/plain",
                    "value": f"A file was uploaded: {filename}"
                }
            ]
        },
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )
