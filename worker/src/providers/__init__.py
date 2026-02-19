from providers.base import CloudProvider
from providers.gcp import GCPProvider


def get_provider(provider_name: str, credentials: dict) -> CloudProvider | None:
    """Return the right CloudProvider instance for a given provider name and credentials."""
    if provider_name == "gcp":
        return GCPProvider(credentials)
    return None
