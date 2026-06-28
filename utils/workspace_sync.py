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
            creds = None
            scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
                    if not os.path.exists(creds_path):
                        raise FileNotFoundError(f"Credentials file not found at {creds_path}. Please download it from Google Cloud Console.")
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, scopes)
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
        
        # Remove the original extension from the document name
        name = os.path.basename(filepath)
        name_without_ext = os.path.splitext(name)[0]
        
        metadata = {
            'name': name_without_ext, 
            'parents': [folder_id],
            'mimeType': 'application/vnd.google-apps.document'
        }
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
            strategy_link = self._upload_file(strategy_doc_path, folder_id, 'text/plain')
            cl_link = self._upload_file(cover_letter_path, folder_id, 'text/plain') if cover_letter_path else ""
            
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
                    range="'Job Application Tracker'!A:H",
                    valueInputOption="USER_ENTERED",
                    body=body
                ).execute()
                logger.info(f"Appended row to Tracker Sheet {self.tracker_sheet_id}")
            
            logger.info("Successfully synced to Google Workspace.")
            return True
        except Exception as e:
            logger.error(f"Error syncing to Workspace: {e}")
            return False
