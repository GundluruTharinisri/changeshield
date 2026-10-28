SEVERITY_POINTS = {"critical": 25, "major": 15, "minor": 5, "warning": 2, "info": 0}


def risk_score(findings) -> int:
    return min(100, sum(SEVERITY_POINTS.get(f.severity, 0) for f in findings))
