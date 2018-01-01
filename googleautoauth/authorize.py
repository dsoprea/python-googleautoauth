import os
import logging
import pickle
import json
import datetime
import tempfile

import oauth2client.client

import httplib2

import googleautoauth.google_authorizer

_LOGGER = logging.getLogger(__name__)


def build_client_credentials(client_id, client_secret):
    """Our identity with Google."""

    client_credentials = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": [],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://accounts.google.com/o/oauth2/token"
        }
    }

    return client_credentials


class Authorize(object):
    """Manages authorization process. This is general-purpose and not auto-
    auth-specific.
    """

    def __init__(
            self, storage_filepath,
            client_credentials,
            scopes,

            # By default, tell Google that we want to see the token in the
            # webpage rather than redirecting anywhere else.
            redirect_uri=oauth2client.client.OOB_CALLBACK_URN):
        self.__client_credentials = client_credentials
        self.__redirect_uri = redirect_uri
        self.__scopes = ' '.join(scopes)

        filepath = os.path.expanduser(storage_filepath)

        path = os.path.dirname(storage_filepath)
        if os.path.exists(path) is False:
            raise Exception("Storage path does not already exist: [{}]".format(
                            path))

        self.__filepath = storage_filepath

    def _get_flow(self):
        try:
            return self.__flow
        except AttributeError:
            pass

        with tempfile.NamedTemporaryFile() as f:
            json.dump(self.__client_credentials, f)
            f.flush()

            self.__flow = \
                oauth2client.client.flow_from_clientsecrets(
                    f.name,
                    scope=self.__scopes,
                    redirect_uri=self.__redirect_uri)

        return self.__flow

    def get_auth_url(self):
        flow = self._get_flow()
        return flow.step1_get_authorize_url()

    def _update_token(self, token):
        """Write the credentials we get either from the initial authorization
        or a refresh.
        """

        self.__token = token

        with open(self.__filepath, 'w') as f:
            pickle.dump(self.__token, f)

    def check_for_renew(self, do_force=False):
        """Call this at regular intervals to make sure our credentials don't
        need to be refreshed. It's very low-cost if nothing needs to be done.
        """

        if do_force is False and datetime.datetime.now() < self.token.token_expiry:
            return

        http = httplib2.Http()
        self.token.refresh(http)

        self._update_token(self.token)

    @property
    def token(self):
        try:
            return self.__token
        except AttributeError:
            pass

        try:
            with open(self.__filepath) as f:
                self.__token = pickle.load(f)
        except IOError:
            found = False
        else:
            found = True

        if found is False:
            raise Exception("Credentials not found. Please authorize first.")

        # `self.__client_credentials` will always exist by this point.
        self.check_for_renew()

        return self.__token

    def authorize(self, token):
        """Called with the code the user gets from Google."""

        flow = self._get_flow()

        updated_token = flow.step2_exchange(token)
        self._update_token(updated_token)
