import logging
import threading
import webbrowser
import time
import urlparse
import io

import SocketServer
import BaseHTTPServer

import googleautoauth.google_authorizer
import googleautoauth.authorize

_LOGGER = logging.getLogger(__name__)


class _HTTPRequest(BaseHTTPServer.BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = io.StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()


class _WebserverMonitor(object):
    def __init__(self):
        # Allows us to be in sync when starting and stopping the thread.
        self.__server_state_e = threading.Event()

        self.__t = threading.Thread(target=self.__thread)
        self._port = None

        # Signaled when the authorization response is received.
        self._request_state_e = threading.Event()

        # Will be assigned with the response from Google.
        self._http_status_raw = None

    def start(self):
        self.__t.start()

        # Wait for the loop to change the event state.
        _LOGGER.debug("Waiting for thread to start.")
        self.__server_state_e.wait()

        _LOGGER.debug("Server is now running.")

        self.__server_state_e.clear()

    def stop(self):
        assert \
            self.__server_state_e is not None, \
            "Thread doesn't appear to have ever been started."

        assert \
            self.__t.is_alive() is True, \
            "Thread doesn't appear to be running."

        self.__server_state_e.clear()
        self.__s.shutdown()

        # Wait for the loop to change the event state.
        _LOGGER.debug("Waiting for thread to stop.")
        self.__server_state_e.wait()

        _LOGGER.debug("Server is no longer running.")

        self.__server_state_e.clear()

    def __thread(self):
        """Where the main loop lives."""

        _LOGGER.debug("Webserver is starting.")

        monitor = self

        # Embedding this because it's so trivial.
        class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
            def do_GET(self):

                # We have the first line of the response with the authorization code
                # passed as a query argument.
                #
                # Example:
                #
                # GET /?code=4/clwm0rESq8sqeC-JxIcfiSdjh2593hLej9CZxAcbe1A HTTP/1.1
                #

                try:
                    unicode
                except NameError:
                    request = self.requestline + "\n\n"
                else:
                    request = unicode(self.requestline + "\n\n")

                # Use Python to parse the request. We need to add one newline for the
                # line and another for a subsequent blank line to terminate the block
                # and conform with the RFC.
                hr = _HTTPRequest(request)
                u = urlparse.urlparse(hr.path)
                arguments = urlparse.parse_qs(u.query)

                # It's not an authorization response. Bail with the same error
                # the library would normally send for unhandled requests.
                if 'code' not in arguments:
                    self.send_error(
                        501,
                        "Unsupported method ({}): {}".format(
                        self.command, hr.path))

                    return

                token = arguments['code'][0]
                _LOGGER.debug("Received auth-code [{}]".format(token))

                monitor._token = token

                monitor._request_state_e.set()

                self.send_response(200, message='OK')

                self.send_header("Content-type", 'text/html')
                self.end_headers()

                self.wfile.write("""\
<html>
<head></head>
<body>
Authorization recorded.
</body>
</html>
""")

            def log_message(self, format, *args):
                pass


        class Server(SocketServer.TCPServer):
            def server_activate(self, *args, **kwargs):
                r = SocketServer.TCPServer.server_activate(self, *args, **kwargs)

                # Sniff the port, now that we're running.
                monitor._port = self.server_address[1]

                return r

        # Our little webserver. (0) for the port will automatically assign it
        # to some unused port.
        binding = ('localhost', 0)
        self.__s = Server(binding, Handler)

        _LOGGER.debug("Created server.")

        # Signal the startup routine that we're starting.
        self.__server_state_e.set()

        _LOGGER.debug("Running server.")
        self.__s.serve_forever()

        _LOGGER.debug("Webserver is stopping.")

        # Signal the startup routine that we're stopping.
        self.__server_state_e.set()

    @property
    def port(self):
        assert \
            self._port is not None, \
            "Thread hasn't been started or a port hasn't been assigned."

        return self._port

    @property
    def request_state_e(self):
        return self._request_state_e

    @property
    def token(self):
        return self._token


class AutoAuth(object):
    """Knows how to open the browser, authorize the application (prompting the
    user if necessary), redirect, receive the response, and store the
    credentials.
    """

    def __init__(self, google_authorizer):
        assert \
            issubclass(
                google_authorizer.__class__,
                googleautoauth.google_authorizer.GoogleAuthorizer) is True, \
            "google_authorizer must be a GoogleAuthorizer: [{}]".format(
            google_authorizer)

        self.__ga = google_authorizer

    def get_and_write_creds(self):
        _LOGGER.debug("Requesting authorization.")

        wm = _WebserverMonitor()

        # Start the webserver.
        wm.start()

        # Open a browser window to request authorization.

        redirect_uri = 'http://localhost:{}'.format(wm.port)

        url = self.__ga.get_auth_url(redirect_uri)
        _LOGGER.debug("Opening browser: [{}]".format(url))

        webbrowser.open(url)

        # Wait for the response from Google. We implement this as a loop rather
        # than a blocking call so that the user can terminate this with a
        # simple break (in contract, blocking on an event makes us
        # unresponsive).

        try:
            while 1:
                if wm.request_state_e.is_set() is True:
                    break

                time.sleep(1)
        except:
            raise
        else:
            token = wm.token
        finally:
            # Shutdown the webserver.
            wm.stop()

        # Finish the authorization from our side and record.
        self.__ga.do_authorize(token)

        _LOGGER.debug("Authorization complete.")


class AuthorizerBridge(googleautoauth.google_authorizer.GoogleAuthorizer):
    """A bridging object that adapts the auto-auth flow to the traditional
    `Authorize` process since an `Authorize` object can also be used just to
    support a traditional authorization flow without involving an automatic-
    authorization.
    """

    def __init__(self, storage_filepath, client_credentials, scopes):
        self.__storage_filepath = storage_filepath
        self.__client_credentials = client_credentials
        self.__scopes = scopes

    def get_auth_url(self, redirect_uri):
        self.__a = \
            googleautoauth.authorize.Authorize(
                self.__storage_filepath,
                self.__client_credentials,
                self.__scopes,
                redirect_uri=redirect_uri)

        return self.__a.get_auth_url()

    def do_authorize(self, token):
        self.__a.authorize(token)
        self.__token = token

    @property
    def token(self):
        """The raw string token returned from Google. This is different from
        the underlying token object in the Authorize object.
        """

        return self.__token

    @property
    def authorize(self):
        """The underlying `Authorize` object."""

        return self.__a
