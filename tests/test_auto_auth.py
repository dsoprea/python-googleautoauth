import unittest

import googleautoauth.google_authorizer
import googleautoauth.auto_auth
import googleautoauth.test_support


class _TestAuthorizer(googleautoauth.google_authorizer.GoogleAuthorizer):
    def get_auth_url(self, redirect_uri):
        with googleautoauth.test_support.get_test_authorizer(redirect_uri=redirect_uri) as a:
            return a.get_auth_url()

    def do_authorize(self, auth_code):
        self.__auth_code = auth_code

    @property
    def auth_code(self):
        return self.__auth_code


class TestAutoAuth(unittest.TestCase):
    def test_get_and_write_creds(self):
        ta = _TestAuthorizer()
        aa = googleautoauth.auto_auth.AutoAuth(ta)
        aa.get_and_write_creds()

        self.assertTrue(len(ta.auth_code) > 0)
