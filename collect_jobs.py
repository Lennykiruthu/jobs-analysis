# Import necessary libraries
import requests      # For making HTTP requests to the Adzuna API
import json          # For working with JSON responses
import sqlite3       # For interacting with a SQLite database
import time          # To introduce delay between API requests (avoid rate-limiting)
from dotenv import load_dotenv
import os

# Keep prompting until a non-empty job keyword is entered
while True:
    search_query = input("Enter a job keyword (e.g. 'data analyst', 'machine learning'): ").strip()
    if search_query:
        break
    print('Job keyword cannot be empty. Please try again')

# Load variables from .env into the local environment
load_dotenv() 
 
# My Adzuna API credentials
APP_ID  = os.getenv('APP_ID')
APP_KEY = os.getenv('APP_KEY')

# List of locations to search for jobs from different countries
locations = [
    {'country' : 'gb', 'location' : 'London'},
    {'country' : 'us', 'location' : 'New York'},
    {'country' : 'us', 'location' : 'California'},        
]
pages   = 5

# List to store all fetched jobs from all locations
all_jobs      = []


print('Fetching jobs from Adzuna API.')

for loc in locations:
    print(f'\nFetching {search_query} jobs for location: {loc['country']}, {loc['location']}.')
    for page in range (1, pages + 1):
        print(f'\nFetching jobs on page: {page}.')
        # Construct the API endpoint URL dynamically based on the country and page
        url     = f"https://api.adzuna.com/v1/api/jobs/{loc['country']}/search/{page}"

        # Set up query parameters for the API request
        params  = {
            'app_id'           : APP_ID,
            'app_key'          : APP_KEY,
            'what'             : search_query,
            'where'            : loc['location'],
            'results_per_page' : 50
            }

        # Send a GET request to the Adzuna API
        response = requests.get(url, params=params)
        if response.status_code == 200:
            jobs = response.json().get('results', [])
            all_jobs.extend(jobs)
        else:
            print(f'Failed for {loc['location']} on page {page}')
        time.sleep(3)

print(f"Fetched total: {len(all_jobs)} jobs")    
print('Creating and inserting jobs into database.')

inserted_count = 0
skipped_count = 0

# Connect to SQLite database (or create it if it doesn't exist)
conn   = sqlite3.connect('adzuna_jobs.db')
cursor = conn.cursor()

# Create the jobs table if it doesn't already exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS jobs(
    id TEXT PRIMARY KEY,
    title TEXT,
    company TEXT,
    area_list TEXT,
    location TEXT,
    category TEXT,
    salary_max REAL,
    salary_min REAL,
    salary_is_predicted TEXT,
    latitude REAL,
    longitude REAL,
    contract_type TEXT,
    contract_time TEXT,
    description TEXT,
    created TEXT,
    redirect_url TEXT)
''')

# Loop over each job in the job list and insert into the database
for job in all_jobs:
    try:
        cursor.execute('''
        INSERT OR IGNORE INTO jobs(
        id, title, company, area_list, location, category, salary_max, salary_min, 
        salary_is_predicted, latitude, longitude, contract_type, contract_time, 
        description, created, redirect_url)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',(
            job.get('id'),
            job.get('title'),
            job.get('company', {}).get('display_name'), 
            json.dumps(job.get('location', {}).get('area')),
            job.get('location', {}).get('display_name'), 
            job.get('category', {}).get('label'), 
            job.get('salary_max'), 
            job.get('salary_min'), 
            job.get('salary_is_predicted'),
            job.get('latitude'), 
            job.get('longitude'), 
            job.get('contract_type'), 
            job.get('contract_time'), 
            job.get('description'), 
            job.get('created'), 
            job.get('redirect_url'),        
        ))

        # Checking to see how many rows were affected by the sql operation
        if cursor.rowcount == 1:
            inserted_count += 1
            print(f"Inserted job id: {job.get('id')}")
        else: 
            skipped_count += 1
            print(f"Skipped duplicate job id {job.get('id')}")

    except Exception as e:
        print(f"❌ Error inserting job ID: {job.get('id')}: {e}")
        skipped_count += 1

# Commit changes and close the connection to the database
conn.commit()
print(f"\n✅ Job insertion complete: {inserted_count} inserted, {skipped_count} skipped")

# Close sqlite connection and release resources
conn.close()

# Confirm that jobs have been saved
print("Jobs saved to SQLite DB.")    