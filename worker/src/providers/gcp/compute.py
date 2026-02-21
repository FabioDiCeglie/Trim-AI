from providers.gcp.helpers import fetch_gcp_api, parse_resource_url

COMPUTE_BASE = "https://compute.googleapis.com/compute/v1"
SQL_BASE = "https://sqladmin.googleapis.com/v1"
STORAGE_BASE = "https://storage.googleapis.com/storage/v1"
FUNCTIONS_BASE = "https://cloudfunctions.googleapis.com/v1"
BIGQUERY_BASE = "https://bigquery.googleapis.com/bigquery/v2"
CONTAINER_BASE = "https://container.googleapis.com/v1"


async def list_instances(project_id: str, token: str) -> list[dict]:
    """Fetch all VM instances across all zones. Flags stopped VMs as waste."""
    url = f"{COMPUTE_BASE}/projects/{project_id}/aggregated/instances"
    data = await fetch_gcp_api(url, token, "GCP Compute API")
    if not data:
        return []

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
                "region": parse_resource_url(vm.get("zone", "")),
                "status": "waste" if is_stopped else "healthy",
                "waste_reason": "stopped" if is_stopped else "none",
                "recommended_action": "Delete or start the VM" if is_stopped else "",
                "machine_type": parse_resource_url(vm.get("machineType", "")),
                "vm_status": status,
            })

    return instances


async def list_disks(project_id: str, token: str) -> list[dict]:
    """Fetch all persistent disks. Flags unattached disks as waste."""
    url = f"{COMPUTE_BASE}/projects/{project_id}/aggregated/disks"
    data = await fetch_gcp_api(url, token, "GCP Compute API")
    if not data:
        return []

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
                "region": parse_resource_url(disk.get("zone", "")),
                "status": "waste" if is_unattached else "healthy",
                "waste_reason": "unattached" if is_unattached else "none",
                "recommended_action": "Delete this disk to stop charges" if is_unattached else "",
                "size_gb": size_gb,
                "attached_to": users[0] if users else None,
            })

    return disks


async def list_addresses(project_id: str, token: str) -> list[dict]:
    """Fetch all static external IP addresses. Flags unused IPs as waste."""
    url = f"{COMPUTE_BASE}/projects/{project_id}/aggregated/addresses"
    data = await fetch_gcp_api(url, token, "GCP Compute API")
    if not data:
        return []

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
                "region": parse_resource_url(addr.get("region", "")),
                "status": "waste" if is_unused else "healthy",
                "waste_reason": "unused" if is_unused else "none",
                "recommended_action": "Release this IP to stop charges" if is_unused else "",
                "ip_address": ip_address,
                "assigned_to": users[0] if users else None,
            })

    return addresses


async def list_cloud_run_services(project_id: str, token: str) -> list[dict]:
    """Fetch all Cloud Run services. Flags services with min_instances > 0 as waste."""
    url = f"https://run.googleapis.com/v1/projects/{project_id}/locations/-/services"
    data = await fetch_gcp_api(url, token, "GCP Cloud Run API")
    if not data:
        return []

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


async def list_cloud_sql_instances(project_id: str, token: str) -> list[dict]:
    """Fetch all Cloud SQL instances. Flags stopped instances as waste."""
    url = f"{SQL_BASE}/projects/{project_id}/instances"
    data = await fetch_gcp_api(url, token, "GCP Cloud SQL API")
    if not data:
        return []

    instances = []
    for db in data.get("items", []):
        name = db.get("name", "")
        region = db.get("region", "")
        state = db.get("state", "")
        settings = db.get("settings", {})
        tier = settings.get("tier", "")
        data_disk_size_gb = settings.get("dataDiskSizeGb", 0)
        data_disk_type = settings.get("dataDiskType", "")
        
        # Check if instance is stopped or in maintenance
        is_stopped = state != "RUNNABLE"
        
        instances.append({
            "id": str(db.get("id", "")),
            "name": name,
            "provider": "gcp",
            "resource_type": "cloud-sql",
            "region": region,
            "status": "waste" if is_stopped else "healthy",
            "waste_reason": "stopped" if is_stopped else "none",
            "recommended_action": "Delete or start the instance" if is_stopped else "",
            "tier": tier,
            "disk_size_gb": data_disk_size_gb,
            "disk_type": data_disk_type,
            "state": state,
        })

    return instances


async def list_storage_buckets(project_id: str, token: str) -> list[dict]:
    """Fetch all Cloud Storage buckets. Flags Standard class buckets as potential waste."""
    url = f"{STORAGE_BASE}/b?project={project_id}"
    data = await fetch_gcp_api(url, token, "GCP Storage API")
    if not data:
        return []

    buckets = []
    for bucket in data.get("items", []):
        name = bucket.get("name", "")
        location = bucket.get("location", "")
        storage_class = bucket.get("storageClass", "STANDARD")
        created = bucket.get("timeCreated", "")
        
        # Flag Standard class buckets as potential waste (could use cheaper Nearline/Coldline)
        # This is a simple heuristic - in reality we'd need to check access patterns
        is_waste = storage_class == "STANDARD" and created  # Could be improved with access time analysis
        
        buckets.append({
            "id": name,  # Bucket name is unique
            "name": name,
            "provider": "gcp",
            "resource_type": "storage-bucket",
            "region": location,
            "status": "warning" if is_waste else "healthy",
            "waste_reason": "wrong-storage-class" if is_waste else "none",
            "recommended_action": "Consider Nearline or Coldline storage class for infrequently accessed data" if is_waste else "",
            "storage_class": storage_class,
            "created": created,
        })

    return buckets


async def list_cloud_functions(project_id: str, token: str) -> list[dict]:
    """Fetch all Cloud Functions (Gen 1). Would need metrics to detect unused ones."""
    url = f"{FUNCTIONS_BASE}/projects/{project_id}/locations/-/functions"
    data = await fetch_gcp_api(url, token, "GCP Cloud Functions API")
    if not data:
        return []

    functions = []
    for func in data.get("functions", []):
                name = func.get("name", "").split("/")[-1]
                region = func.get("name", "").split("/")[3] if "/" in func.get("name", "") else "unknown"
                runtime = func.get("runtime", "")
                available_memory_mb = func.get("availableMemoryMb", 256)
                timeout = func.get("timeout", "")
                
                functions.append({
                    "id": func.get("name", ""),
                    "name": name,
                    "provider": "gcp",
                    "resource_type": "cloud-function",
                    "region": region,
                    "status": "healthy",  # Would need metrics to detect unused
                    "waste_reason": "none",
                    "recommended_action": "",
                    "runtime": runtime,
                    "memory_mb": available_memory_mb,
                    "timeout": timeout,
                })
    
    return functions


async def list_load_balancers(project_id: str, token: str) -> list[dict]:
    """Fetch all Load Balancers. Flags unused ones (no backends) as waste."""
    url = f"{COMPUTE_BASE}/projects/{project_id}/global/backendServices"
    data = await fetch_gcp_api(url, token, "GCP Compute API")
    if not data:
        return []

    load_balancers = []
    for lb in data.get("items", []):
        name = lb.get("name", "")
        backends = lb.get("backends", [])
        is_unused = len(backends) == 0
        
        load_balancers.append({
            "id": str(lb.get("id", "")),
            "name": name,
            "provider": "gcp",
            "resource_type": "load-balancer",
            "region": "global",
            "status": "waste" if is_unused else "healthy",
            "waste_reason": "unused" if is_unused else "none",
            "recommended_action": "Delete this load balancer" if is_unused else "",
            "backend_count": len(backends),
        })

    return load_balancers


async def list_bigquery_datasets(project_id: str, token: str) -> list[dict]:
    """Fetch all BigQuery datasets. Would need query metrics to detect unused ones."""
    url = f"{BIGQUERY_BASE}/projects/{project_id}/datasets"
    data = await fetch_gcp_api(url, token, "GCP BigQuery API")
    if not data:
        return []

    datasets = []
    for dataset in data.get("datasets", []):
        ref = dataset.get("datasetReference", {})
        name = ref.get("datasetId", "")
        location = dataset.get("location", "")
        created = dataset.get("creationTime", "")
        
        datasets.append({
            "id": f"{project_id}:{name}",
            "name": name,
            "provider": "gcp",
            "resource_type": "bigquery-dataset",
            "region": location,
            "status": "healthy",  # Would need query metrics to detect unused
            "waste_reason": "none",
            "recommended_action": "",
            "created": created,
        })

    return datasets


async def list_gke_clusters(project_id: str, token: str) -> list[dict]:
    """Fetch all GKE (Google Kubernetes Engine) clusters. Flags idle/oversized node pools."""
    url = f"{CONTAINER_BASE}/projects/{project_id}/locations/-/clusters"
    data = await fetch_gcp_api(url, token, "GCP GKE API")
    if not data:
        return []

    clusters = []
    for cluster in data.get("clusters", []):
        name = cluster.get("name", "")
        location = cluster.get("location", "")
        status = cluster.get("status", "")
        node_pools = cluster.get("nodePools", [])
        current_node_count = cluster.get("currentNodeCount", 0)
        
        # Stopped or error state = waste; empty cluster = potential waste
        is_stopped = status not in ("RUNNING", "RECONCILING")
        is_empty = current_node_count == 0 and not is_stopped
        
        clusters.append({
            "id": cluster.get("id", ""),
            "name": name,
            "provider": "gcp",
            "resource_type": "gke-cluster",
            "region": location,
            "status": "waste" if is_stopped else ("warning" if is_empty else "healthy"),
            "waste_reason": "stopped" if is_stopped else ("empty" if is_empty else "none"),
            "recommended_action": "Delete or start the cluster" if is_stopped else ("Consider deleting if unused" if is_empty else ""),
            "node_pool_count": len(node_pools),
            "current_node_count": current_node_count,
            "cluster_status": status,
        })

    return clusters
