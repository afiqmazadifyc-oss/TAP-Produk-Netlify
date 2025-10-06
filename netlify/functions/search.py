import os
import json
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

URL_SHEET = os.environ.get('GOOGLE_SHEET_URL')

def get_credentials():
    creds_json_str = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if not creds_json_str:
        raise ValueError("Kredensial Google tidak ditemukan.")
    
    creds_info = json.loads(creds_json_str)
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']
    return Credentials.from_service_account_info(creds_info, scopes=SCOPES)

def handler(event, context):
    if event['httpMethod'] != 'POST':
        return {'statusCode': 405, 'body': 'Method Not Allowed'}

    try:
        body = json.loads(event.get('body', '{}'))
        keyword = body.get('keyword', '').strip().lower()

        if not keyword:
            return {'statusCode': 200, 'body': json.dumps([])}

        creds = get_credentials()
        client = gspread.authorize(creds)
        sheet = client.open_by_url(URL_SHEET).sheet1
        
        list_of_lists = sheet.get_all_values()
        headers = list_of_lists.pop(0) if list_of_lists else []
        data_cache = pd.DataFrame(list_of_lists, columns=headers)

        if 'Nama Produk' not in data_cache.columns:
            return {'statusCode': 500, 'body': json.dumps({'error': 'Kolom "Nama Produk" tidak ditemukan di Google Sheet.'})}

        search_terms = keyword.split()
        processed_names = data_cache['Nama Produk'].str.replace(r'[^a-zA-Z0-9]', '', regex=True).str.lower()
        
        final_mask = pd.Series([True] * len(data_cache), index=data_cache.index)
        for term in search_terms:
            condition = processed_names.str.contains(term.replace(' ', ''))
            final_mask = final_mask & condition
        
        hasil = data_cache[final_mask]
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': hasil.to_json(orient='records')
        }

    except Exception as e:
        print(f"Error: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}