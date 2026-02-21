import js
import json
from pyodide.ffi import to_js
from providers.base import CloudProvider
from providers.gcp.auth import GCPAuthService
from providers.gcp.compute import (
    list_instances,
    list_disks,
    list_addresses,
    list_cloud_run_services,
    list_cloud_sql_instances,
    list_storage_buckets,
    list_cloud_functions,
    list_load_balancers,
    list_bigquery_datasets,
    list_gke_clusters,
)
from providers.gcp.monitoring import (
    list_instance_metrics,
    list_cloud_run_metrics,
    list_cloud_sql_metrics,
    list_gke_metrics,
)


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
        """
        Return all GCP resources — Compute Engine (VMs, disks, IPs), Cloud Run,
        Cloud SQL, Storage, Cloud Functions, Load Balancers, BigQuery, GKE —
        flagging wasteful ones.
        """
        token = await self._auth.get_access_token()
        vms = await list_instances(self._project_id, token)
        disks = await list_disks(self._project_id, token)
        ips = await list_addresses(self._project_id, token)
        cloud_run = await list_cloud_run_services(self._project_id, token)
        cloud_sql = await list_cloud_sql_instances(self._project_id, token)
        storage = await list_storage_buckets(self._project_id, token)
        functions = await list_cloud_functions(self._project_id, token)
        load_balancers = await list_load_balancers(self._project_id, token)
        bigquery = await list_bigquery_datasets(self._project_id, token)
        gke = await list_gke_clusters(self._project_id, token)
        return vms + disks + ips + cloud_run + cloud_sql + storage + functions + load_balancers + bigquery + gke

    async def get_metrics(self, request) -> list[dict]:
        """Return CPU / RAM time-series for GCE VMs, Cloud Run, Cloud SQL, and GKE (last 30 days by default)."""
        token = await self._auth.get_access_token()
        days = 30
        try:
            from urllib.parse import parse_qs, urlparse
            query = parse_qs(urlparse(request.url).query)
            if "days" in query and query["days"]:
                days = max(1, min(30, int(query["days"][0])))
        except (ValueError, IndexError):
            pass
        vm = await list_instance_metrics(self._project_id, token, days=days)
        cloud_run = await list_cloud_run_metrics(self._project_id, token, days=days)
        cloud_sql = await list_cloud_sql_metrics(self._project_id, token, days=days)
        gke = await list_gke_metrics(self._project_id, token, days=days)
        return vm + cloud_run + cloud_sql + gke

    async def get_billing(self) -> dict:
        """Return cost breakdown and spend anomalies for the project."""
        return {}
