import os
import logging
import pickle
import json
import datetime
import tempfile
import fcntl
import contextlib

logging.getLogger('oauth2client.client').setLevel(logging.ERROR)
import oauth2client.client

import httplib2

import googleautoauth.google_authorizer
import googleautoauth.client

_DEFAULT_RETRIES = 5

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

def get_flow(cc, scopes, redirect_uri):
    with tempfile.NamedTemporaryFile() as f:
        json.dump(cc, f)
        f.flush()

        flow = \
            oauth2client.client.flow_from_clientsecrets(
                f.name,
                scope=scopes,
                redirect_uri=redirect_uri)

        return flow


class Authorize(object):
    """Manages authorization process. This is general-purpose and not auto-
    auth-specific.
    """

    def __init__(
            self, authorization_filepath,
            client_credentials,
            scopes,

            # By default, tell Google that we want to see the token in the
            # webpage rather than redirecting anywhere else.
            redirect_uri=oauth2client.client.OOB_CALLBACK_URN):
        self.__lock_filepath = \
            os.path.join(tempfile.gettempdir(), '.google_api_auth_lock')

        self.__client_credentials = client_credentials
        self.__redirect_uri = redirect_uri
        self.__scopes = ' '.join(scopes)

        filepath = os.path.expanduser(authorization_filepath)

        path = os.path.dirname(authorization_filepath)
        if os.path.exists(path) is False:
            raise Exception("Storage path does not already exist: [{}]".format(
                            path))

        self.__filepath = authorization_filepath

    def _get_flow(self):
        try:
            return self.__flow
        except AttributeError:
            pass

        self.__flow = \
            get_flow(
                self.__client_credentials,
                self.__scopes,
                self.__redirect_uri)

        return self.__flow

    def get_auth_url(self):
        flow = self._get_flow()
        return flow.step1_get_authorize_url()

    def _update_token(self, token):
        """Write the credentials we get either from the initial authorization
        or a refresh.
        """

        self._token = token

        with open(self.__filepath, 'w') as f:
            pickle.dump(self._token, f)

    def _check_for_renew(self, token, do_force=False):
        """Call this at regular intervals to make sure our credentials don't
        need to be refreshed. It's very low-cost if nothing needs to be done.
        """

        with self._lock_auth_file():
            if do_force is False and \
               datetime.datetime.now() < token.token_expiry:
                return

            http = httplib2.Http()
            token.refresh(http)

            self._update_token(token)

    @contextlib.contextmanager
    def _lock_auth_file(self):
        # Allow for a recurrent file-lock. We're not multithreaded so there
        # should be any issues.

        try:
            self.__file_locked
        except AttributeError:
            pass
        else:
            yield
            return

        self.__file_locked = True

        try:
            if os.path.exists(self.__lock_filepath) is False:
                with open(self.__lock_filepath, 'w'):
                    pass

            with open(self.__lock_filepath, 'w') as f:
                fcntl.flock(f, fcntl.LOCK_EX)

                try:
                    yield
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
        finally:
            del self.__file_locked

    def _get_token(self, allow_renew=True):
        if getattr(self, '_token', None) is not None:
            # If we get here, a token *was* known.
            self._check_for_renew(self._token)
            return self._token

        # If we get here, a token *was not* already known.

        try:
            with open(self.__filepath) as f:
                self._token = pickle.load(f)
        except IOError:
            found = False
        else:
            found = True

        if found is False:
            raise Exception("Credentials not found. Please authorize first.")

        # `self.__client_credentials` will always exist by this point.
        if allow_renew is True:
            self._check_for_renew(self._token)

        return self._token

    def _robust(self, cb):
        n = _DEFAULT_RETRIES
        while n > 0:
            try:
                cb()
            except oauth2client.client.FlowExchangeError as e:
                if str(e) == 'invalid_grant':
                    n -= 1

                    if n == 0:
                        # We've run out of retries.
                        raise

                    continue

                # Any other exception.
                raise
            else:
                return

    def authorize(self, token):
        """Called with the code the user gets from Google."""

        flow = self._get_flow()

        def cb():
            updated_token = flow.step2_exchange(token)
            self._update_token(updated_token)

        self._robust(cb)

    def get_client(self, *args, **kwargs):
        """Produce the actual API client. THE CLIENT OBJECT SHOULD *NOT* BE
        CACHED. This will induce a check for whether our authorization has
        expired and automatically refresh if necessary.
        """

        http = httplib2.Http()
        self._get_token().authorize(http)

        return googleautoauth.client.get_client(http, *args, **kwargs)
