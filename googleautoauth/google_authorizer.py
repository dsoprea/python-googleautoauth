class GoogleAuthorizer(object):
    def get_auth_url(self, redirect_uri):
        raise NotImplementedError()

    def do_authorize(self, token):
        raise NotImplementedError()
