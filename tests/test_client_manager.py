import unittest

import googleautoauth.test_support


class TestClientManager(unittest.TestCase):
    def test_get_client(self):
        cm = googleautoauth.test_support.get_client_manager()
        c = cm.get_client()

        p = c.playlists()

        request = p.list(
                mine=True,
                part='contentDetails')

        response = request.execute()
        self.assertEquals(response['kind'], 'youtube#playlistListResponse')
