import os
import logging
import pickle
import json
import datetime
import tempfile

import oauth2client.client

import httplib2

_LOGGER = logging.getLogger(__name__)


class Authorize(object):
    """Manages authorization process."""

    def __init__(
            self, storage_filepath,
            client_credentials,
            scopes,
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

    def _update_cache(self, credentials):
        """Write the credentials we get either from the initial authorization
        or a refresh.
        """

        with open(self.__filepath, 'w') as f:
            pickle.dump(credentials, f)

    def check_for_renew(self, credentials=None):
        """Call this at regular intervals to make sure our credentials don't
        need to be refreshed. It's very low-cost if nothing needs to be done.
        """

        if credentials is None:
            credentials = self.credentials

        if datetime.datetime.now() < credentials.token_expiry:
            return

        http = httplib2.Http()
        credentials.refresh(http)

        self._update_cache(credentials)

    @property
    def credentials(self):
        try:
            return self.__credentials
        except AttributeError:
            pass

        try:
            with open(self.__filepath) as f:
                self.__credentials = pickle.load(f)
        except IOError:
            found = False
        else:
            found = True

        if found is False:
            raise Exception("Credentials not found. Please authorize first.")

        self.check_for_renew()
        return self.__credentials

    def authorize(self, auth_code):
        """Called with the code the user gets from Google."""

        flow = self._get_flow()

        credentials = flow.step2_exchange(auth_code)
        self._update_cache(credentials)
