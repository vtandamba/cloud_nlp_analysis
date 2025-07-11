from flask import *
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2 import credentials as google_credentials
import requests

SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
API_SERVICE_NAME = 'searchconsole'
API_VERSION = 'v1'

def fetch_days_with_clicks(site_url, article_url, credentials):
    start_date = datetime(2024, 1, 1).strftime('%Y-%m-%d')
    end_date = datetime(2024, 12, 31).strftime('%Y-%m-%d')
    request = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['date', 'page'],
        'dimensionFilterGroups': [{'filters': [{'dimension': 'page', 'expression': article_url}]}],
        'rowLimit': 25000,
        'type': 'discover'
    }

    api_url = f'https://www.googleapis.com/webmasters/v3/sites/{site_url}/searchAnalytics/query'
    headers = {'Authorization': f'Bearer {credentials.token}'}
    response = requests.post(api_url, headers=headers, json=request)
    if response.status_code != 200:
        current_app.logger.error(f"Error retrieving data for site {site_url}: {response.status_code}")
        return 0, []

    response_data = response.json()
    days_with_clicks = sum(1 for row in response_data.get('rows', []) if row['clicks'] > 0)
    dates_with_clicks = [row['keys'][0] for row in response_data.get('rows', []) if row['clicks'] > 0]
    return days_with_clicks, dates_with_clicks

def calculate_days_with_clicks(sites, article_url, credentials):
    results = [fetch_days_with_clicks(site, article_url, credentials) for site in sites]
    all_dates = [date for _, dates in results for date in dates]
    if not all_dates:
        return 0, []
    date_objects = [datetime.strptime(date, '%Y-%m-%d').date() if isinstance(date, str) else date for date in all_dates]
    min_date = min(date_objects)
    max_date = max(date_objects)

    lifespan_days = (max_date - min_date).days + 1
    formatted_dates = [date.strftime('%d-%m-%Y') for date in date_objects]
    return lifespan_days, formatted_dates

def get_user_sites():
    if 'credentials' not in session:
        return None
    credentials = google_credentials.Credentials(**session['credentials'])
    service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    response = service.sites().list().execute()
    sites = [site['siteUrl'] for site in response.get('siteEntry', [])]
    return sites

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }