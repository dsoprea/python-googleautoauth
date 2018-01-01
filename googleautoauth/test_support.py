import os
import tempfile
import shutil
import contextlib

import googleautoauth.authorize

@contextlib.contextmanager
def temp_path():
    original_wd = os.getcwd()
    path = tempfile.mkdtemp()

    os.chdir(path)

    try:
        yield path
    finally:
        os.chdir(original_wd)

        if os.path.exists(path) is True:
            shutil.rmtree(path)

def get_test_client_credentials():
    credentials = \
        googleautoauth.authorize.build_client_credentials(
            client_id="872980721285-bk2f9bk1r1j6tmo5k9ndbia4ef6nmi80.apps.googleusercontent.com",
            client_secret="5VKjPZHDC8TWjfItcJfPqK48")

    return credentials

@contextlib.contextmanager
def get_test_authorize(**kwargs):
    with temp_path() as path:
        storage_filepath = os.path.join(path, 'auth')
        credentials = get_test_client_credentials()

        scopes = [
            'https://www.googleapis.com/auth/youtube.readonly',
        ]

        a = googleautoauth.authorize.Authorize(
                storage_filepath,
                credentials,
                scopes,
                **kwargs)

        yield a

@contextlib.contextmanager
def get_test_authorizer():
    with temp_path() as path:
        storage_filepath = os.path.join(path, 'auth')
        credentials = get_test_client_credentials()

        scopes = [
            'https://www.googleapis.com/auth/youtube.readonly',
        ]

        a = googleautoauth.auto_auth.AuthorizerBridge(
                storage_filepath,
                credentials,
                scopes)

        yield a
