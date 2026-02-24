"""
Demo routes for the try-it-out flow. No authentication required.

GET  /api/v1/demo/projects  — two mock projects
GET  /api/v1/demo/overview  — mock overview (supports ?project= filter)
"""
from utils import ok
from workers import Response


DEMO_PROJECTS = [
    {"id": "demo-project-prod", "name": "acme-prod", "provider": "gcp"},
    {"id": "demo-project-staging", "name": "acme-staging", "provider": "gcp"},
]


DEMO_OVERVIEW = {
    "summary": {
        "total_resources": 24,
        "waste_count": 12,
        "with_metrics": 18,
        "over_provisioned": 3,
        "under_provisioned": 1,
    },
    "summary_cards": [
        {"id": "total_resources", "label": "Total resources", "value": 24},
        {"id": "waste_count", "label": "Waste", "value": 12, "sublabel": "need attention"},
        {"id": "with_metrics", "label": "With metrics", "value": 18},
        {"id": "potential_savings", "label": "Potential savings", "value": "447.8", "sublabel": "USD/month"},
    ],
    "highlights": [
        {
            "type": "compute",
            "resource_type": "vm",
            "id": "vm-1",
            "name": "e2-medium-instance-prod",
            "reason": "Idle / low utilization",
            "recommended_action": "Downsize to e2-small or stop when not needed.",
            "estimated_savings": {"value": 28, "currency": "USD"},
        },
        {
            "type": "compute",
            "resource_type": "disk",
            "id": "disk-1",
            "name": "pd-ssd-100gb-unattached",
            "reason": "Unattached disk",
            "recommended_action": "Delete if no longer needed or snapshot and remove.",
            "estimated_savings": {"value": 17, "currency": "USD"},
        },
        {
            "type": "compute",
            "resource_type": "ip",
            "id": "ip-1",
            "name": "static-ip-unused",
            "reason": "Static IP not in use",
            "recommended_action": "Release the address to avoid ongoing cost.",
            "estimated_savings": {"value": 3.6, "currency": "USD"},
        },
        {
            "type": "compute",
            "resource_type": "vm",
            "id": "vm-3",
            "name": "n2-standard-4-batch-worker",
            "reason": "Stopped for 18 days",
            "recommended_action": "Delete or snapshot if not scheduled to restart.",
            "estimated_savings": {"value": 95, "currency": "USD"},
        },
        {
            "type": "compute",
            "resource_type": "vm",
            "id": "vm-4",
            "name": "e2-micro-legacy-proxy",
            "reason": "Avg CPU 0.3% over 30 days",
            "recommended_action": "Migrate traffic to Cloud Run and terminate.",
            "estimated_savings": {"value": 6.5, "currency": "USD"},
        },
        {
            "type": "compute",
            "resource_type": "disk",
            "id": "disk-3",
            "name": "pd-ssd-500gb-old-db-backup",
            "reason": "Unattached disk, created 6 months ago",
            "recommended_action": "Snapshot to Cloud Storage and delete.",
            "estimated_savings": {"value": 85, "currency": "USD"},
        },
        {
            "type": "compute",
            "resource_type": "disk",
            "id": "disk-4",
            "name": "pd-standard-200gb-test-data",
            "reason": "Unattached, no reads in 90 days",
            "recommended_action": "Delete if test data is no longer needed.",
            "estimated_savings": {"value": 8, "currency": "USD"},
        },
        {
            "type": "compute",
            "resource_type": "ip",
            "id": "ip-2",
            "name": "static-ip-old-lb",
            "reason": "Reserved IP, load balancer deleted",
            "recommended_action": "Release the address.",
            "estimated_savings": {"value": 3.6, "currency": "USD"},
        },
        {
            "type": "compute",
            "resource_type": "vm",
            "id": "vm-5",
            "name": "n1-highmem-4-analytics",
            "reason": "Over-provisioned (avg RAM 12%)",
            "recommended_action": "Downsize to e2-standard-2 or n2-standard-2.",
            "estimated_savings": {"value": 120, "currency": "USD"},
        },
        {
            "type": "compute",
            "resource_type": "vm",
            "id": "vm-6",
            "name": "e2-standard-2-jenkins-ci",
            "reason": "Runs only during business hours but billed 24/7",
            "recommended_action": "Use instance schedule or preemptible VM.",
            "estimated_savings": {"value": 35, "currency": "USD"},
        },
        {
            "type": "compute",
            "resource_type": "disk",
            "id": "disk-5",
            "name": "pd-ssd-250gb-ml-training",
            "reason": "Unattached since last training run",
            "recommended_action": "Archive to Cloud Storage bucket and delete.",
            "estimated_savings": {"value": 42.5, "currency": "USD"},
        },
        {
            "type": "compute",
            "resource_type": "ip",
            "id": "ip-3",
            "name": "static-ip-dev-vpn",
            "reason": "VPN gateway deleted, IP still reserved",
            "recommended_action": "Release the address.",
            "estimated_savings": {"value": 3.6, "currency": "USD"},
        },
    ],
    "compute": [],
    "metrics": [],
    "billing": {
        "billing_account_display_name": "My Billing Account",
        "currency_code": "USD",
        "potential_savings": {"value": 447.8, "currency": "USD"},
        "top_services": [
            {"service": "Compute Engine", "cost": 412.5},
            {"service": "Cloud Storage", "cost": 89.2},
            {"service": "BigQuery", "cost": 56.8},
            {"service": "Cloud Run", "cost": 34.1},
            {"service": "Networking", "cost": 28.4},
        ],
    },
}


DEMO_OVERVIEW_STAGING = {
    "summary": {
        "total_resources": 8,
        "waste_count": 2,
        "with_metrics": 6,
        "over_provisioned": 1,
        "under_provisioned": 0,
    },
    "summary_cards": [
        {"id": "total_resources", "label": "Total resources", "value": 8},
        {"id": "waste_count", "label": "Waste", "value": 2, "sublabel": "need attention"},
        {"id": "with_metrics", "label": "With metrics", "value": 6},
        {"id": "potential_savings", "label": "Potential savings", "value": "24", "sublabel": "USD/month"},
    ],
    "highlights": [
        {
            "type": "compute",
            "resource_type": "vm",
            "id": "vm-2",
            "name": "n1-standard-2-staging-api",
            "reason": "Over-provisioned (avg CPU 4%)",
            "recommended_action": "Downsize to e2-small or switch to Cloud Run.",
            "estimated_savings": {"value": 18, "currency": "USD"},
        },
        {
            "type": "compute",
            "resource_type": "disk",
            "id": "disk-2",
            "name": "pd-standard-50gb-old-backup",
            "reason": "Unattached disk, no recent reads",
            "recommended_action": "Snapshot and delete if no longer needed.",
            "estimated_savings": {"value": 6, "currency": "USD"},
        },
    ],
    "compute": [],
    "metrics": [],
    "billing": {
        "billing_account_display_name": "My Billing Account",
        "currency_code": "USD",
        "potential_savings": {"value": 24, "currency": "USD"},
        "top_services": [
            {"service": "Compute Engine", "cost": 156.2},
            {"service": "Cloud Storage", "cost": 32.1},
            {"service": "Cloud Run", "cost": 18.5},
        ],
    },
}


DEMO_OVERVIEW_ALL = {
    "summary": {
        "total_resources": 32,
        "waste_count": 14,
        "with_metrics": 24,
        "over_provisioned": 4,
        "under_provisioned": 1,
    },
    "summary_cards": [
        {"id": "total_resources", "label": "Total resources", "value": 32},
        {"id": "waste_count", "label": "Waste", "value": 14, "sublabel": "need attention"},
        {"id": "with_metrics", "label": "With metrics", "value": 24},
        {"id": "potential_savings", "label": "Potential savings", "value": "471.8", "sublabel": "USD/month"},
    ],
    "highlights": DEMO_OVERVIEW["highlights"] + DEMO_OVERVIEW_STAGING["highlights"],
    "compute": [],
    "metrics": [],
    "billing": {
        "billing_account_display_name": "My Billing Account",
        "currency_code": "USD",
        "potential_savings": {"value": 471.8, "currency": "USD"},
        "top_services": [
            {"service": "Compute Engine", "cost": 568.7},
            {"service": "Cloud Storage", "cost": 121.3},
            {"service": "BigQuery", "cost": 56.8},
            {"service": "Cloud Run", "cost": 52.6},
            {"service": "Networking", "cost": 28.4},
        ],
    },
}


def _get_demo_overview(project_id: str | None = None) -> dict:
    if project_id == "demo-project-staging":
        return DEMO_OVERVIEW_STAGING
    if project_id == "demo-project-prod":
        return DEMO_OVERVIEW
    return DEMO_OVERVIEW_ALL


async def demo_projects() -> Response:
    return ok(DEMO_PROJECTS)


async def demo_overview(request) -> Response:
    from urllib.parse import parse_qs, urlparse
    query = parse_qs(urlparse(request.url).query)
    project_id = query.get("project", [None])[0] if query.get("project") else None
    return ok(_get_demo_overview(project_id))
