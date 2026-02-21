"""
Cloud Monitoring (Stackdriver) — CPU and memory time-series for Compute Engine VMs.
Used for right-sizing and "What's going wrong" baselines.
"""
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from providers.gcp.compute import _fetch_gcp_api

MONITORING_BASE = "https://monitoring.googleapis.com/v3"
CPU_METRIC = 'metric.type="compute.googleapis.com/instance/cpu/utilization"'
# Memory requires Ops Agent on the VM; we still request it, API may return empty
MEMORY_METRIC = 'metric.type="agent.googleapis.com/memory/percent_used"'


def _interval_endpoints(days: int = 30) -> tuple[str, str]:
    """Return (startTime, endTime) in RFC3339 for the last N days."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    return start.isoformat().replace("+00:00", "Z"), now.isoformat().replace("+00:00", "Z")


async def list_instance_metrics(project_id: str, token: str, days: int = 30) -> list[dict]:
    """
    Fetch CPU (and if available, memory) time-series for all Compute Engine instances.
    Returns one entry per instance with metrics array: [{ timestamp, cpu_percent, ram_percent }].
    """
    start_time, end_time = _interval_endpoints(days)
    project_name = f"projects/{project_id}"

    # Fetch CPU utilization (always available for GCE VMs)
    cpu_url = (
        f"{MONITORING_BASE}/{project_name}/timeSeries?"
        f"filter={quote(CPU_METRIC)}&"
        f"interval.startTime={quote(start_time)}&"
        f"interval.endTime={quote(end_time)}&"
        f"aggregation.alignmentPeriod=3600s&"
        f"aggregation.perSeriesAligner=ALIGN_MEAN"
    )
    cpu_data = await _fetch_gcp_api(cpu_url, token, "GCP Monitoring API")
    if not cpu_data:
        return []

    # Build map: instance_id -> list of (timestamp, cpu_percent)
    by_instance: dict[str, list[dict]] = {}
    for ts in cpu_data.get("timeSeries", []):
        resource_labels = ts.get("resource", {}).get("labels", {})
        instance_id = resource_labels.get("instance_id", "")
        zone = resource_labels.get("zone", "")
        if not instance_id:
            continue
        points = []
        for point in ts.get("points", []):
            interval = point.get("interval", {})
            end = interval.get("endTime", "")
            # Value is 0-1 for utilization; convert to percent
            val = point.get("value", {}).get("doubleValue", 0) or 0
            points.append({"timestamp": end, "cpu_percent": round(float(val) * 100, 2), "ram_percent": None})
        key = f"{zone}/{instance_id}"
        by_instance[key] = points

    # Optionally fetch memory (agent-based; may be empty)
    memory_url = (
        f"{MONITORING_BASE}/{project_name}/timeSeries?"
        f"filter={quote(MEMORY_METRIC)}&"
        f"interval.startTime={quote(start_time)}&"
        f"interval.endTime={quote(end_time)}&"
        f"aggregation.alignmentPeriod=3600s&"
        f"aggregation.perSeriesAligner=ALIGN_MEAN"
    )
    memory_data = await _fetch_gcp_api(memory_url, token, "GCP Monitoring API")
    if memory_data:
        for ts in memory_data.get("timeSeries", []):
            resource_labels = ts.get("resource", {}).get("labels", {})
            instance_id = resource_labels.get("instance_id", "")
            zone = resource_labels.get("zone", "")
            if not instance_id:
                continue
            key = f"{zone}/{instance_id}"
            if key not in by_instance:
                continue
            # Match by timestamp and add ram_percent
            time_to_idx = {p["timestamp"]: i for i, p in enumerate(by_instance[key])}
            for point in ts.get("points", []):
                end = point.get("interval", {}).get("endTime", "")
                val = point.get("value", {}).get("doubleValue", 0) or 0
                if end in time_to_idx:
                    by_instance[key][time_to_idx[end]]["ram_percent"] = round(float(val), 2)

    # Normalize to list of { id, name, resource_type, metrics }
    result = []
    for key, points in by_instance.items():
        zone, instance_id = key.split("/", 1) if "/" in key else ("", key)
        result.append({
            "id": instance_id,
            "name": instance_id,  # Monitoring doesn't give display name; frontend can join with compute
            "provider": "gcp",
            "resource_type": "vm",
            "region": zone.rsplit("-", 1)[0] if zone else "",
            "metrics": sorted(points, key=lambda p: p["timestamp"]),
        })
    return result
