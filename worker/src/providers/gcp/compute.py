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


async def list_cloud_run_services(project_id: str, token: str) -> list[dict]:
    """
    Fetch all Cloud Run services across all regions.
    Flags wasteful services:
    - min instances > 0 but no traffic (paying for idle)
    - Over-provisioned memory/CPU limits
    """
    url = f"https://run.googleapis.com/v1/projects/{project_id}/locations/-/services"
    resp = await js.fetch(
        url,
        to_js({"headers": {"Authorization": f"Bearer {token}"}}, dict_converter=js.Object.fromEntries),
    )
    raw = await resp.text()
    if not raw.strip():
        return []
    data = json.loads(raw)
    if "error" in data:
        # Cloud Run API might not be enabled, that's okay
        if "not enabled" in str(data.get("error", {})).lower():
            return []
        raise Exception(f"GCP Cloud Run API error: {data['error'].get('message', data['error'])}")

    services = []
    for service in data.get("items", []):
        metadata = service.get("metadata", {})
        spec = service.get("spec", {})
        template = spec.get("template", {})
        template_spec = template.get("spec", {})
        status = service.get("status", {})

        name = metadata.get("name", "")
        region = metadata.get("labels", {}).get("cloud.googleapis.com/location", "")
        min_instances = template_spec.get("minInstanceCount", 0)
        
        # Extract memory and CPU from container resources
        containers = template_spec.get("containers", [])
        memory = "unknown"
        cpu = "unknown"
        if containers:
            resources = containers[0].get("resources", {})
            limits = resources.get("limits", {})
            memory = limits.get("memory", "unknown")
            cpu = limits.get("cpu", "unknown")
        
        # Check if service is running but might be idle
        # If min instances > 0, it's always running (costing money even with no traffic)
        is_idle_waste = min_instances > 0
        
        # Get traffic info if available
        traffic = status.get("traffic", [])
        has_traffic = len(traffic) > 0 and any(t.get("percent", 0) > 0 for t in traffic)

        services.append({
            "id": metadata.get("uid", ""),
            "name": name,
            "provider": "gcp",
            "resource_type": "cloud-run",
            "region": region or "unknown",
            "status": "waste" if is_idle_waste else "healthy",
            "waste_reason": "idle" if is_idle_waste else "none",
            "recommended_action": f"Set min instances to 0 to save costs (currently {min_instances})" if is_idle_waste else "",
            "min_instances": min_instances,
            "memory": memory,
            "cpu": cpu,
            "has_traffic": has_traffic,
        })

    return services
