"""
General GCP provider helpers — authenticated API fetch; time intervals and
Monitoring API URL building; Compute resource URL parsing (zone, region, machineType);
point value extraction.
"""
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import js
from pyodide.ffi import to_js

MONITORING_BASE = "https://monitoring.googleapis.com/v3"


async def fetch_gcp_api(url: str, token: str, api_name: str = "GCP API") -> dict:
    """
    Fetch a GCP API URL with Bearer token. Returns parsed JSON, or empty dict
    if the response is empty or the API is not enabled. Raises on other API errors.
    """
    resp = await js.fetch(
        url,
        to_js({"headers": {"Authorization": f"Bearer {token}"}}, dict_converter=js.Object.fromEntries),
    )
    raw = await resp.text()
    if not raw.strip():
        return {}

    data = json.loads(raw)
    if "error" in data:
        error_msg = str(data.get("error", {})).lower()
        if "not enabled" in error_msg or "not been used" in error_msg:
            return {}
        raise Exception(f"{api_name} error: {data['error'].get('message', data['error'])}")

    return data


async def fetch_gcp_api_post(url: str, token: str, body: dict, api_name: str = "GCP API") -> dict:
    """POST to a GCP API with JSON body (e.g. BigQuery jobs.query). Returns parsed JSON or raises."""
    opts = {
        "method": "POST",
        "headers": {"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        "body": json.dumps(body),
    }
    resp = await js.fetch(url, to_js(opts, dict_converter=js.Object.fromEntries))
    raw = await resp.text()
    if not raw.strip():
        return {}
    data = json.loads(raw)
    if "error" in data:
        raise Exception(f"{api_name} error: {data['error'].get('message', data['error'])}")
    return data


def interval_endpoints(days: int = 30) -> tuple[str, str]:
    """Return (startTime, endTime) in RFC3339 for the last N days."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    return start.isoformat().replace("+00:00", "Z"), now.isoformat().replace("+00:00", "Z")


def value_from_point(point: dict) -> float:
    """Extract numeric value from a Monitoring API point (doubleValue or distributionValue.mean)."""
    val = point.get("value", {})
    if "doubleValue" in val:
        return float(val["doubleValue"] or 0)
    dist = val.get("distributionValue", {})
    if dist:
        return float(dist.get("mean", 0) or 0)
    return 0.0


def build_ts_url(
    project_name: str,
    metric_filter: str,
    start_time: str,
    end_time: str,
    *,
    per_series_aligner: str = "ALIGN_MEAN",
) -> str:
    """Build Cloud Monitoring timeSeries list URL. Use ALIGN_RATE for DELTA/DISTRIBUTION metrics (e.g. Cloud Run)."""
    return (
        f"{MONITORING_BASE}/{project_name}/timeSeries?"
        f"filter={quote(metric_filter)}&"
        f"interval.startTime={quote(start_time)}&"
        f"interval.endTime={quote(end_time)}&"
        f"aggregation.alignmentPeriod=3600s&"
        f"aggregation.perSeriesAligner={per_series_aligner}"
    )


# --- Compute: extract resource name from GCP resource URLs (zone, region, machineType, etc.) ---


def parse_resource_url(url: str) -> str:
    """Extract the resource name from a full GCP resource URL (e.g. zone, region, machineType)."""
    return url.split("/")[-1] if url else ""
