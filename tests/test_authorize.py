import unittest

import oauth2client.client

import googleautoauth.test_support


class TestAuthorize(unittest.TestCase):
    def test_get_flow(self):
        with googleautoauth.test_support.get_test_authorizer() as a:
            flow = a._get_flow()
            self.assertTrue(issubclass(flow.__class__, oauth2client.client.OAuth2WebServerFlow))

    def test_get_auth_url(self):
        with googleautoauth.test_support.get_test_authorizer() as a:
            flow = a._get_flow()
            url = a.get_auth_url()

            expected_prefix = 'https://accounts.google.com/o/oauth2/auth?'
            self.assertTrue(url.startswith(expected_prefix))

    # def test__step2_exchange(self):
    #     a = ytad.authorize.Authorize()
    #     flow = a._get_flow()

    #     auth_code = '4/-f6rs-OpcY9Om-G7ZZ0HBznCOu4Aej-7F1_RllIdqqI'
    #     credentials = flow.step2_exchange(auth_code)

    #     self.assertTrue(issubclass(credentials.__class__, oauth2client.client.OAuth2Credentials))
