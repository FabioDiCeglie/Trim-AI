from providers.base import CloudProvider


class GCPProvider(CloudProvider):
    """
    Google Cloud provider — implements the four core data-fetching methods.

    Each method returns normalized dicts that the router sends straight to the frontend.
    Real GCP API calls will be added to each method in subsequent steps.
    """

    def __init__(self, credentials: dict):
        """
        Initialize with decrypted GCP Service Account credentials.

        credentials keys: type, project_id, private_key, client_email
        (standard fields from a GCP Service Account JSON file)
        """
        self._creds = credentials
        self._project_id = credentials.get("project_id", "")

    async def get_projects(self) -> list[dict]:
        """List GCP projects accessible with these credentials."""
        return [{"id": self._project_id, "name": self._project_id, "provider": "gcp"}]

    async def get_compute(self) -> list[dict]:
        """Return VMs, unattached disks, and unused static IPs — flagging wasteful ones."""
        return []

    async def get_metrics(self, request) -> list[dict]:
        """Return CPU / RAM time-series for compute resources."""
        return []

    async def get_billing(self) -> dict:
        """Return cost breakdown and spend anomalies for the project."""
        return {}
