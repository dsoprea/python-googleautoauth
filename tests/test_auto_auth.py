import unittest

import oauth2client.client

import googleautoauth.auto_auth
import googleautoauth.test_support


class TestAutoAuth(unittest.TestCase):
    def test_get_and_write_creds(self):
        with googleautoauth.test_support.get_test_authorizer() as ta:
            aa = googleautoauth.auto_auth.AutoAuth(ta)
            aa.get_and_write_creds()

            self.assertTrue(len(ta.token) > 0)

            # The token should've already been authorized on the server side.
            try:
                ta.authorize.authorize(ta.token)
            except oauth2client.client.FlowExchangeError as e:
                if str(e) != "invalid_grantCode was already redeemed.":
                    raise
            else:
                raise Exception("Expected an error from using the token more than once.")
