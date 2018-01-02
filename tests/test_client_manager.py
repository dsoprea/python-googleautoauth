import unittest

import oauth2client.client

import googleautoauth.constants
import googleautoauth.test_support


class TestClientManager(unittest.TestCase):
    def test_get_client(self):
        with googleautoauth.test_support.temp_path() as path:
            with googleautoauth.test_support.environment(
                    GAA_GOOGLE_API_AUTHORIZATION_REPO_PATH=path):
                cm = googleautoauth.test_support.get_client_manager()
                self.assertEquals(cm.mode, googleautoauth.constants.CMM_INTERACTIVE)

                c = cm.get_client()

                p = c.playlists()

                request = p.list(
                        mine=True,
                        part='contentDetails')

                response = request.execute()
                self.assertEquals(response['kind'], 'youtube#playlistListResponse')

    def test_get_client__existing(self):
        with googleautoauth.test_support.temp_path() as path:
            with googleautoauth.test_support.environment(
                    GAA_GOOGLE_API_AUTHORIZATION_REPO_PATH=path):
                cm = googleautoauth.test_support.get_client_manager()
                self.assertEquals(cm.mode, googleautoauth.constants.CMM_INTERACTIVE)

                cm = googleautoauth.test_support.get_client_manager()
                self.assertEquals(cm.mode, googleautoauth.constants.CMM_EXISTING)

    def test_get_client__manual(self):
        with googleautoauth.test_support.temp_path() as path:
            with googleautoauth.test_support.environment(
                    GAA_GOOGLE_API_AUTHORIZATION_REPO_PATH=path):
                try:
                    cm = googleautoauth.test_support.get_client_manager(token_from_user='FAKE-TOKEN')
                except oauth2client.client.FlowExchangeError as e:
                    if str(e) != "invalid_grantMalformed code.":
                        raise
                else:
                    raise Exception("Expected error from manual authorization with a bad-code.")
