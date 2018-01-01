import unittest
import pickle

import oauth2client.client

import googleautoauth.auto_auth
import googleautoauth.test_support


class TestAuthorize(unittest.TestCase):
    def test_get_flow(self):
        with googleautoauth.test_support.get_test_authorize() as a:
            flow = a._get_flow()
            self.assertTrue(issubclass(flow.__class__, oauth2client.client.OAuth2WebServerFlow))

    def test_get_auth_url(self):
        with googleautoauth.test_support.get_test_authorize() as a:
            flow = a._get_flow()
            url = a.get_auth_url()

            expected_prefix = 'https://accounts.google.com/o/oauth2/auth?'
            self.assertTrue(url.startswith(expected_prefix))

    def test_update_token(self):
        with googleautoauth.test_support.get_test_authorize() as a:
            a._update_token('abc')

            with open('auth') as f:
                token = pickle.load(f)

            self.assertEquals(token, 'abc')

    def test__full_cycle(self):
        with googleautoauth.test_support.get_test_authorizer() as ta:
            aa = googleautoauth.auto_auth.AutoAuth(ta)
            aa.get_and_write_creds()

            # Get the inner `Authorize` object being managed by the authorizor.
            authorize = ta.authorize

            # We should get an error since the token has already been
            # authorized against the server.

            try:
                authorize.authorize(ta.token)
            except oauth2client.client.FlowExchangeError as e:
                if str(e) != "invalid_grantCode was already redeemed.":
                    raise
            else:
                raise Exception("Expected an error from using the token more than once.")

            # Read back the final authorization.
            self.assertTrue(issubclass(authorize.token.__class__, oauth2client.client.OAuth2Credentials))

            original_token = authorize.token.access_token

            # Should be ignored since we couldn't possibly have expired yet.
            authorize.check_for_renew()

            # The token shouldn't have changed because we haven't yet expired.
            self.assertEquals(authorize.token.access_token, original_token)

            client = authorize.get_client('youtube', 'v3')
            playlists = client.playlists()

            request = playlists.list(
                    mine=True,
                    part='contentDetails')

            result = request.execute()
            self.assertEquals(result['kind'], 'youtube#playlistListResponse')
