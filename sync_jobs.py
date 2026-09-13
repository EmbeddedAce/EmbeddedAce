import os
import json
import requests
import firebase_admin
from firebase_admin import credentials, firestore

service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
if not service_account_json:
    raise ValueError("FIREBASE_SERVICE_ACCOUNT environment variable is missing.")

cred_dict = json.loads(service_account_json)
cred = credentials.Certificate(cred_dict)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

def clean_dict(d):
    """Recursively remove any keys that start with double underscores to satisfy Firestore rules."""
    if isinstance(d, dict):
        return {k: clean_dict(v) for k, v in d.items() if not k.startswith("__")}
    elif isinstance(d, list):
        return [clean_dict(v) for v in d]
    else:
        return d

def fetch_and_sync_jobs():
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    
    if not app_id or not app_key:
        raise ValueError("Adzuna App ID or App Key environment variables are missing.")

    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": "Embedded Systems Engineer OR Firmware",
        "where": "Bengaluru",
        "content-type": "application/json"
    }

    print("Fetching jobs from Adzuna API for India/Bengaluru (Embedded Domain)...")
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    data = response.json()
    jobs = data.get("results", [])
    
    embedded_keywords = ["embedded", "firmware", "microcontroller", "stm32", "rtos", "hardware", "arm cortex", "iot"]
    filtered_jobs = []
    
    for job in jobs:
        title = job.get("title", "").lower()
        description = job.get("description", "").lower()
        if any(kw in title or kw in description for kw in embedded_keywords):
            # Recursively strip any nested keys starting with '__' (like '__class__')
            cleaned_job = clean_dict(job)
            filtered_jobs.append(cleaned_job)

    print(f"Filtered {len(filtered_jobs)} relevant embedded jobs out of {len(jobs)} total fetched. Syncing to Firestore...")

    batch = db.batch()
    for job in filtered_jobs:
        job_id = str(job.get("id"))
        if job_id:
            doc_ref = db.collection("jobs").document(job_id)
            batch.set(doc_ref, job, merge=True)

    batch.commit()
    print("Successfully synced embedded jobs to Firebase Firestore!")

if __name__ == "__main__":
    fetch_and_sync_jobs()
