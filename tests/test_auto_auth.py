import unittest

import googleautoauth.auto_auth
import googleautoauth.test_support


class TestAutoAuth(unittest.TestCase):
    def test_get_and_write_creds(self):
        with googleautoauth.test_support.get_test_authorizer() as ta:
            aa = googleautoauth.auto_auth.AutoAuth(ta)
            aa.get_and_write_creds()

            self.assertTrue(len(ta.token) > 0)
