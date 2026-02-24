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
        "waste_count": 3,
        "with_metrics": 18,
        "over_provisioned": 2,
        "under_provisioned": 1,
    },
    "summary_cards": [
        {"id": "total_resources", "label": "Total resources", "value": 24},
        {"id": "waste_count", "label": "Waste", "value": 3, "sublabel": "need attention"},
        {"id": "with_metrics", "label": "With metrics", "value": 18},
        {"id": "potential_savings", "label": "Potential savings", "value": "48.6", "sublabel": "USD/month"},
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
    ],
    "compute": [],
    "metrics": [],
    "billing": {
        "billing_account_display_name": "My Billing Account",
        "currency_code": "USD",
        "potential_savings": {"value": 48.6, "currency": "USD"},
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
        "waste_count": 5,
        "with_metrics": 24,
        "over_provisioned": 3,
        "under_provisioned": 1,
    },
    "summary_cards": [
        {"id": "total_resources", "label": "Total resources", "value": 32},
        {"id": "waste_count", "label": "Waste", "value": 5, "sublabel": "need attention"},
        {"id": "with_metrics", "label": "With metrics", "value": 24},
        {"id": "potential_savings", "label": "Potential savings", "value": "72.6", "sublabel": "USD/month"},
    ],
    "highlights": DEMO_OVERVIEW["highlights"] + DEMO_OVERVIEW_STAGING["highlights"],
    "compute": [],
    "metrics": [],
    "billing": {
        "billing_account_display_name": "My Billing Account",
        "currency_code": "USD",
        "potential_savings": {"value": 72.6, "currency": "USD"},
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
