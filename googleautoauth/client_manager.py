import os
import logging
import contextlib

import httplib2

import googleautoauth.authorize
import googleautoauth.auto_auth

_LOGGER = logging.getLogger(__name__)

# TODO(dustin): We should still allow a manual flow, though the user can also just copy the token file if he already has one. Locked-down environments may not, though.


class ClientManager(object):
    """This class knows how to cache some of the connection semantics without
    sabotaging the authoriation renewal process.
    """

    def __init__(
            self, service_name, service_version, client_credentials,
            scopes, filepath=None):
        self.__service_name = service_name
        self.__service_version = service_version

        if filepath is None:
            filepath = \
                os.environ['GAA_GOOGLE_API_AUTHORIZATION_FILEPATH']

        self._initialize(filepath, client_credentials, scopes)

    def _initialize(self, filepath, cc, scopes):
        if os.path.exists(filepath) is True:
            _LOGGER.debug("Found existing authorization: [{}]".format(
                          filepath))

            self.__authorize = \
                googleautoauth.authorize.Authorize(
                    filepath,
                    cc,
                    scopes)
        else:
            _LOGGER.debug("No existing authorization found. Executing auto-"
                          "auth flow: [{}]".format(filepath))

            path = os.path.dirname(filepath)

            if os.path.exists(path) is False:
                os.makedirs(path)

            ab = googleautoauth.auto_auth.AuthorizerBridge(
                    filepath,
                    cc,
                    scopes)

            aa = googleautoauth.auto_auth.AutoAuth(ab)
            aa.get_and_write_creds()

            self.__authorize = ab.authorize

    def get_client(self):
        """This should be called any time the API needs to be accessed. It
        should not be cached.
        """

        c = self.__authorize.get_client(
                self.__service_name,
                self.__service_version)

        return c
