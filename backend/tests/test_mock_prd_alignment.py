# -*- coding: utf-8 -*-
"""Mock data PRD alignment tests — verifies mock data conforms to PRD rules.

Checks that generated mock data correctly represents the domain model
described in PRD v0.8.2 Section 5.1.  Python 3.6.8 compatible.
"""

import pytest
from app.mock import store


@pytest.fixture(scope="module")
def ms():
    """Initialized mock store."""
    store._ensure_init()
    return store


# ═══════════════════ Experiment Config Alignment ═══════════════════


class TestExperimentConfigAlignment:
    def test_scaffolds_at_least_two_in_some_experiments(self, ms):
        """PRD: experiments can use multiple scaffolds."""
        exps = ms.get_experiments()
        multi_scaffold = [e for e in exps if len(e["config"]["scaffolds"]) >= 2]
        assert len(multi_scaffold) >= 1, "At least one experiment should have >= 2 scaffolds"

    def test_reward_components_include_required(self, ms):
        """PRD: reward_components includes task/format/efficiency."""
        exps = ms.get_experiments()
        required = {"task", "format", "efficiency"}
        for exp in exps:
            components = set(exp["config"]["reward_components"])
            assert required.issubset(components), "Experiment {} missing reward components: {}".format(
                exp["id"], required - components
            )


# ═══════════════════ Trajectory Alignment ═══════════════════


class TestTrajectoryAlignment:
    def test_reward_components_match_experiment_config(self, ms):
        """trajectory.reward_components keys == experiment.config.reward_components."""
        exps = ms.get_experiments()
        exp_map = {}
        for exp in exps:
            exp_map[exp["id"]] = set(exp["config"]["reward_components"])

        trajs = ms.trajectories[:50]  # sample
        for traj in trajs:
            expected = exp_map.get(traj["experiment_id"], set())
            actual = set(traj["reward_components"].keys())
            assert actual == expected, "Trajectory {} reward_components {} != {}".format(traj["id"], actual, expected)

    def test_scaffold_in_experiment_config(self, ms):
        """trajectory.scaffold must be one of experiment.config.scaffolds."""
        exps = ms.get_experiments()
        exp_scaffolds = {}
        for exp in exps:
            exp_scaffolds[exp["id"]] = set(exp["config"]["scaffolds"])

        trajs = ms.trajectories[:100]
        for traj in trajs:
            allowed = exp_scaffolds.get(traj["experiment_id"], set())
            assert traj["scaffold"] in allowed, "Trajectory {} scaffold '{}' not in experiment scaffolds {}".format(
                traj["id"], traj["scaffold"], allowed
            )

    def test_outcome_values_valid(self, ms):
        """outcome must be one of success/failure/timeout/error."""
        valid = {"success", "failure", "timeout", "error"}
        for traj in ms.trajectories[:200]:
            assert traj["outcome"] in valid

    def test_passed_correlates_with_outcome(self, ms):
        """passed=True only when outcome=success."""
        for traj in ms.trajectories[:200]:
            if traj["passed"]:
                assert traj["outcome"] == "success"

    def test_tokens_consistency(self, ms):
        """total_tokens == input_tokens + output_tokens."""
        for traj in ms.trajectories[:100]:
            assert traj["total_tokens"] == traj["input_tokens"] + traj["output_tokens"]

    def test_tokens_per_turn_computed(self, ms):
        """tokens_per_turn approx total_tokens / total_turns."""
        for traj in ms.trajectories[:50]:
            expected = round(traj["total_tokens"] / traj["total_turns"], 1)
            assert abs(traj["tokens_per_turn"] - expected) < 0.2


# ═══════════════════ Turn/Event Alignment ═══════════════════


class TestTurnEventAlignment:
    def test_event_order_reasoning_action_observation(self, ms):
        """Within each Turn, events follow reasoning -> action -> observation."""
        trajs = ms.trajectories[:5]
        for traj in trajs:
            turns = ms.get_turns(traj["id"])
            for turn in turns:
                events = turn["events"]
                types = [e["type"] for e in events]
                assert types == ["reasoning", "action", "observation"], "Turn {} has wrong event order: {}".format(
                    turn["id"], types
                )

    def test_reasoning_event_has_llm_data(self, ms):
        """Event type=reasoning => llm field is populated."""
        traj = ms.trajectories[0]
        turns = ms.get_turns(traj["id"])
        for turn in turns[:3]:
            for ev in turn["events"]:
                if ev["type"] == "reasoning":
                    assert ev["llm"] is not None
                    assert "prompt_tokens" in ev["llm"]
                    assert "completion_tokens" in ev["llm"]
                    assert "model" in ev["llm"]
                    assert "latency_ms" in ev["llm"]

    def test_action_event_has_action_data(self, ms):
        """Event type=action => action field is populated."""
        traj = ms.trajectories[0]
        turns = ms.get_turns(traj["id"])
        for turn in turns[:3]:
            for ev in turn["events"]:
                if ev["type"] == "action":
                    assert ev["action"] is not None
                    assert "tool_name" in ev["action"]
                    assert "tool_input" in ev["action"]
                    assert "tool_output" in ev["action"]
                    assert "status" in ev["action"]

    def test_observation_event_has_observation_data(self, ms):
        """Event type=observation => observation field is populated."""
        traj = ms.trajectories[0]
        turns = ms.get_turns(traj["id"])
        for turn in turns[:3]:
            for ev in turn["events"]:
                if ev["type"] == "observation":
                    assert ev["observation"] is not None
                    assert "content" in ev["observation"]
                    assert "reward" in ev["observation"]

    def test_turn_num_sequential(self, ms):
        """turn_num starts at 1 and is sequential."""
        traj = ms.trajectories[0]
        turns = ms.get_turns(traj["id"])
        nums = [t["turn_num"] for t in turns]
        assert nums == list(range(1, len(nums) + 1))

    def test_event_num_sequential_within_turn(self, ms):
        """event_num starts at 1 and is sequential within a turn."""
        traj = ms.trajectories[0]
        turns = ms.get_turns(traj["id"])
        for turn in turns[:5]:
            nums = [e["event_num"] for e in turn["events"]]
            assert nums == list(range(1, len(nums) + 1))


# ═══════════════════ Annotation Alignment ═══════════════════


class TestAnnotationAlignment:
    VALID_PATTERNS = {
        "action_loop",
        "tool_error",
        "timeout",
        "token_explosion",
        "ineffective_action",
        "early_abandon",
        "repeat_error",
    }

    def test_annotation_pattern_type_valid(self, ms):
        """pattern_type must be one of the 7 PRD-defined types."""
        annotations = ms.get_annotations()
        assert len(annotations) > 0
        for ann in annotations:
            assert ann["pattern_type"] in self.VALID_PATTERNS, "Invalid pattern_type: {}".format(ann["pattern_type"])

    def test_annotation_has_required_fields(self, ms):
        """Each annotation has id, trajectory_id, experiment_id, etc."""
        required = [
            "id",
            "trajectory_id",
            "experiment_id",
            "pattern_type",
            "description",
            "affected_turns",
            "severity",
        ]
        annotations = ms.get_annotations()
        for ann in annotations[:20]:
            for field in required:
                assert field in ann, "Annotation missing field: {}".format(field)

    def test_annotation_severity_valid(self, ms):
        """severity must be warning or error."""
        annotations = ms.get_annotations()
        valid_sev = {"warning", "error"}
        for ann in annotations[:50]:
            assert ann["severity"] in valid_sev

    def test_annotation_affected_turns_nonempty(self, ms):
        """affected_turns should be a non-empty list of ints."""
        annotations = ms.get_annotations()
        for ann in annotations[:20]:
            at = ann["affected_turns"]
            assert isinstance(at, list)
            assert len(at) > 0
            for t in at:
                assert isinstance(t, int)


# ═══════════════════ Data Volume Checks ═══════════════════


class TestDataVolume:
    """PRD data scale requirements."""

    def test_at_least_two_projects(self, ms):
        assert len(ms.get_projects()) >= 2

    def test_six_experiments(self, ms):
        assert len(ms.get_experiments()) == 6

    def test_fifty_iterations_per_experiment(self, ms):
        for exp in ms.get_experiments():
            iters = ms.get_iterations(exp["id"])
            assert len(iters) == 50, "Experiment {} has {} iterations (expected 50)".format(exp["id"], len(iters))

    def test_hundred_trajectories_per_iteration(self, ms):
        exp = ms.get_experiments()[0]
        iters = ms.get_iterations(exp["id"])
        # Check first iteration has ~100 trajectories
        trajs = [t for t in ms.trajectories if t["iteration_id"] == iters[0]["id"]]
        assert len(trajs) == 100

    def test_annotations_exist_for_failed_trajectories(self, ms):
        annotations = ms.get_annotations()
        assert len(annotations) > 0
        # All annotated trajectories should be non-success
        annotated_traj_ids = set(a["trajectory_id"] for a in annotations)
        traj_map = {}
        for t in ms.trajectories:
            traj_map[t["id"]] = t
        for tid in list(annotated_traj_ids)[:50]:
            traj = traj_map.get(tid)
            if traj:
                assert traj["outcome"] != "success", "Annotation on successful trajectory {}".format(tid)
