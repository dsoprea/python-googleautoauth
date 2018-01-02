import sys
import os
import tempfile
import shutil
import contextlib
import io

import googleautoauth.authorize
import googleautoauth.client_manager

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

def get_client_manager(*args, **kwargs):
    """Return a CM instance. This requires
    GAA_GOOGLE_API_AUTHORIZATION_FILEPATH to be defined.
    """

    credentials = get_test_client_credentials()

    scopes = [
        'https://www.googleapis.com/auth/youtube.readonly',
    ]

    cm = googleautoauth.client_manager.ClientManager(
            'youtube',
            'v3',
            credentials,
            scopes,
            *args,
            **kwargs)

    return cm

@contextlib.contextmanager
def capture_output(streams_cb=None):
    stdout = sys.stdout
    stderr = sys.stderr

    if streams_cb is not None:
        streams_cb(stdout, stderr)

    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    try:
        yield
    finally:
        sys.stdout = stdout
        sys.stderr = stderr

@contextlib.contextmanager
def environment(**kwargs):
    original = os.environ.copy()

    for k, v in kwargs.items():
        if v is None:
            try:
                del os.environ[k]
            except KeyError:
                pass
        else:
            os.environ[k] = v

    yield

    for k, v in kwargs.items():
        if v is None:
            continue

        del os.environ[k]

    for k, v in original.items():
        os.environ[k] = v
