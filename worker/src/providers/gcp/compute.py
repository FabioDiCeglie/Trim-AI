import js
import json
from pyodide.ffi import to_js

COMPUTE_BASE = "https://compute.googleapis.com/compute/v1"


async def list_instances(project_id: str, token: str) -> list[dict]:
    """
    Fetch all VM instances across all zones using the aggregatedList API.
    Flags stopped VMs as waste — they still charge for attached disks and reserved IPs.
    """
    url = f"{COMPUTE_BASE}/projects/{project_id}/aggregated/instances"
    resp = await js.fetch(
        url,
        to_js({"headers": {"Authorization": f"Bearer {token}"}}, dict_converter=js.Object.fromEntries),
    )
    raw = await resp.text()
    if not raw.strip():
        raise Exception("Empty response from GCP Compute API — check service account permissions (needs Compute Viewer role)")
    data = json.loads(raw)
    if "error" in data:
        raise Exception(f"GCP Compute API error: {data['error'].get('message', data['error'])}")

    instances = []
    for zone_data in data.get("items", {}).values():
        for vm in zone_data.get("instances", []):
            status = vm.get("status", "")
            is_stopped = status != "RUNNING"

            instances.append({
                "id": vm.get("id", ""),
                "name": vm.get("name", ""),
                "provider": "gcp",
                "resource_type": "vm",
                "region": _parse_zone(vm.get("zone", "")),
                "status": "waste" if is_stopped else "healthy",
                "waste_reason": "stopped" if is_stopped else "none",
                "recommended_action": "Delete or start the VM" if is_stopped else "",
                "machine_type": _parse_machine_type(vm.get("machineType", "")),
                "vm_status": status,
            })

    return instances


def _parse_zone(zone_url: str) -> str:
    """Extract zone name from a full GCP zone URL."""
    return zone_url.split("/")[-1] if zone_url else ""


def _parse_machine_type(mt_url: str) -> str:
    """Extract machine type name from a full GCP machineType URL."""
    return mt_url.split("/")[-1] if mt_url else ""
