"""Dovezile trebuie să semnaleze cifrele raportate care nu corespund predicțiilor."""
from copy import deepcopy

from cyberpunks.benchmark import evidence as E


def test_modified_report_is_detected_from_independent_predictions(monkeypatch):
    original = E.load

    def changed(path):
        report = original(path)
        if path.name == "bilant_v2.json":
            report = deepcopy(report)
            report["catboost"]["test"]["macro_f1"] += .1
        return report

    monkeypatch.setattr(E, "load", changed)
    checks, _ = E.verify_predictions()
    failures = [c["check"] for c in checks if not c["passed"]]
    assert failures == ["bilant_v2/catboost/macro_f1"]


def test_nonfinite_metric_cannot_pass():
    assert not E.compare("invalid", .5, float("nan"))["passed"]
