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

def fetch_and_sync_jobs():
    url = "https://www.arbeitnow.com/api/job-board-api"

    print("Fetching jobs from Arbeitnow API...")
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    data = response.json()
    jobs = data.get("data", [])
    
    keywords = ["embedded", "firmware", "systems", "hardware"]
    filtered_jobs = [
        j for j in jobs 
        if any(kw in j.get("title", "").lower() or kw in j.get("description", "").lower() for kw in keywords)
    ]
    
    print(f"Filtered {len(filtered_jobs)} relevant jobs out of {len(jobs)} total. Syncing to Firestore...")

    batch = db.batch()
    for job in filtered_jobs:
        job_id = job.get("slug")
        if job_id:
            doc_ref = db.collection("jobs").document(job_id)
            batch.set(doc_ref, job, merge=True)

    batch.commit()
    print("Successfully synced jobs to Firebase Firestore!")

if __name__ == "__main__":
    fetch_and_sync_jobs()
