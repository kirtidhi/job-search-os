from googleapiclient.discovery import build
import google.auth
from googleapiclient.http import MediaFileUpload
from datetime import datetime

try:
    credentials, project = google.auth.default()
    drive_service = build('drive', 'v3', credentials=credentials)
    sheets_service = build('sheets', 'v4', credentials=credentials)
    
    import os; from dotenv import load_dotenv; load_dotenv(); tracker_sheet_id = os.getenv('TRACKER_SHEET_ID')

    def create_folder(name):
        folder_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')

    def upload_file_as_doc(filepath, folder_id, source_mimetype, doc_name):
        metadata = {
            'name': doc_name, 
            'parents': [folder_id],
            'mimeType': 'application/vnd.google-apps.document'
        }
        media = MediaFileUpload(filepath, mimetype=source_mimetype)
        file = drive_service.files().create(body=metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('webViewLink')

    folder_id = create_folder("Adobe - Senior Product Manager, Adobe GenStudio - Docs")
    base = "output/Adobe_AdobeGenStudio_AdTrafficking_20260626"
    resume = upload_file_as_doc(f"{base}/resume.html", folder_id, 'text/html', 'Resume')
    cl = upload_file_as_doc(f"{base}/cover_letter.md", folder_id, 'text/markdown', 'Cover Letter')
    play = upload_file_as_doc(f"{base}/playbook.md", folder_id, 'text/markdown', 'Playbook')

    # Append to the tracker sheet
    new_row = [
        "Adobe",
        "Senior Product Manager, Adobe GenStudio (Ad Trafficking and Activation)",
        "https://careers.adobe.com/us/en/job/R162016/Senior-Product-Manager-Adobe-GenStudio-Ad-Trafficking-and-Activation",
        "Ready to Apply",
        datetime.now().strftime("%Y-%m-%d"),
        resume,
        cl,
        play
    ]
    
    body = {
        'values': [new_row]
    }
    
    sheets_service.spreadsheets().values().append(
        spreadsheetId=tracker_sheet_id, 
        range="'Job Application Tracker'!A:H",
        valueInputOption="USER_ENTERED", 
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()

    print("Successfully converted and uploaded files for Adobe as Google Docs, and appended to the Tracker!")
except Exception as e:
    print(f"Error: {e}")
