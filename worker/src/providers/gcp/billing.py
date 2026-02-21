"""
GCP Cloud Billing API — project billing info, billing account details, and
cost data from BigQuery billing export. When export is configured, returns
top_services and potential_savings so the product can say "you can save X".
"""
from providers.gcp.helpers import fetch_gcp_api, fetch_gcp_api_post

BILLING_BASE = "https://cloudbilling.googleapis.com/v1"
BIGQUERY_BASE = "https://bigquery.googleapis.com/bigquery/v2"


def _bq_table(project_id: str, dataset_id: str, billing_account_id: str, detailed: bool) -> str:
    """BigQuery table name for billing export (dashes in billing id are kept)."""
    suffix = "resource_v1" if detailed else "v1"
    return f"`{project_id}.{dataset_id}.gcp_billing_export_{suffix}_{billing_account_id}`"


async def _query_bigquery(
    project_id: str,
    dataset_id: str,
    billing_account_id: str,
    token: str,
    detailed: bool,
) -> tuple[list[dict], list[dict] | None]:
    """
    Query BigQuery billing export for last 30 days. Returns (top_services, resource_costs).
    resource_costs is None if standard-only export; else list of {resource_key, service, cost}.
    """
    table = _bq_table(project_id, dataset_id, billing_account_id, detailed=False)
    # Top services from standard table (works for both standard and detailed export)
    sql_top = f"""
    SELECT
      COALESCE(service.description, 'Unknown') AS service,
      SUM(cost) AS cost
    FROM {table}
    WHERE project.id = @project_id
      AND usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
      AND (cost_type = 'regular' OR cost_type IS NULL)
    GROUP BY 1
    ORDER BY 2 DESC
    LIMIT 15
    """
    body = {
        "query": sql_top,
        "useLegacySql": False,
        "parameterMode": "NAMED",
        "queryParameters": [{"name": "project_id", "parameterType": {"type": "STRING"}, "parameterValue": {"value": project_id}}],
    }
    url = f"{BIGQUERY_BASE}/projects/{project_id}/queries"
    try:
        result = await fetch_gcp_api_post(url, token, body, "BigQuery")
    except Exception:
        return [], None

    rows = result.get("rows") or []
    top_services = []
    for r in rows:
        f = r.get("f") or []
        top_services.append({"service": f[0].get("v") if len(f) > 0 else "Unknown", "cost": float(f[1].get("v", 0)) if len(f) > 1 else 0})

    resource_costs = None
    if detailed:
        table_res = _bq_table(project_id, dataset_id, billing_account_id, detailed=True)
        sql_res = f"""
        SELECT
          COALESCE(resource.name, resource.global_name, '') AS resource_key,
          COALESCE(service.description, '') AS service,
          SUM(cost) AS cost
        FROM {table_res}
        WHERE project.id = @project_id
          AND usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
          AND (cost_type = 'regular' OR cost_type IS NULL)
        GROUP BY 1, 2
        HAVING SUM(cost) > 0
        """
        body_res = {
            "query": sql_res,
            "useLegacySql": False,
            "parameterMode": "NAMED",
            "queryParameters": [{"name": "project_id", "parameterType": {"type": "STRING"}, "parameterValue": {"value": project_id}}],
        }
        try:
            res_result = await fetch_gcp_api_post(url, token, body_res, "BigQuery")
            rrows = res_result.get("rows") or []
            resource_costs = []
            for r in rrows:
                f = r.get("f") or []
                resource_costs.append({
                    "resource_key": (f[0].get("v") or "").strip(),
                    "service": f[1].get("v") or "",
                    "cost": float(f[2].get("v", 0)) if len(f) > 2 else 0,
                })
        except Exception:
            pass

    return top_services, resource_costs


def _match_resource_cost(rid: str, name: str, resource_costs: list[dict]) -> float:
    """Sum cost from resource_costs rows whose resource_key matches this compute resource (id or name)."""
    total = 0.0
    rid = (rid or "").strip()
    name = (name or "").strip()
    for rc in resource_costs:
        key = (rc.get("resource_key") or "").strip()
        if not key:
            continue
        if key == rid or key == name:
            total += rc.get("cost", 0)
        elif rid and key.endswith("/" + rid):
            total += rc.get("cost", 0)
        elif name and key.endswith("/" + name):
            total += rc.get("cost", 0)
    return total


def _compute_potential_savings(
    compute: list[dict],
    resource_costs: list[dict],
    currency_code: str,
) -> dict | None:
    """
    Given wasted compute resources and per-resource cost from BigQuery detailed export,
    estimate potential savings (so we can say "you can save X").
    """
    if not compute or not resource_costs:
        return None
    by_resource = []
    total = 0.0
    for r in compute:
        reason = r.get("waste_reason")
        if not reason or reason == "none":
            continue
        rid = r.get("id") or ""
        name = r.get("name") or ""
        cost = _match_resource_cost(rid, name, resource_costs)
        if cost <= 0:
            continue
        # Savable fraction: 100% for stopped/unattached/unused; ~30% for wrong-storage-class
        if reason in ("wrong-storage-class",):
            pct = 0.3
        else:
            pct = 1.0
        savable = round(cost * pct, 2)
        total += savable
        by_resource.append({
            "id": rid,
            "name": name,
            "reason": reason,
            "cost": round(cost, 2),
            "savable_pct": int(pct * 100),
            "savable_amount": savable,
        })

    if total <= 0:
        return None
    return {
        "value": round(total, 2),
        "currency": currency_code or "USD",
        "by_resource": by_resource,
    }


async def get_project_billing_info(
    project_id: str,
    token: str,
    *,
    credentials: dict | None = None,
    compute: list[dict] | None = None,
) -> dict:
    """
    Get billing info for the project. If credentials include billing_export_dataset (and
    optionally billing_export_project_id), queries BigQuery for top_services and
    optionally potential_savings from wasted resources. Use billing_export_use_detailed=True
    to query the detailed export table for per-resource cost and savings.
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
            "potential_savings": None,
            "cost_data_available": False,
        }

    billing_account_name = data.get("billingAccountName") or ""
    billing_account_id = billing_account_name.replace("billingAccounts/", "") if billing_account_name else None
    billing_enabled = data.get("billingEnabled", False)

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

    out = {
        "billing_enabled": billing_enabled,
        "billing_account_id": billing_account_id,
        "billing_account_display_name": display_name,
        "currency_code": currency_code or "USD",
        "top_services": [],
        "month_over_month_delta": None,
        "anomalies": [],
        "potential_savings": None,
        "cost_data_available": False,
    }

    creds = credentials or {}
    bq_project = creds.get("billing_export_project_id") or project_id
    bq_dataset = creds.get("billing_export_dataset_id") or creds.get("billing_export_dataset")
    use_detailed = creds.get("billing_export_use_detailed", False)

    if bq_dataset and billing_account_id:
        top_services, resource_costs = await _query_bigquery(bq_project, bq_dataset, billing_account_id, token, use_detailed)
        out["top_services"] = top_services
        out["cost_data_available"] = bool(top_services)
        if compute and resource_costs and currency_code:
            out["potential_savings"] = _compute_potential_savings(compute, resource_costs, currency_code)

    return out
