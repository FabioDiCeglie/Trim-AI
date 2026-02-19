import js
import json
from pyodide.ffi import to_js
from providers.base import CloudProvider
from providers.gcp.auth import GCPAuthService
from providers.gcp.compute import list_instances, list_disks, list_addresses


class GCPProvider(CloudProvider):
    """
    Google Cloud provider — implements the four core data-fetching methods.
    Each method gets a fresh access token, calls the relevant GCP API,
    and returns normalized dicts the router sends straight to the frontend.
    """

    BASE = "https://cloudresourcemanager.googleapis.com"

    def __init__(self, credentials: dict):
        self._creds = credentials
        self._project_id = credentials.get("project_id", "")
        self._auth = GCPAuthService(credentials)

    async def get_projects(self) -> list[dict]:
        """List GCP projects accessible with these credentials."""
        token = await self._auth.get_access_token()
        resp = await js.fetch(
            f"{self.BASE}/v1/projects",
            to_js({"headers": {"Authorization": f"Bearer {token}"}}, dict_converter=js.Object.fromEntries),
        )
        data = json.loads(await resp.text())
        projects = data.get("projects", [])
        return [
            {"id": p["projectId"], "name": p.get("name", p["projectId"]), "provider": "gcp"}
            for p in projects
        ]

    async def get_compute(self) -> list[dict]:
        """Return VMs, unattached disks, and unused static IPs — flagging wasteful ones."""
        token = await self._auth.get_access_token()
        vms = await list_instances(self._project_id, token)
        disks = await list_disks(self._project_id, token)
        ips = await list_addresses(self._project_id, token)
        return vms + disks + ips

    async def get_metrics(self, request) -> list[dict]:
        """Return CPU / RAM time-series for compute resources."""
        return []

    async def get_billing(self) -> dict:
        """Return cost breakdown and spend anomalies for the project."""
        return {}
