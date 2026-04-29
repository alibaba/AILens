"""Unit tests for SQL aggregated extractors.

Tests individual SQL extractor functions for correctness and edge cases.

Python 3.6.8 compatible.
"""

from app.metrics.extractors.sql_aggregated import (
    create_sql_aggregated_extractor,
    extract_failed_count_sql,
    extract_passed_count_sql,
    extract_reward_avg_sql,
    extract_reward_stddev_sql,
    extract_trajectory_count_sql,
)


class TestSQLAggregatedExtractors(object):
    """Test individual SQL extractor functions."""

    def test_extract_trajectory_count_sql(self):
        """Test SQL trajectory count extractor."""
        experiment_id = "exp-grpo-cc"
        labels_filter = {}

        result = extract_trajectory_count_sql("test_metric", experiment_id, labels_filter, None)

        assert isinstance(result, list)
        assert len(result) == 1
        assert "metric" in result[0]
        assert "values" in result[0]
        assert result[0]["metric"]["__name__"] == "test_metric"
        assert result[0]["metric"]["experiment_id"] == experiment_id

        # Should have values for multiple iterations
        values = result[0]["values"]
        assert len(values) > 0
        assert all(len(v) == 2 for v in values)  # [iteration_num, count]
        assert all(isinstance(v[0], int) and isinstance(v[1], str) for v in values)

    def test_extract_passed_count_sql(self):
        """Test SQL passed count extractor."""
        experiment_id = "exp-grpo-cc"
        labels_filter = {}

        result = extract_passed_count_sql("test_passed", experiment_id, labels_filter, None)

        assert isinstance(result, list)
        assert len(result) == 1

        # Passed count should be less than or equal to total count
        passed_values = result[0]["values"]

        total_result = extract_trajectory_count_sql("test_total", experiment_id, labels_filter, None)
        total_values = total_result[0]["values"]

        assert len(passed_values) == len(total_values)
        for i, (passed_val, total_val) in enumerate(zip(passed_values, total_values)):
            assert passed_val[0] == total_val[0]  # Same iteration
            assert int(passed_val[1]) <= int(total_val[1])  # Passed <= Total

    def test_extract_failed_count_sql(self):
        """Test SQL failed count extractor."""
        experiment_id = "exp-grpo-cc"
        labels_filter = {}

        # Test that passed + failed = total
        passed_result = extract_passed_count_sql("test_passed", experiment_id, labels_filter, None)
        failed_result = extract_failed_count_sql("test_failed", experiment_id, labels_filter, None)
        total_result = extract_trajectory_count_sql("test_total", experiment_id, labels_filter, None)

        passed_values = passed_result[0]["values"]
        failed_values = failed_result[0]["values"]
        total_values = total_result[0]["values"]

        assert len(passed_values) == len(failed_values) == len(total_values)

        for passed_val, failed_val, total_val in zip(passed_values, failed_values, total_values):
            assert passed_val[0] == failed_val[0] == total_val[0]  # Same iteration
            assert int(passed_val[1]) + int(failed_val[1]) == int(total_val[1])

    def test_extract_reward_avg_sql(self):
        """Test SQL reward average extractor."""
        experiment_id = "exp-grpo-cc"
        labels_filter = {}

        result = extract_reward_avg_sql("test_reward_avg", experiment_id, labels_filter, None)

        assert isinstance(result, list)
        assert len(result) == 1

        values = result[0]["values"]
        assert len(values) > 0

        # All reward averages should be reasonable floats
        for iteration_num, avg_str in values:
            avg_val = float(avg_str)
            assert -1.0 <= avg_val <= 1.0, f"Reward average {avg_val} should be in [-1, 1] range"

    def test_extract_reward_stddev_sql(self):
        """Test SQL reward standard deviation extractor."""
        experiment_id = "exp-grpo-cc"
        labels_filter = {}

        result = extract_reward_stddev_sql("test_reward_stddev", experiment_id, labels_filter, None)

        assert isinstance(result, list)
        assert len(result) == 1

        values = result[0]["values"]
        assert len(values) > 0

        # All standard deviations should be non-negative
        for iteration_num, stddev_str in values:
            stddev_val = float(stddev_str)
            assert stddev_val >= 0, f"Standard deviation {stddev_val} should be non-negative"

    def test_sql_extractor_with_scaffold_filter(self):
        """Test SQL extractors with scaffold filter."""
        experiment_id = "exp-grpo-cc"
        labels_filter = {"scaffold": "claude_code"}

        result = extract_trajectory_count_sql("test_scaffold_filter", experiment_id, labels_filter, None)

        assert len(result) == 1
        assert result[0]["metric"]["scaffold"] == "claude_code"

        # Should still have values
        values = result[0]["values"]
        assert len(values) > 0

    def test_sql_extractor_with_multiple_filters(self):
        """Test SQL extractors with multiple filters."""
        experiment_id = "exp-grpo-cc"
        labels_filter = {"scaffold": "claude_code", "language": "python"}

        result = extract_trajectory_count_sql("test_multi_filter", experiment_id, labels_filter, None)

        assert len(result) == 1
        metric_labels = result[0]["metric"]
        assert metric_labels["scaffold"] == "claude_code"
        assert metric_labels["language"] == "python"

    def test_sql_extractor_with_iteration_range(self):
        """Test SQL extractors with iteration range."""
        experiment_id = "exp-grpo-cc"
        labels_filter = {}
        iteration_range = (1, 5)

        result = extract_trajectory_count_sql("test_range", experiment_id, labels_filter, iteration_range)

        assert len(result) == 1
        values = result[0]["values"]

        # All iterations should be within range
        for iteration_num, count_str in values:
            assert 1 <= iteration_num <= 5

    def test_sql_extractor_with_split_by_scaffold(self):
        """Test SQL extractors with split_by scaffold."""
        experiment_id = "exp-grpo-cc"
        labels_filter = {"split_by": "scaffold"}

        result = extract_trajectory_count_sql("test_split_scaffold", experiment_id, labels_filter, None)

        # Should return multiple series, one per scaffold
        assert len(result) > 1

        scaffolds = set()
        for series in result:
            scaffold = series["metric"].get("scaffold")
            assert scaffold is not None
            scaffolds.add(scaffold)
            assert len(series["values"]) > 0

        assert len(scaffolds) > 1  # Should have multiple scaffolds

    def test_sql_extractor_with_split_by_language(self):
        """Test SQL extractors with split_by language."""
        experiment_id = "exp-grpo-cc"
        labels_filter = {"split_by": "language"}

        result = extract_reward_avg_sql("test_split_language", experiment_id, labels_filter, None)

        # Should return multiple series, one per language
        assert len(result) > 1

        languages = set()
        for series in result:
            language = series["metric"].get("language")
            assert language is not None
            languages.add(language)

        assert len(languages) > 1  # Should have multiple languages

    def test_create_sql_aggregated_extractor_custom(self):
        """Test creating custom SQL aggregated extractors."""
        # Create a MIN extractor for reward
        min_extractor = create_sql_aggregated_extractor("MIN", "reward")

        experiment_id = "exp-grpo-cc"
        labels_filter = {}

        result = min_extractor("test_min_reward", experiment_id, labels_filter, None)

        assert isinstance(result, list)
        assert len(result) == 1

        values = result[0]["values"]
        assert len(values) > 0

        # Get average for comparison
        avg_result = extract_reward_avg_sql("test_avg_reward", experiment_id, labels_filter, None)
        avg_values = avg_result[0]["values"]

        # Min should be <= average for each iteration
        for min_val, avg_val in zip(values, avg_values):
            assert min_val[0] == avg_val[0]  # Same iteration
            assert float(min_val[1]) <= float(avg_val[1])

    def test_sql_extractor_empty_experiment(self):
        """Test SQL extractors with non-existent experiment."""
        experiment_id = "non-existent-exp"
        labels_filter = {}

        result = extract_trajectory_count_sql("test_empty", experiment_id, labels_filter, None)

        # Should return empty list for non-existent experiment
        assert result == []

    def test_sql_extractor_edge_case_filters(self):
        """Test SQL extractors with edge case filters."""
        experiment_id = "exp-grpo-cc"

        # Test with non-existent scaffold
        labels_filter = {"scaffold": "non-existent-scaffold"}
        result = extract_trajectory_count_sql("test_no_match", experiment_id, labels_filter, None)

        # Should return empty or minimal results
        assert isinstance(result, list)
        # In mock environment, might return empty results
        if result:
            assert len(result[0]["values"]) == 0 or len(result) == 0
