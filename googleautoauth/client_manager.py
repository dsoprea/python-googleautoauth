import os
import logging
import contextlib
import json
import hashlib

import httplib2

import googleautoauth.constants
import googleautoauth.config.client_manager
import googleautoauth.authorize
import googleautoauth.auto_auth

_LOGGER = logging.getLogger(__name__)


class ClientManager(object):
    """This class knows how to cache some of the connection semantics without
    sabotaging the authoriation renewal process.
    """

    def __init__(
            self, service_name, service_version, client_credentials,
            scopes, filepath=None, token_from_user=None, webserver_port=0):
        self.__service_name = service_name
        self.__service_version = service_version

        self.__webserver_port = \
            int(os.environ.get('GAA_WEBSERVER_PORT', str(webserver_port)))

        if filepath is None:
            path = \
                os.environ.get(
                    'GAA_GOOGLE_API_AUTHORIZATION_REPO_PATH',
                    googleautoauth.config.client_manager.DEFAULT_PATH)

            # Create a hash based on our unique profile in order to prevent
            # collisions with other integrations on the system.

            payload = {
                'service_name': service_name,
                'service_version': service_version,
                'client_credentials': client_credentials,
                'scopes': scopes,
            }

            encoded = json.dumps(payload)
            hash_ = hashlib.sha1(encoded).hexdigest()

            filename = '{}_{}_{}'.format(service_name, service_version, hash_)
            filepath = os.path.join(path, filename)

        filepath = os.path.expanduser(filepath)
        self._initialize(
            filepath,
            client_credentials,
            scopes,
            token_from_user=token_from_user)

    def _initialize(self, filepath, cc, scopes, token_from_user=None):
        authorize = None

        if token_from_user is not None:
            _LOGGER.debug("We were given a manual authorization: [{}]".format(
                          filepath))

            authorize = \
                googleautoauth.authorize.Authorize(
                    filepath,
                    cc,
                    scopes)

            authorize.authorize(token_from_user)

            self._mode = googleautoauth.constants.CMM_MANUAL

        if os.path.exists(filepath) is True:
            _LOGGER.debug("Found existing authorization: [{}]".format(
                          filepath))

            if authorize is None:
                authorize = \
                    googleautoauth.authorize.Authorize(
                        filepath,
                        cc,
                        scopes)

                self._mode = googleautoauth.constants.CMM_EXISTING

            self.__authorize = authorize
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
            aa.get_and_write_creds(webserver_port=self.__webserver_port)

            self.__authorize = ab.authorize
            self._mode = googleautoauth.constants.CMM_INTERACTIVE

        assert \
            getattr(self, '_mode', None) is not None, \
            "Mode not correctly set."

    def get_client(self):
        """This should be called any time the API needs to be accessed. It
        should not be cached.
        """

        c = self.__authorize.get_client(
                self.__service_name,
                self.__service_version)

        return c

    @property
    def mode(self):
        return self._mode
