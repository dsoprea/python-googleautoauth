import apiclient.discovery

def get_client(http, service_name, service_version):
    """Create an API client instance."""

    client = \
        apiclient.discovery.build(
            service_name,
            service_version,
            http=http,
            discoveryServiceUrl=apiclient.discovery.DISCOVERY_URI)

    return client
