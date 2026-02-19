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


async def list_disks(project_id: str, token: str) -> list[dict]:
    """
    Fetch all persistent disks across all zones.
    Flags unattached disks as waste — they cost money but aren't being used.
    """
    url = f"{COMPUTE_BASE}/projects/{project_id}/aggregated/disks"
    resp = await js.fetch(
        url,
        to_js({"headers": {"Authorization": f"Bearer {token}"}}, dict_converter=js.Object.fromEntries),
    )
    raw = await resp.text()
    if not raw.strip():
        return []
    data = json.loads(raw)
    if "error" in data:
        raise Exception(f"GCP Compute API error: {data['error'].get('message', data['error'])}")

    disks = []
    for zone_data in data.get("items", {}).values():
        for disk in zone_data.get("disks", []):
            users = disk.get("users", [])
            is_unattached = len(users) == 0
            size_gb = int(disk.get("sizeGb", 0))

            disks.append({
                "id": str(disk.get("id", "")),
                "name": disk.get("name", ""),
                "provider": "gcp",
                "resource_type": "disk",
                "region": _parse_zone(disk.get("zone", "")),
                "status": "waste" if is_unattached else "healthy",
                "waste_reason": "unattached" if is_unattached else "none",
                "recommended_action": "Delete this disk to stop charges" if is_unattached else "",
                "size_gb": size_gb,
                "attached_to": users[0] if users else None,
            })

    return disks


async def list_addresses(project_id: str, token: str) -> list[dict]:
    """
    Fetch all static external IP addresses (reserved but may be unassigned).
    Flags unused IPs as waste — they cost money even if not assigned to a VM.
    """
    url = f"{COMPUTE_BASE}/projects/{project_id}/aggregated/addresses"
    resp = await js.fetch(
        url,
        to_js({"headers": {"Authorization": f"Bearer {token}"}}, dict_converter=js.Object.fromEntries),
    )
    raw = await resp.text()
    if not raw.strip():
        return []
    data = json.loads(raw)
    if "error" in data:
        raise Exception(f"GCP Compute API error: {data['error'].get('message', data['error'])}")

    addresses = []
    for region_data in data.get("items", {}).values():
        for addr in region_data.get("addresses", []):
            users = addr.get("users", [])
            is_unused = len(users) == 0
            ip_address = addr.get("address", "")

            addresses.append({
                "id": str(addr.get("id", "")),
                "name": addr.get("name", ""),
                "provider": "gcp",
                "resource_type": "ip",
                "region": _parse_region(addr.get("region", "")),
                "status": "waste" if is_unused else "healthy",
                "waste_reason": "unused" if is_unused else "none",
                "recommended_action": "Release this IP to stop charges" if is_unused else "",
                "ip_address": ip_address,
                "assigned_to": users[0] if users else None,
            })

    return addresses


def _parse_region(region_url: str) -> str:
    """Extract region name from a full GCP region URL."""
    return region_url.split("/")[-1] if region_url else ""
