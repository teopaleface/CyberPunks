"""Reject unsupported claims, stale versions and incomplete coverage."""

from .queue_analysis import analyze_queue


def validate_analysis(context, analysis):
    # Canonical deterministic reconstruction validates every copied value and derived total.
    if analysis != analyze_queue(context):
        raise ValueError("Analysis differs from authorized snapshot evidence")
