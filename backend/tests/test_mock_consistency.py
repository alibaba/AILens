"""Mock data consistency tests — validates invariants of generated data.

T-TEST-02: >= 15 test cases verifying foreign-key integrity,
enum validity, numeric consistency, and data completeness.

Python 3.6.8 compatible.
"""


# ═══════════════════ 1. Foreign Key Integrity (5 cases) ═══════════════════


class TestForeignKeyIntegrity:
    """Every FK reference in mock data points to an existing entity."""

    def test_trajectory_task_id_exists(self, mock_store):
        """All trajectory.task_id values point to existing tasks."""
        task_ids = set(t["id"] for t in mock_store.tasks)
        for traj in mock_store.trajectories:
            assert traj["task_id"] in task_ids, "trajectory {} references missing task {}".format(
                traj["id"], traj["task_id"]
            )

    def test_trajectory_experiment_id_exists(self, mock_store):
        """All trajectory.experiment_id values point to existing experiments."""
        exp_ids = set(e["id"] for e in mock_store.experiments)
        for traj in mock_store.trajectories:
            assert traj["experiment_id"] in exp_ids, "trajectory {} references missing experiment {}".format(
                traj["id"], traj["experiment_id"]
            )

    def test_trajectory_iteration_id_exists(self, mock_store):
        """All trajectory.iteration_id values point to existing iterations."""
        all_iter_ids = set()
        for iters in mock_store.iterations.values():
            for it in iters:
                all_iter_ids.add(it["id"])
        for traj in mock_store.trajectories:
            assert traj["iteration_id"] in all_iter_ids, "trajectory {} references missing iteration {}".format(
                traj["id"], traj["iteration_id"]
            )

    def test_experiment_project_id_exists(self, mock_store):
        """All experiment.project_id values point to existing projects."""
        project_ids = set(p["id"] for p in mock_store.projects)
        for exp in mock_store.experiments:
            assert exp["project_id"] in project_ids, "experiment {} references missing project {}".format(
                exp["id"], exp["project_id"]
            )


# ═══════════════════ 2. Enum Value Validity (3 cases) ═══════════════════


class TestEnumValidity:
    """Enum/categorical fields contain only legal values."""

    def test_trajectory_scaffold_in_experiment(self, mock_store):
        """trajectory.scaffold is in the parent experiment's scaffolds list."""
        exp_map = {}
        for exp in mock_store.experiments:
            exp_map[exp["id"]] = exp["config"]["scaffolds"]
        for traj in mock_store.trajectories:
            scaffolds = exp_map.get(traj["experiment_id"], [])
            assert traj["scaffold"] in scaffolds, (
                "trajectory {} scaffold '{}' not in experiment {} scaffolds {}".format(
                    traj["id"],
                    traj["scaffold"],
                    traj["experiment_id"],
                    scaffolds,
                )
            )

    def test_trajectory_outcome_legal(self, mock_store):
        """trajectory.outcome is one of the defined outcomes."""
        valid_outcomes = {"success", "failure", "timeout", "error"}
        for traj in mock_store.trajectories:
            assert traj["outcome"] in valid_outcomes, "trajectory {} has invalid outcome '{}'".format(
                traj["id"], traj["outcome"]
            )

    def test_experiment_status_legal(self, mock_store):
        """experiment.status is one of the defined statuses."""
        valid_statuses = {"running", "completed", "failed", "cancelled"}
        for exp in mock_store.experiments:
            assert exp["status"] in valid_statuses, "experiment {} has invalid status '{}'".format(
                exp["id"], exp["status"]
            )


# ═══════════════════ 3. Numeric Consistency (4 cases) ═══════════════════


class TestNumericConsistency:
    """Numeric fields maintain expected relationships."""

    def test_total_tokens_equals_sum(self, mock_store):
        """total_tokens == input_tokens + output_tokens (exact)."""
        for traj in mock_store.trajectories:
            expected = traj["input_tokens"] + traj["output_tokens"]
            assert traj["total_tokens"] == expected, "trajectory {}: total_tokens {} != {} + {}".format(
                traj["id"],
                traj["total_tokens"],
                traj["input_tokens"],
                traj["output_tokens"],
            )

    def test_reward_components_keys_match(self, mock_store):
        """trajectory.reward_components keys == experiment.config.reward_components."""
        exp_map = {}
        for exp in mock_store.experiments:
            exp_map[exp["id"]] = set(exp["config"]["reward_components"])
        for traj in mock_store.trajectories:
            expected_keys = exp_map.get(traj["experiment_id"], set())
            actual_keys = set(traj["reward_components"].keys())
            assert actual_keys == expected_keys, "trajectory {} reward_components keys {} != expected {}".format(
                traj["id"], actual_keys, expected_keys
            )

    def test_iteration_nums_consecutive(self, mock_store):
        """iteration_num values within each experiment are 1, 2, 3, ..., N."""
        for exp_id, iters in mock_store.iterations.items():
            nums = sorted(it["iteration_num"] for it in iters)
            expected = list(range(1, len(nums) + 1))
            assert nums == expected, "experiment {} iteration_nums {} not consecutive 1..{}".format(
                exp_id, nums, len(nums)
            )

    def test_total_events_gte_total_turns(self, mock_store):
        """total_turns > 0 and total_events >= total_turns for all trajectories."""
        for traj in mock_store.trajectories:
            assert traj["total_turns"] > 0, "trajectory {} has total_turns == 0".format(traj["id"])
            assert traj["total_events"] >= traj["total_turns"], (
                "trajectory {}: total_events {} < total_turns {}".format(
                    traj["id"],
                    traj["total_events"],
                    traj["total_turns"],
                )
            )


# ═══════════════════ 4. Data Completeness (3 cases) ═══════════════════


class TestDataCompleteness:
    """Every entity has child records — no orphaned parents."""

    def test_every_experiment_has_iterations(self, mock_store):
        """Each experiment has at least 1 iteration."""
        for exp in mock_store.experiments:
            iters = mock_store.iterations.get(exp["id"], [])
            assert len(iters) >= 1, "experiment {} has no iterations".format(exp["id"])

    def test_every_iteration_has_trajectories(self, mock_store):
        """Each iteration has at least 1 trajectory."""
        # Build iteration_id → trajectory count
        iter_traj_count = {}
        for traj in mock_store.trajectories:
            iid = traj["iteration_id"]
            iter_traj_count[iid] = iter_traj_count.get(iid, 0) + 1

        for exp_id, iters in mock_store.iterations.items():
            for it in iters:
                count = iter_traj_count.get(it["id"], 0)
                assert count >= 1, "iteration {} (exp {}) has no trajectories".format(it["id"], exp_id)

    def test_every_project_has_experiments(self, mock_store):
        """Each original project has at least 1 experiment.

        Note: dynamically-created projects (e.g. from test_create_project)
        are excluded — they are not part of the seed data invariant.
        """
        # Original project IDs from _PROJECT_DEFS
        original_project_ids = {"proj-code-agent-v2", "proj-reasoning"}

        proj_exp_count = {}
        for exp in mock_store.experiments:
            pid = exp["project_id"]
            proj_exp_count[pid] = proj_exp_count.get(pid, 0) + 1

        for proj in mock_store.projects:
            if proj["id"] not in original_project_ids:
                continue
            count = proj_exp_count.get(proj["id"], 0)
            assert count >= 1, "project {} has no experiments".format(proj["id"])
