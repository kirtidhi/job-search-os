from googleapiclient.discovery import build
import google.auth
from googleapiclient.http import MediaFileUpload
import os

try:
    credentials, project = google.auth.default()
    drive_service = build('drive', 'v3', credentials=credentials)
    sheets_service = build('sheets', 'v4', credentials=credentials)
    
    tracker_sheet_id = '1nKjjHbo_zqlRiNo1SymrLDOc28YkbE5Hvk4CdxvYFIA'

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
            'mimeType': 'application/vnd.google-apps.document' # This triggers conversion!
        }
        media = MediaFileUpload(filepath, mimetype=source_mimetype)
        file = drive_service.files().create(body=metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('webViewLink')

    # Job 1
    folder1_id = create_folder("Woolworths Group - Product Manager, Platform Capabilities - Docs")
    base1 = "output/WoolworthsGroup_Woolworths_20260626_080944"
    resume1 = upload_file_as_doc(f"{base1}/resume.html", folder1_id, 'text/html', 'Resume')
    cl1 = upload_file_as_doc(f"{base1}/cover_letter.md", folder1_id, 'text/markdown', 'Cover Letter')
    play1 = upload_file_as_doc(f"{base1}/playbook.md", folder1_id, 'text/markdown', 'Playbook')

    # Job 2
    folder2_id = create_folder("Woolworths Group - Senior Product Manager, Client Experience - Docs")
    base2 = "output/WoolworthsGroup_Woolworths_20260626_080945"
    resume2 = upload_file_as_doc(f"{base2}/resume.html", folder2_id, 'text/html', 'Resume')
    cl2 = upload_file_as_doc(f"{base2}/cover_letter.md", folder2_id, 'text/markdown', 'Cover Letter')
    play2 = upload_file_as_doc(f"{base2}/playbook.md", folder2_id, 'text/markdown', 'Playbook')

    result = sheets_service.spreadsheets().values().get(spreadsheetId=tracker_sheet_id, range="'Job Application Tracker'!A:H").execute()
    values = result.get('values', [])
    
    row1_idx = None
    row2_idx = None
    
    for i, row in enumerate(values):
        if len(row) >= 2 and row[0] == 'Woolworths Group' and 'Platform Capabilities' in row[1]:
            row1_idx = i + 1
        elif len(row) >= 2 and row[0] == 'Woolworths Group' and 'Client Experience' in row[1]:
            row2_idx = i + 1

    if row1_idx:
        body = {'values': [[resume1, cl1, play1]]}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=tracker_sheet_id, range=f"'Job Application Tracker'!F{row1_idx}:H{row1_idx}",
            valueInputOption="USER_ENTERED", body=body).execute()
            
    if row2_idx:
        body = {'values': [[resume2, cl2, play2]]}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=tracker_sheet_id, range=f"'Job Application Tracker'!F{row2_idx}:H{row2_idx}",
            valueInputOption="USER_ENTERED", body=body).execute()

    print("Successfully converted and uploaded files as Google Docs!")
except Exception as e:
    print(f"Error: {e}")
