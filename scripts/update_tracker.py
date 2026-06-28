from googleapiclient.discovery import build
import google.auth
# Let's try default credentials
try:
    credentials, project = google.auth.default()
    sheets_service = build('sheets', 'v4', credentials=credentials)
    
    import os; from dotenv import load_dotenv; load_dotenv(); tracker_sheet_id = os.getenv('TRACKER_SHEET_ID')
    values = [
        ['Woolworths Group', 'Product Manager, Platform Capabilities', 'https://careers.woolworthsgroup.com.au/en_GB/apply/JobDetail/92248?source=LinkedIn', '2026-06-26', '0.9', 'output/WoolworthsGroup_Woolworths_20260626_080944/resume.html', 'output/WoolworthsGroup_Woolworths_20260626_080944/cover_letter.md', 'output/WoolworthsGroup_Woolworths_20260626_080944/playbook.md'],
        ['Woolworths Group', 'Senior Product Manager, Client Experience', 'https://careers.woolworthsgroup.com.au/en_GB/apply/JobDetail/92524?source=LinkedIn', '2026-06-26', '0.95', 'output/WoolworthsGroup_Woolworths_20260626_080945/resume.html', 'output/WoolworthsGroup_Woolworths_20260626_080945/cover_letter.md', 'output/WoolworthsGroup_Woolworths_20260626_080945/playbook.md']
    ]
    body = {'values': values}
    result = sheets_service.spreadsheets().values().append(
        spreadsheetId=tracker_sheet_id,
        range="'Job Application Tracker'!A:H",
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    print("Successfully updated the tracker sheet!")
except Exception as e:
    print(f"Error: {e}")
