"""API tests for analysis endpoints (migrated from stats).

Tests that the 10 non-time-series endpoints are accessible at
/api/v1/experiments/{id}/analysis/* and that old /stats/* paths return 404.
"""

EXP_ID = "exp-grpo-cc"
BASE = "/api/v1/experiments/{}/analysis".format(EXP_ID)
OLD_BASE = "/api/v1/experiments/{}/stats".format(EXP_ID)


# ═══════════════════ Old paths return 404 ═══════════════════


class TestOldStatsPathsReturn404:
    def test_old_convergence_404(self, client):
        r = client.get("{}/convergence".format(OLD_BASE))
        assert r.status_code == 404

    def test_old_efficiency_404(self, client):
        r = client.get("{}/efficiency".format(OLD_BASE))
        assert r.status_code == 404

    def test_old_agent_behavior_404(self, client):
        r = client.get("{}/agent-behavior".format(OLD_BASE))
        assert r.status_code == 404

    def test_old_error_recovery_404(self, client):
        r = client.get("{}/error-recovery".format(OLD_BASE))
        assert r.status_code == 404

    def test_old_reward_quality_404(self, client):
        r = client.get("{}/reward-quality".format(OLD_BASE))
        assert r.status_code == 404

    def test_old_task_effectiveness_404(self, client):
        r = client.get("{}/task-effectiveness".format(OLD_BASE))
        assert r.status_code == 404

    def test_old_scaffold_404(self, client):
        r = client.get("{}/scaffold".format(OLD_BASE))
        assert r.status_code == 404


# ═══════════════════ Analysis endpoints (migrated from stats) ═══════════════════


# NOTE: TestTaskEffectivenessAnalysis removed
# /analysis/task-effectiveness endpoint migrated to frontend TraceQL hook (useTaskEffectiveness)


# TestToolQualityAnalysis and TestToolLatencyAnalysis removed


class TestScaffoldAnalysis:
    def test_scaffold_stats(self, client):
        r = client.get("{}/scaffold".format(BASE))
        assert r.status_code == 200
        data = r.json()["items"]
        assert len(data) == 2  # claude_code, openclaw
        for s in data:
            assert "scaffold" in s
            assert "count" in s
            assert "pass_rate" in s
            assert "max_turns_passed" in s
            assert "avg_turns_passed" in s


# NOTE: TestLanguageAnalysis removed - /analysis/language endpoint deleted
# Language stats now queried via PromQL aggregation
# See test_turn_metrics.py for PromQL metric tests pattern

# NOTE: TestTurnsAnalysis removed - Turn Analysis now uses PromQL metrics
# See test_turn_metrics.py for PromQL metric tests
