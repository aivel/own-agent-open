from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from googleapiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

class GoogleDriveAPI:
    SCOPES = 'https://www.googleapis.com/auth/drive'
    CLIENT_SECRET_FILE = 'client_secret.json'
    APPLICATION_NAME = 'Drive API Python Quickstart'

    def __init__(self):
        credentials = GoogleDriveAPI.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.drive_service = discovery.build('drive', 'v3', http=http)

    @staticmethod
    def get_credentials():
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        try:
            import argparse
            flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            flags = None

        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'drive-python-quickstart.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(GoogleDriveAPI.CLIENT_SECRET_FILE, GoogleDriveAPI.SCOPES)
            flow.user_agent = GoogleDriveAPI.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else:  # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def list_files(self):
        results = self.drive_service.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        return items

    def get_file(self, file_id):
        fields = 'id, mimeType, webViewLink'
        file = self.drive_service.files().get(fileId=file_id, fields=fields).execute()

        return file

    def create_permission(self, file_id, email):

        result = self.drive_service.permissions().create(fileId=file_id, body={
            'role': 'writer',
            'type': 'user',
            'emailAddress': email
        }).execute()

        return result

    def list_revisions(self, file_id):

        result = self.drive_service.revisions().list(fileId=file_id).execute()

        return result

    def create_file(self, file_name):
        file_metadata = {
            'name': file_name,
            'mimeType': 'application/vnd.google-apps.document'
        }

        media = MediaFileUpload('test.docx',
                                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                resumable=True)

        file = self.drive_service.files().create(body=file_metadata,
                                                 media_body=media,
                                                 keepRevisionForever=True).execute()

        return file

