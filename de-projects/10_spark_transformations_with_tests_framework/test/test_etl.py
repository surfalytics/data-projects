import tempfile
import unittest
from pathlib import Path
from typing import Optional

import importlib_resources
from pyspark.sql import DataFrame
from pyspark.sql.utils import AnalysisException

from app.etl import (
    get_spark,
    load_logs,
    load_experiments,
    load_metrics,
    join_tables,
    filter_late_logs,
    calculate_experiment_final_scores,
    save,
)


class TestETL(unittest.TestCase):
    data_module = "app"

    @classmethod
    def setUpClass(cls) -> None:
        get_spark()
        with importlib_resources.path(cls.data_module, "logs.jsonl") as f:
            logs_path = f
        with importlib_resources.path(cls.data_module, "experiments.csv") as f:
            experiments_path = f
        cls.logs = load_logs(logs_path)
        cls.experiments = load_experiments(experiments_path)
        cls.metrics = load_metrics()
        cls.full_logs = join_tables(cls.logs, cls.experiments, cls.metrics)

    def assertSortedListEqual(
        self, list1: list, list2: list, msg: Optional[str] = None
    ):
        self.assertListEqual(sorted(list1), sorted(list2), msg)

    def assertSetContains(self, set1: set, subset: set, msg: Optional[str] = None):
        if msg is None:
            msg = f"Set {set1} does not contain subset {subset}"
        self.assertTrue(subset.issubset(set1), msg)

    def assertDataFrameEqual(
        self, df1: DataFrame, df2: DataFrame, msg: Optional[str] = None
    ):
        self.assertEqual(
            df1.select(sorted(df1.columns))
            .exceptAll(df2.select(sorted(df2.columns)))
            .count(),
            0,
            msg,
        )

    def test_logs_should_have_valid_number_of_rows(self):
        self.assertEqual(self.logs.count(), 64)

    def test_logs_should_have_valid_column_names(self):
        self.assertSortedListEqual(
            self.logs.columns,
            [
                "logId",
                "expId",
                "metricId",
                "valid",
                "createdAt",
                "ingestedAt",
                "step",
                "value",
            ],
        )

    def test_experiments_should_have_valid_number_of_rows(self):
        self.assertEqual(self.experiments.count(), 4)

    def test_experiments_should_have_valid_column_names(self):
        self.assertSortedListEqual(self.experiments.columns, ["expId", "expName"])

    def test_metrics_should_have_valid_number_of_rows(self):
        self.assertEqual(self.metrics.count(), 2)

    def test_metrics_should_have_valid_column_names(self):
        self.assertSortedListEqual(self.metrics.columns, ["metricId", "metricName"])

    def test_joined_tables_have_valid_number_of_rows(self):
        self.assertEqual(self.full_logs.count(), 64)

    def test_joined_tables_have_valid_column_names(self):
        self.assertSortedListEqual(
            self.full_logs.columns,
            [
                "logId",
                "expId",
                "expName",
                "metricId",
                "metricName",
                "valid",
                "createdAt",
                "ingestedAt",
                "step",
                "value",
            ],
        )

    def test_filtered_late_logs_in_4_hours_have_valid_number_of_rows(self):
        valid_logs = filter_late_logs(self.full_logs, 4)
        self.assertEqual(valid_logs.count(), 7)

    def test_filtered_late_logs_in_4_hours_have_valid_column_names(self):
        valid_logs = filter_late_logs(self.full_logs, 4)
        self.assertSetContains(
            set(valid_logs.columns),
            {
                "logId",
                "expId",
                "expName",
                "metricId",
                "metricName",
                "valid",
                "createdAt",
                "ingestedAt",
                "step",
                "value",
            },
        )

    def test_filtered_late_logs_in_8_hours_have_valid_number_of_rows(self):
        valid_logs = filter_late_logs(self.full_logs, 8)
        self.assertEqual(valid_logs.count(), 11)

    def test_filtered_late_logs_in_8_hours_have_valid_column_names(self):
        valid_logs = filter_late_logs(self.full_logs, 8)
        self.assertSetContains(
            set(valid_logs.columns),
            {
                "logId",
                "expId",
                "expName",
                "metricId",
                "metricName",
                "valid",
                "createdAt",
                "ingestedAt",
                "step",
                "value",
            },
        )

    def test_calculated_experiment_final_scores_have_valid_number_of_rows(self):
        valid_logs = filter_late_logs(self.full_logs, 8)
        final_scores = calculate_experiment_final_scores(valid_logs)
        self.assertEqual(final_scores.count(), 7)

    def test_calculated_experiment_final_scores_have_valid_loss(self):
        valid_logs = filter_late_logs(self.full_logs, 8)
        final_scores = calculate_experiment_final_scores(valid_logs)
        loss = (
            final_scores.select(final_scores.minValue)
            .where(final_scores.expId == 0)
            .where(final_scores.metricName == "Loss")
            .collect()
        )
        self.assertEqual(len(loss), 1)
        self.assertEqual(len(loss[0]), 1)
        self.assertAlmostEqual(loss[0][0], 0.1, places=3)

    def test_calculated_experiment_final_scores_have_valid_accuracy(self):
        valid_logs = filter_late_logs(self.full_logs, 8)
        final_scores = calculate_experiment_final_scores(valid_logs)
        accuracy = (
            final_scores.select(final_scores.minValue)
            .where(final_scores.expId == 2)
            .where(final_scores.metricName == "Accuracy")
            .collect()
        )
        self.assertEqual(len(accuracy), 1)
        self.assertEqual(len(accuracy[0]), 1)
        self.assertAlmostEqual(accuracy[0][0], 0.125, places=3)

    def test_saved_data_is_in_partitioned_parquet_format(self):
        valid_logs = filter_late_logs(self.full_logs, 8)
        final_scores = calculate_experiment_final_scores(valid_logs)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp) / "logs"
            save(final_scores, tmp_path)
            try:
                restored_final_scores = get_spark().read.parquet(str(tmp_path))
            except AnalysisException:
                self.fail("Stored data should not be empty")
            self.assertDataFrameEqual(final_scores, restored_final_scores)
            self.assertEqual(len(list(tmp_path.glob("metricId=*"))), 2)
