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

1. Developer: Provide an authorization object containing the developer's identity information.
2. Us: Create a temporary webserver on an available port.
3. Us: Build a URL that takes the local webserver as the redirect URI.
4. Us: Open the Google authentication portal in the default web browser.
5. User: Acknowledges the authorization in the browser.
6. Google: Authorize and redirect to the local, temporary webserver (passes the authorization token as an argument). Since Google does not need to talk directly to the webserver (the browser just redirects to a *localhost* URL), firewalls do not matter.
7. Us: The temporary webserver receives and records the token.
8. Us: The webserver is terminated and the authorization object records the token.

Notice that now only one step needs to be implemented by the developer and only one step needs to be performed by the user.


Implementation Requirements
===========================

- An interactive browser (e.g. Chrome, Lynx, etc..) is available and can be opened during install/setup. The user will have to manually close this when finished.
- An authorization token can be stored on the filesystem.


Usage
=====

Build your client-identity::

    client_id = 'abc'
    client_secret = 'def'

    cc = googleautoauth.authorize.build_client_credentials(client_id, client_secret)

Create a `GoogleAuthorizer` object (`AuthorizerBridge` fulfills this)::

    storage_filepath = '~/.token'
    scopes = [
        '...',
    ]

    ab = googleautoauth.auto_auth.AuthorizerBridge(storage_filepath, cc, scopes)

Create an `AutoAuth` object::

    aa = googleautoauth.auto_auth.AutoAuth(ab)

Run the automatic process detailed above::

    aa.get_and_write_creds()

Make an API client:

    # Get a YouTube API client.
    client = ab.authorize.get_client('youtube', 'v3')

Example usage:

    playlists = client.playlists()

    request = playlists.list(
            mine=True,
            part='contentDetails')

    result = request.execute()
    # result['kind'] == '(kind of entity)'

To check the token and renew if necessary::

    ab.authorize.check_for_renew()


*check_for_renew* Notes
~~~~~~~~~~~~~~~~~~~~~~~

- This call has a trivial cost if the token does not need to be renewed.
- This call is implicitly made on every invocation of `get_client()` (above). **Do not cache the client** unless you are prepared to regularly call `check_for_renew()` yourself.


Resume Session
--------------

When you want to resume the same authorization session later (which should work indefinitely since the process implicitly renews the authorization token periodically), you may directly use the `Authorize` class (instead of `AutoAuth`)::

    authorize = googleautoauth.authorize.Authorize(storage_filepath, client_credentials, scopes)
    client = authorize.get_client('youtube', 'v3')


Testing
=======

To run the tests (requires user interaction with the browser)::

    $ ./test.sh
