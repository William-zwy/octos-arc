from capability_judge import judge_round


def test_judge_is_fail_closed_without_acceptance():
    result = judge_round(
        {"invariants": [{}], "capabilities": [{}], "nodes": [{}]},
        source_changed=True,
        build_passed=True,
        readiness_passed=True,
        smoke_passed=True,
        persistence_passed=True,
    )
    assert result["status"] == "inconclusive"
    assert result["official_acceptance_unknown"] is True


def test_judge_flags_readiness_and_missing_contract():
    result = judge_round(
        {},
        source_changed=True,
        build_passed=True,
        readiness_passed=False,
        smoke_passed=False,
        persistence_passed=False,
    )
    assert "readiness" in result["hard_failures"]
    assert "invariants" in result["missing_evidence"]
    assert any("GET /" in item for item in result["recommendations"])
