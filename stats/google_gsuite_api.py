from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from googleapiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


class GoogleGsuiteAPI:
    SCOPES = 'https://www.googleapis.com/auth/activity https://www.googleapis.com/auth/drive.metadata.readonly'
    CLIENT_SECRET_FILE = 'client_secret_gsuite.json'
    APPLICATION_NAME = 'G suite activity API Python Quickstart'

    def __init__(self):
        credentials = GoogleGsuiteAPI.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.activity_service = discovery.build('appsactivity', 'v1', http=http)

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
                                       'appsactivity-python-quickstart.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(GoogleGsuiteAPI.CLIENT_SECRET_FILE, GoogleGsuiteAPI.SCOPES)
            flow.user_agent = GoogleGsuiteAPI.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else:  # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def get_activities(self, file_id):

        result = self.activity_service.activities().list(source='drive.google.com',
                                                         groupingStrategy='none',
                                                         drive_fileId=file_id).execute()

        activities = result.get('activities', [])
        next_page_token = result.get('nextPageToken')

        while next_page_token != '' and next_page_token is not None:
            additional_result = self.activity_service.activities().list(source='drive.google.com',
                                                                        groupingStrategy='none',
                                                                        drive_fileId=file_id,
                                                                        pageToken=next_page_token).execute()

            additional_activities = additional_result.get('activities', [])
            next_page_token = additional_result.get('nextPageToken')

            for activity in additional_activities:
                activities.push(activity)

        return activities
