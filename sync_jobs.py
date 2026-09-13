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
    rapidapi_key = os.environ.get("RAPIDAPI_KEY")
    if not rapidapi_key:
        raise ValueError("RAPIDAPI_KEY environment variable is missing.")

    # Check your RapidAPI dashboard playground code snippet for the exact endpoint URL path
    url = "https://jsearch.p.rapidapi.com/search"
    querystring = {"query": "Embedded Systems Engineer", "page": "1", "num_pages": "1"}
    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }

    print("Fetching jobs from RapidAPI...")
    response = requests.get(url, headers=headers, params=querystring)
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    data = response.json()
    jobs = data.get("data", [])
    print(f"Fetched {len(jobs)} jobs. Syncing to Firestore...")

    batch = db.batch()
    for job in jobs:
        job_id = job.get("job_id")
        if job_id:
            doc_ref = db.collection("jobs").document(job_id)
            batch.set(doc_ref, job, merge=True)

    batch.commit()
    print("Successfully synced jobs to Firebase Firestore!")

if __name__ == "__main__":
    fetch_and_sync_jobs()
