import logging
import os
import pickle
from datetime import datetime
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

class WorkspaceManager:
    def __init__(self, tracker_sheet_id):
        self.tracker_sheet_id = tracker_sheet_id
        try:
            scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
            creds = None
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes)
                    creds = flow.run_local_server(port=0)
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)

            self.drive_service = build('drive', 'v3', credentials=creds)
            self.sheets_service = build('sheets', 'v4', credentials=creds)
        except Exception as e:
            logger.error(f"Failed to initialize Google API: {e}")
            self.drive_service = None
            self.sheets_service = None

    def _create_folder(self, name):
        folder_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = self.drive_service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')

    def _upload_file(self, filepath, folder_id, mimetype):
        if not os.path.exists(filepath):
            logger.warning(f"File not found for upload, skipping: {filepath}")
            return ""
        name = os.path.basename(filepath)
        metadata = {'name': name, 'parents': [folder_id]}
        media = MediaFileUpload(filepath, mimetype=mimetype)
        file = self.drive_service.files().create(body=metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('webViewLink')

    def sync(self, job, tailored_resume_path, strategy_doc_path, cover_letter_path=None, fit_data=None):
        if not self.drive_service:
            logger.warning("Workspace sync skipped - no Google credentials.")
            return False
            
        logger.info(f"Syncing assets for {job.get('title')} to Google Workspace...")
        try:
            # 1. Create Folder
            folder_name = f"{job['company']} - {job['title']} - {datetime.now().strftime('%Y-%m-%d')}"
            folder_id = self._create_folder(folder_name)
            
            # 2. Upload files
            resume_link = self._upload_file(tailored_resume_path, folder_id, 'text/html')
            strategy_link = self._upload_file(strategy_doc_path, folder_id, 'text/markdown')
            cl_link = self._upload_file(cover_letter_path, folder_id, 'text/markdown') if cover_letter_path else ""
            
            # 3. Append to tracker sheet
            if self.tracker_sheet_id and self.tracker_sheet_id != "YOUR_GOOGLE_SHEET_ID":
                values = [[
                    job['company'], 
                    job['title'], 
                    job.get('url', ''),
                    datetime.now().strftime('%Y-%m-%d'),
                    fit_data['score'] if fit_data else '',
                    resume_link,
                    cl_link,
                    strategy_link
                ]]
                body = {'values': values}
                self.sheets_service.spreadsheets().values().append(
                    spreadsheetId=self.tracker_sheet_id,
                    range="Sheet1!A:H",
                    valueInputOption="USER_ENTERED",
                    body=body
                ).execute()
                logger.info(f"Appended row to Tracker Sheet {self.tracker_sheet_id}")
            
            logger.info("Successfully synced to Google Workspace.")
            return True
        except Exception as e:
            logger.error(f"Error syncing to Workspace: {e}")
            return False
