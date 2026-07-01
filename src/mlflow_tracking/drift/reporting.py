"""
reporting.py

Builds the human-readable drift_summary.txt content from a drift report
dict. No MLflow, no data collection -- pure text formatting.
"""

from mlflow_tracking.drift.metrics import fmt


def build_summary_text(report):
    """Human-readable drift_summary.txt content."""
    overall = report.get("overall", {})
    lines = ["Watt Drift Detection Summary", "=" * 29, ""]
    lines.append(f"Overall drift detected: {'YES' if overall.get('drift_detected') else 'NO'}")
    lines.append(f"Alarm count: {overall.get('alarm_count', 0)}")
    lines.append("")

    lines.append("Database count drift:")
    db = report.get("database_count_drift", {})
    if db.get("available"):
        any_table = False
        for section in (db.get("structured", {}), db.get("vector", {})):
            for table, info in section.items():
                any_table = True
                pct = info.get("percent_change")
                status = "ALARM" if info.get("alarm") else "OK"
                if pct is None:
                    lines.append(f"- {table}: unavailable ({info.get('reason', 'no data')})")
                else:
                    sign = "+" if pct >= 0 else ""
                    lines.append(f"- {table} changed by {sign}{pct:.1f}%: {status}")
        if not any_table:
            lines.append("- no tables found")
    else:
        lines.append("- unavailable")
    lines.append("")

    lines.append("Sentiment drift:")
    sd = report.get("sentiment_drift", {})
    if sd.get("available"):
        lines.append(f"- score: {fmt(sd.get('score'))}")
        lines.append(f"- threshold: {sd.get('threshold')}")
        lines.append(f"- status: {'ALARM' if sd.get('alarm') else 'OK'}")
    else:
        lines.append(f"- unavailable: {sd.get('reason')}")
    lines.append("")

    lines.append("Topic drift:")
    td = report.get("topic_drift", {})
    if td.get("available"):
        lines.append(f"- score: {fmt(td.get('score'))}")
        lines.append(f"- threshold: {td.get('threshold')}")
        lines.append(f"- status: {'ALARM' if td.get('alarm') else 'OK'}")
    else:
        lines.append(f"- unavailable because no topic table was found ({td.get('reason')})")
    lines.append("")

    lines.append("Keyword drift:")
    kd = report.get("keyword_drift", {})
    if kd.get("available"):
        lines.append(f"- Jaccard distance: {fmt(kd.get('jaccard_distance'))}")
        lines.append(f"- threshold: {kd.get('threshold')}")
        lines.append(f"- status: {'ALARM' if kd.get('alarm') else 'OK'}")
        lines.append(f"- source: {kd.get('source')}")
    else:
        lines.append(f"- unavailable: {kd.get('reason')}")
    lines.append("")

    lines.append("Retrieval drift:")
    rd = report.get("retrieval_drift", {})
    if rd.get("available"):
        lines.append(f"- zero source rate current: {fmt(rd.get('zero_source_rate_current'))}")
        lines.append(f"- average sources current: {fmt(rd.get('average_sources_current'), '{:.1f}')}")
        lines.append(f"- average latency current: {fmt(rd.get('average_latency_current'), '{:.2f}')}s")
        lines.append(f"- status: {'ALARM' if rd.get('alarm') else 'OK'}")
    else:
        lines.append(f"- unavailable: {rd.get('reason')}")
    lines.append("")

    lines.append("Interpretation:")
    if overall.get("alarm_count", 0) == 0:
        lines.append(
            "No significant drift detected. Current data and retrieval behavior "
            "look consistent with the baseline."
        )
    else:
        readable = ", ".join(a.replace("_", " ") for a in overall.get("alarms", []))
        lines.append(
            f"The system detected noticeable drift in: {readable}. This may mean "
            "newer data or retrieval behavior differs from the baseline and is "
            "worth a manual look."
        )

    return "\n".join(lines)
