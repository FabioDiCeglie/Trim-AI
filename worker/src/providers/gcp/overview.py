"""
Overview / dashboard builder — aggregates compute, metrics, and billing into a
single response shaped for the dashboard. All utilization and highlight logic lives here.

Future: requested vs used, trend, request count, cost-based waste score.
"""
# Thresholds for utilization_status (can be made configurable later)
OVER_PROVISIONED_CPU_PCT = 5
OVER_PROVISIONED_RAM_PCT = 10
UNDER_PROVISIONED_CPU_PCT = 80
UNDER_PROVISIONED_RAM_PCT = 90


def _enhance_metrics(metrics_list: list[dict]) -> tuple[list[dict], int, int]:
    """
    Compute avg, peak, and utilization_status per metric item.
    Returns (metrics_enhanced, over_provisioned_count, under_provisioned_count).
    """
    over_provisioned = 0
    under_provisioned = 0
    enhanced = []
    for item in metrics_list:
        points = item.get("metrics") or []
        cpus = [p["cpu_percent"] for p in points if p.get("cpu_percent") is not None]
        rams = [p["ram_percent"] for p in points if p.get("ram_percent") is not None]
        avg_cpu = sum(cpus) / len(cpus) if cpus else None
        avg_ram = sum(rams) / len(rams) if rams else None
        peak_cpu = max(cpus) if cpus else None
        peak_ram = max(rams) if rams else None

        if avg_cpu is not None and avg_cpu < OVER_PROVISIONED_CPU_PCT and (avg_ram is None or avg_ram < OVER_PROVISIONED_RAM_PCT):
            utilization_status = "over_provisioned"
            over_provisioned += 1
        elif (avg_cpu is not None and avg_cpu > UNDER_PROVISIONED_CPU_PCT) or (avg_ram is not None and avg_ram > UNDER_PROVISIONED_RAM_PCT):
            utilization_status = "under_provisioned"
            under_provisioned += 1
        else:
            utilization_status = "ok"

        enhanced.append({
            **item,
            "avg_cpu_percent": round(avg_cpu, 2) if avg_cpu is not None else None,
            "avg_ram_percent": round(avg_ram, 2) if avg_ram is not None else None,
            "peak_cpu_percent": round(peak_cpu, 2) if peak_cpu is not None else None,
            "peak_ram_percent": round(peak_ram, 2) if peak_ram is not None else None,
            "utilization_status": utilization_status,
        })
    return enhanced, over_provisioned, under_provisioned


def _waste_count(compute: list[dict]) -> int:
    """Count compute resources with waste_reason != 'none'."""
    return sum(1 for r in compute if r.get("waste_reason") and r.get("waste_reason") != "none")


def _build_summary(compute: list[dict], metrics_enhanced: list[dict], over_provisioned: int, under_provisioned: int) -> dict:
    waste = _waste_count(compute)
    return {
        "total_resources": len(compute),
        "waste_count": waste,
        "with_metrics": len(metrics_enhanced),
        "over_provisioned": over_provisioned,
        "under_provisioned": under_provisioned,
    }


def _build_summary_cards(summary: dict, billing: dict) -> list[dict]:
    """Cards for dashboard top row: label + value (+ optional sublabel)."""
    return [
        {"id": "total_resources", "label": "Total resources", "value": summary["total_resources"]},
        {"id": "waste_count", "label": "With waste", "value": summary["waste_count"], "sublabel": "stopped, unattached, etc."},
        {"id": "over_provisioned", "label": "Over-provisioned", "value": summary["over_provisioned"], "sublabel": "low CPU/RAM"},
        {"id": "under_provisioned", "label": "Under-provisioned", "value": summary["under_provisioned"], "sublabel": "high CPU/RAM"},
        {"id": "billing", "label": "Billing", "value": billing.get("billing_account_display_name") or "—", "sublabel": billing.get("currency_code") or ""},
    ]


def _build_highlights(compute: list[dict], metrics_enhanced: list[dict]) -> list[dict]:
    """
    Short list of items to show in a dashboard highlights/alerts strip.
    Combines compute waste (stopped, unattached, …) and metrics over/under-provisioned.
    """
    highlights = []
    for r in compute:
        reason = r.get("waste_reason")
        if reason and reason != "none":
            highlights.append({
                "type": "waste",
                "resource_type": r.get("resource_type", ""),
                "id": r.get("id", ""),
                "name": r.get("name", ""),
                "reason": reason,
                "status": r.get("status", ""),
                "recommended_action": r.get("recommended_action", ""),
            })
    for m in metrics_enhanced:
        status = m.get("utilization_status")
        if status in ("over_provisioned", "under_provisioned"):
            highlights.append({
                "type": "utilization",
                "resource_type": m.get("resource_type", ""),
                "id": m.get("id", ""),
                "name": m.get("name", ""),
                "reason": status,
                "avg_cpu_percent": m.get("avg_cpu_percent"),
                "avg_ram_percent": m.get("avg_ram_percent"),
            })
    return highlights


def build_overview(compute: list[dict], metrics_list: list[dict], billing: dict) -> dict:
    """
    Build the full dashboard payload from raw compute, metrics, and billing.
    Response is shaped for the frontend: summary_cards, highlights, compute, metrics, billing.
    """
    metrics_enhanced, over_provisioned, under_provisioned = _enhance_metrics(metrics_list)
    summary = _build_summary(compute, metrics_enhanced, over_provisioned, under_provisioned)
    summary_cards = _build_summary_cards(summary, billing)
    highlights = _build_highlights(compute, metrics_enhanced)

    return {
        "summary": summary,
        "summary_cards": summary_cards,
        "highlights": highlights,
        "compute": compute,
        "metrics": metrics_enhanced,
        "billing": billing,
    }
