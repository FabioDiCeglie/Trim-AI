"""
Cloud Monitoring (Stackdriver) — CPU and memory time-series for GCE VMs,
Cloud Run, Cloud SQL, and GKE. Used for right-sizing and baselines.
"""
from providers.gcp.helpers import fetch_gcp_api
from providers.gcp.helpers import build_ts_url, interval_endpoints, value_from_point

# GCE
GCE_CPU = 'metric.type="compute.googleapis.com/instance/cpu/utilization"'
GCE_MEMORY = 'metric.type="agent.googleapis.com/memory/percent_used"'

# Cloud Run (run.googleapis.com)
RUN_CPU = 'metric.type="run.googleapis.com/container/cpu/utilizations"'
RUN_MEMORY = 'metric.type="run.googleapis.com/container/memory/utilizations"'

# Cloud SQL (cloudsql.googleapis.com)
SQL_CPU = 'metric.type="cloudsql.googleapis.com/database/cpu/utilization"'
SQL_MEMORY = 'metric.type="cloudsql.googleapis.com/database/memory/utilization"'

# GKE (kubernetes.io)
GKE_CPU = 'metric.type="kubernetes.io/container/cpu/limit_utilization"'
GKE_MEMORY = 'metric.type="kubernetes.io/container/memory/limit_utilization"'


async def list_instance_metrics(project_id: str, token: str, days: int = 30) -> list[dict]:
    """
    Fetch CPU (and if available, memory) time-series for all Compute Engine instances.
    Returns one entry per instance with metrics array: [{ timestamp, cpu_percent, ram_percent }].
    """
    start_time, end_time = interval_endpoints(days)
    project_name = f"projects/{project_id}"

    cpu_data = await fetch_gcp_api(
        build_ts_url(project_name, GCE_CPU, start_time, end_time), token, "GCP Monitoring API"
    )
    if not cpu_data:
        return []

    by_instance: dict[str, list[dict]] = {}
    for ts in cpu_data.get("timeSeries", []):
        resource_labels = ts.get("resource", {}).get("labels", {})
        instance_id = resource_labels.get("instance_id", "")
        zone = resource_labels.get("zone", "")
        if not instance_id:
            continue
        points = []
        for point in ts.get("points", []):
            end = point.get("interval", {}).get("endTime", "")
            val = value_from_point(point)
            points.append({"timestamp": end, "cpu_percent": round(val * 100, 2), "ram_percent": None})
        key = f"{zone}/{instance_id}"
        by_instance[key] = points

    memory_data = await fetch_gcp_api(
        build_ts_url(project_name, GCE_MEMORY, start_time, end_time), token, "GCP Monitoring API"
    )
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
            time_to_idx = {p["timestamp"]: i for i, p in enumerate(by_instance[key])}
            for point in ts.get("points", []):
                end = point.get("interval", {}).get("endTime", "")
                val = value_from_point(point)
                if end in time_to_idx:
                    by_instance[key][time_to_idx[end]]["ram_percent"] = round(val, 2)

    result = []
    for key, points in by_instance.items():
        zone, instance_id = key.split("/", 1) if "/" in key else ("", key)
        result.append({
            "id": instance_id,
            "name": instance_id,
            "provider": "gcp",
            "resource_type": "vm",
            "region": zone.rsplit("-", 1)[0] if zone else "",
            "metrics": sorted(points, key=lambda p: p["timestamp"]),
        })
    return result


async def list_cloud_run_metrics(project_id: str, token: str, days: int = 30) -> list[dict]:
    """CPU and memory utilization for Cloud Run revisions (services)."""
    start_time, end_time = interval_endpoints(days)
    project_name = f"projects/{project_id}"

    cpu_data = await fetch_gcp_api(
        build_ts_url(project_name, RUN_CPU, start_time, end_time), token, "GCP Monitoring API"
    )
    if not cpu_data:
        return []

    by_revision: dict[str, list[dict]] = {}
    for ts in cpu_data.get("timeSeries", []):
        labels = ts.get("resource", {}).get("labels", {})
        service_name = labels.get("service_name", "")
        revision_name = labels.get("revision_name", "")
        location = labels.get("location", "")
        if not service_name:
            continue
        key = f"{location}/{service_name}/{revision_name}"
        points = []
        for point in ts.get("points", []):
            end = point.get("interval", {}).get("endTime", "")
            val = value_from_point(point)
            # run utilizations can be 0-1 or 0-100; normalize to percent
            pct = val * 100 if val <= 1 else val
            points.append({"timestamp": end, "cpu_percent": round(pct, 2), "ram_percent": None})
        by_revision[key] = points

    memory_data = await fetch_gcp_api(
        build_ts_url(project_name, RUN_MEMORY, start_time, end_time), token, "GCP Monitoring API"
    )
    if memory_data:
        for ts in memory_data.get("timeSeries", []):
            labels = ts.get("resource", {}).get("labels", {})
            service_name = labels.get("service_name", "")
            revision_name = labels.get("revision_name", "")
            location = labels.get("location", "")
            if not service_name:
                continue
            key = f"{location}/{service_name}/{revision_name}"
            if key not in by_revision:
                continue
            time_to_idx = {p["timestamp"]: i for i, p in enumerate(by_revision[key])}
            for point in ts.get("points", []):
                end = point.get("interval", {}).get("endTime", "")
                val = value_from_point(point)
                pct = val * 100 if val <= 1 else val
                if end in time_to_idx:
                    by_revision[key][time_to_idx[end]]["ram_percent"] = round(pct, 2)

    result = []
    for key, points in by_revision.items():
        parts = key.split("/", 2)
        location = parts[0] if len(parts) > 0 else ""
        service_name = parts[1] if len(parts) > 1 else key
        revision_name = parts[2] if len(parts) > 2 else ""
        result.append({
            "id": key,
            "name": f"{service_name} ({revision_name})" if revision_name else service_name,
            "provider": "gcp",
            "resource_type": "cloud_run",
            "region": location.rsplit("-", 1)[0] if location else "",
            "metrics": sorted(points, key=lambda p: p["timestamp"]),
        })
    return result


async def list_cloud_sql_metrics(project_id: str, token: str, days: int = 30) -> list[dict]:
    """CPU and memory utilization for Cloud SQL instances."""
    start_time, end_time = interval_endpoints(days)
    project_name = f"projects/{project_id}"

    cpu_data = await fetch_gcp_api(
        build_ts_url(project_name, SQL_CPU, start_time, end_time), token, "GCP Monitoring API"
    )
    if not cpu_data:
        return []

    by_db: dict[str, list[dict]] = {}
    for ts in cpu_data.get("timeSeries", []):
        labels = ts.get("resource", {}).get("labels", {})
        database_id = labels.get("database_id", "")
        if not database_id:
            continue
        points = []
        for point in ts.get("points", []):
            end = point.get("interval", {}).get("endTime", "")
            val = value_from_point(point)
            # 10^2.% can be 0-1 or 0-100
            pct = val * 100 if val <= 1 else val
            points.append({"timestamp": end, "cpu_percent": round(pct, 2), "ram_percent": None})
        by_db[database_id] = points

    memory_data = await fetch_gcp_api(
        build_ts_url(project_name, SQL_MEMORY, start_time, end_time), token, "GCP Monitoring API"
    )
    if memory_data:
        for ts in memory_data.get("timeSeries", []):
            labels = ts.get("resource", {}).get("labels", {})
            database_id = labels.get("database_id", "")
            if not database_id or database_id not in by_db:
                continue
            time_to_idx = {p["timestamp"]: i for i, p in enumerate(by_db[database_id])}
            for point in ts.get("points", []):
                end = point.get("interval", {}).get("endTime", "")
                val = value_from_point(point)
                pct = val * 100 if val <= 1 else val
                if end in time_to_idx:
                    by_db[database_id][time_to_idx[end]]["ram_percent"] = round(pct, 2)

    result = []
    for database_id, points in by_db.items():
        # database_id is often "project:region:instance"
        name = database_id.split(":")[-1] if ":" in database_id else database_id
        region = database_id.split(":")[-2] if database_id.count(":") >= 2 else ""
        result.append({
            "id": database_id,
            "name": name,
            "provider": "gcp",
            "resource_type": "cloud_sql",
            "region": region,
            "metrics": sorted(points, key=lambda p: p["timestamp"]),
        })
    return result


async def list_gke_metrics(project_id: str, token: str, days: int = 30) -> list[dict]:
    """CPU and memory limit utilization for GKE containers."""
    start_time, end_time = interval_endpoints(days)
    project_name = f"projects/{project_id}"

    cpu_data = await fetch_gcp_api(
        build_ts_url(project_name, GKE_CPU, start_time, end_time), token, "GCP Monitoring API"
    )
    if not cpu_data:
        return []

    by_container: dict[str, list[dict]] = {}
    for ts in cpu_data.get("timeSeries", []):
        labels = ts.get("resource", {}).get("labels", {})
        cluster = labels.get("cluster_name", "")
        location = labels.get("location", "")
        namespace = labels.get("namespace_name", "")
        pod = labels.get("pod_name", "")
        container = labels.get("container_name", "")
        if not cluster or not container:
            continue
        key = f"{location}/{cluster}/{namespace}/{pod}/{container}"
        points = []
        for point in ts.get("points", []):
            end = point.get("interval", {}).get("endTime", "")
            val = value_from_point(point)
            points.append({"timestamp": end, "cpu_percent": round(val * 100, 2), "ram_percent": None})
        by_container[key] = points

    memory_data = await fetch_gcp_api(
        build_ts_url(project_name, GKE_MEMORY, start_time, end_time), token, "GCP Monitoring API"
    )
    if memory_data:
        for ts in memory_data.get("timeSeries", []):
            labels = ts.get("resource", {}).get("labels", {})
            cluster = labels.get("cluster_name", "")
            location = labels.get("location", "")
            namespace = labels.get("namespace_name", "")
            pod = labels.get("pod_name", "")
            container = labels.get("container_name", "")
            if not cluster or not container:
                continue
            key = f"{location}/{cluster}/{namespace}/{pod}/{container}"
            if key not in by_container:
                continue
            time_to_idx = {p["timestamp"]: i for i, p in enumerate(by_container[key])}
            for point in ts.get("points", []):
                end = point.get("interval", {}).get("endTime", "")
                val = value_from_point(point)
                if end in time_to_idx:
                    by_container[key][time_to_idx[end]]["ram_percent"] = round(val * 100, 2)

    result = []
    for key, points in by_container.items():
        parts = key.split("/", 4)
        location = parts[0] if len(parts) > 0 else ""
        cluster = parts[1] if len(parts) > 1 else ""
        namespace = parts[2] if len(parts) > 2 else ""
        pod = parts[3] if len(parts) > 3 else ""
        container = parts[4] if len(parts) > 4 else ""
        result.append({
            "id": key,
            "name": f"{container} ({namespace}/{pod})" if pod else f"{container} ({namespace})",
            "provider": "gcp",
            "resource_type": "gke_container",
            "region": location.rsplit("-", 1)[0] if location else "",
            "metrics": sorted(points, key=lambda p: p["timestamp"]),
        })
    return result
