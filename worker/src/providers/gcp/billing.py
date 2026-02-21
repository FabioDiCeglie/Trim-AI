"""
GCP Cloud Billing API — project billing info and billing account details.
Cost breakdown by service (top_services, anomalies) requires BigQuery billing export;
this module returns what the Billing REST API provides.
"""
from providers.gcp.helpers import fetch_gcp_api

BILLING_BASE = "https://cloudbilling.googleapis.com/v1"


async def get_project_billing_info(project_id: str, token: str) -> dict:
    """
    Get billing info for the project (linked billing account, enabled flag).
    Returns normalized dict for the frontend; empty dict if API not enabled or no access.
    """
    url = f"{BILLING_BASE}/projects/{project_id}/billingInfo"
    data = await fetch_gcp_api(url, token, "GCP Cloud Billing API")
    if not data:
        return {
            "billing_enabled": False,
            "billing_account_id": None,
            "billing_account_display_name": None,
            "currency_code": None,
            "top_services": [],
            "month_over_month_delta": None,
            "anomalies": [],
        }

    billing_account_name = data.get("billingAccountName") or ""
    billing_account_id = billing_account_name.replace("billingAccounts/", "") if billing_account_name else None
    billing_enabled = data.get("billingEnabled", False)

    # Optionally fetch billing account details (display name, currency)
    display_name = None
    currency_code = None
    if billing_account_name:
        account = await fetch_gcp_api(
            f"{BILLING_BASE}/{billing_account_name}",
            token,
            "GCP Cloud Billing API",
        )
        if account:
            display_name = account.get("displayName")
            currency_code = account.get("currencyCode", "USD")

    return {
        "billing_enabled": billing_enabled,
        "billing_account_id": billing_account_id,
        "billing_account_display_name": display_name,
        "currency_code": currency_code or "USD",
        "top_services": [],  # Requires BigQuery billing export
        "month_over_month_delta": None,  # Requires BigQuery billing export
        "anomalies": [],  # Requires BigQuery billing export or Monitoring
    }
