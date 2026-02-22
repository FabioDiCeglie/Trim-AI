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
from providers.gcp.billing import get_project_billing_info
from providers.gcp.overview import build_overview


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

    async def get_compute(self, project_id: str | None = None) -> list[dict]:
        """
        Return all GCP resources — Compute Engine (VMs, disks, IPs), Cloud Run,
        Cloud SQL, Storage, Cloud Functions, Load Balancers, BigQuery, GKE —
        flagging wasteful ones. Use project_id to scope to a specific project.
        """
        pid = project_id or self._project_id
        token = await self._auth.get_access_token()
        vms = await list_instances(pid, token)
        disks = await list_disks(pid, token)
        ips = await list_addresses(pid, token)
        cloud_run = await list_cloud_run_services(pid, token)
        cloud_sql = await list_cloud_sql_instances(pid, token)
        storage = await list_storage_buckets(pid, token)
        functions = await list_cloud_functions(pid, token)
        load_balancers = await list_load_balancers(pid, token)
        bigquery = await list_bigquery_datasets(pid, token)
        gke = await list_gke_clusters(pid, token)
        return vms + disks + ips + cloud_run + cloud_sql + storage + functions + load_balancers + bigquery + gke

    async def get_metrics(self, request, project_id: str | None = None) -> list[dict]:
        """Return CPU / RAM time-series for GCE VMs, Cloud Run, Cloud SQL, and GKE (last 30 days by default)."""
        pid = project_id or self._project_id
        token = await self._auth.get_access_token()
        days = 30
        try:
            from urllib.parse import parse_qs, urlparse
            query = parse_qs(urlparse(request.url).query)
            if "days" in query and query["days"]:
                days = max(1, min(30, int(query["days"][0])))
        except (ValueError, IndexError):
            pass
        vm = await list_instance_metrics(pid, token, days=days)
        cloud_run = await list_cloud_run_metrics(pid, token, days=days)
        cloud_sql = await list_cloud_sql_metrics(pid, token, days=days)
        gke = await list_gke_metrics(pid, token, days=days)
        return vm + cloud_run + cloud_sql + gke

    async def get_billing(self, compute: list[dict] | None = None, project_id: str | None = None) -> dict:
        """Return billing account info. Pass compute when building overview to get potential_savings from BigQuery export."""
        pid = project_id or self._project_id
        token = await self._auth.get_access_token()
        return await get_project_billing_info(
            pid,
            token,
            credentials=self._creds,
            compute=compute,
        )

    async def get_overview(self, request, project_id: str | None = None) -> dict:
        """Single dashboard payload: compute, metrics (with utilization), billing, summary_cards, highlights. Optional project_id scopes to that project."""
        pid = project_id or self._project_id
        compute = await self.get_compute(project_id=pid)
        metrics_list = await self.get_metrics(request, project_id=pid)
        billing = await self.get_billing(compute=compute, project_id=pid)
        return build_overview(compute, metrics_list, billing)

