from googleapiclient.discovery import build
import google.auth
# Let's try default credentials
try:
    credentials, project = google.auth.default()
    sheets_service = build('sheets', 'v4', credentials=credentials)
    
    tracker_sheet_id = '1nKjjHbo_zqlRiNo1SymrLDOc28YkbE5Hvk4CdxvYFIA'
    sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=tracker_sheet_id).execute()
    sheets = sheet_metadata.get('sheets', '')
    for sheet in sheets:
        print(sheet.get("properties", {}).get("title", ""))
except Exception as e:
    print(f"Error: {e}")
