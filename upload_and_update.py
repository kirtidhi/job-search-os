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

    def upload_file(filepath, folder_id, mimetype):
        name = os.path.basename(filepath)
        metadata = {'name': name, 'parents': [folder_id]}
        media = MediaFileUpload(filepath, mimetype=mimetype)
        file = drive_service.files().create(body=metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('webViewLink')

    # Job 1
    folder1_id = create_folder("Woolworths Group - Product Manager, Platform Capabilities - 2026-06-26")
    base1 = "output/WoolworthsGroup_Woolworths_20260626_080944"
    resume1 = upload_file(f"{base1}/resume.html", folder1_id, 'text/html')
    cl1 = upload_file(f"{base1}/cover_letter.md", folder1_id, 'text/markdown')
    play1 = upload_file(f"{base1}/playbook.md", folder1_id, 'text/markdown')

    # Job 2
    folder2_id = create_folder("Woolworths Group - Senior Product Manager, Client Experience - 2026-06-26")
    base2 = "output/WoolworthsGroup_Woolworths_20260626_080945"
    resume2 = upload_file(f"{base2}/resume.html", folder2_id, 'text/html')
    cl2 = upload_file(f"{base2}/cover_letter.md", folder2_id, 'text/markdown')
    play2 = upload_file(f"{base2}/playbook.md", folder2_id, 'text/markdown')

    # Now update the last 2 rows in the sheet. Let's just append new rows and clear old or just overwrite.
    # To overwrite, we need to know the row index. Or just append the new corrected ones.
    # Let's read the sheet to find the rows.
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

    print("Successfully uploaded to Drive and updated the tracker sheet links!")
except Exception as e:
    print(f"Error: {e}")
