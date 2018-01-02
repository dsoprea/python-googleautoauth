Overview
========

The Google API OAuth authorization process is very complex when running from command-line applications:

1. Developer: Request a URL from the Google client-tools.
2. Developer: Present the URL to the user and have them open it in a browser.
3. User: Logs-in.
4. User: Acknowledge that the tool will be able to access user's data.
5. Google: Authorization portal provides a code/token.
6. User: Provides the code to the tool at the command-line.
7. Developer: Does a final authorization with Google using the token.

The tool must also periodically renew its authorization (whenever the expiration timestamp is reached).

This tool eliminates most of the steps:

1. Developer: Provide the developer's client-identity information.
2. Us: Create a temporary webserver on an available port.
3. Us: Build a URL that takes the local webserver as the redirect URI.
4. Us: Open the Google authentication portal in the default web browser.
5. User: Acknowledges the request in the browser.
6. Google: Authorize and redirect to the local, temporary webserver (passes the authorization token as an argument). Since Google does not need to talk directly to the webserver (the browser just redirects to a *localhost* URL), firewalls do not matter.
7. Us: The temporary webserver receives and records the token.
8. Us: The webserver is terminated and the authorization object records the token.

Notice that now only one step needs to be implemented by the developer and only one step needs to be performed by the user.

The interactive flow is only necessary before the authorization file is initially created. All further requests will be done in the background.


Implementation Requirements
===========================

- An interactive browser (e.g. Chrome, Lynx, etc..) is available and can be opened during install/setup. The user will have to manually close this when finished.
- An authorization token can be stored on the filesystem.


Usage
=====

Flow
----

Examples are for the YouTube API.

Build your client-identity::

    client_id = 'abc'
    client_secret = 'def'

    cc = googleautoauth.authorize.build_client_credentials(client_id, client_secret)

Create a `ClientManager` object::

    service_name = 'youtube'
    service_version = 'v3'

    scopes = [
        'https://www.googleapis.com/auth/youtube.readonly',
    ]

    # If this is `None` or omitted, the value will either be taken from `GAA_GOOGLE_API_AUTHORIZATION_FILEPATH` or default to '~/.googleautoauth/authorization'.
    filepath = None

    cm = googleautoauth.client_manager.ClientManager(
            service_name,
            service_version,
            cc,
            scopes,
            filepath=filepath)

Example usage:

    # This will open the Google authorization portal in the browser if the
    # authorization file doesn't already exist.
    client = cm.get_client()

    playlists = client.playlists()

    request = \
        playlists.list(
            mine=True,
            part='contentDetails')

    result = request.execute()
    # result['kind'] == 'youtube#playlistListResponse'

The `ClientManager` object can be cached but the client object returned by `cm.get_client()` can not. This call will automatically renew the API authorization as required.


Command-Line Tool
-----------------

A command-line tool (`gaa_authorize`) is provided to pre-create an authorization, for convenience. This can be used to ensure that no interactive authoriation is triggered from your program flow.

The tool can also be used to get a URL (-u) that can be used to manually get a token and to then manually register it locally (-t).

Example usage::

    $ gaa_authorize "service name" "service version" "(client ID)" "(client secret)" --scope "(scope 1)" --scope "(scope 2...)" -u
    https://accounts.google.com/o/oauth2/auth?scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fyoutube.readonly&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&response_type=code&client_id=872980721285-bk2f9bk1r1j6tmo5k9ndbia4ef6nmi80.apps.googleusercontent.com&access_type=offline

    $ gaa_authorize "service name" "service version" "(client ID)" "(client secret)" --scope "(scope 1)" --scope "(scope 2...)" -t 4/zXaFbTbevyn3zEizMiRdY0GVb3BM7XBUqbGdJhi8Fh8


Testing
=======

To run the tests::

    $ ./test.sh

The tests will require user interaction with the browser.
