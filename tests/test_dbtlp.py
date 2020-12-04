import json
import os

import pytest
from jsonschema import validate

from dbt_log_parser import parse
from dbt_log_parser.parser import DbtLogParser

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_sample_log():
    """Parse works as expected on a representative dbt log."""
    log_filepath = os.path.join(cur_dir, "./fixtures/simple_case/sample.log")
    actual_report = parse(
        log_filepath=log_filepath, outfile="test-out.json", write_report=True
    )

    report_path = os.path.join(cur_dir, "./fixtures/simple_case/sample.json")
    with open(report_path, "r") as f:
        expected_report = json.load(f)

    assert expected_report == actual_report

    schema_path = os.path.join(
        os.path.abspath(os.path.dirname(cur_dir)), "./schemas/report.json"
    )
    with open(schema_path, "r") as f:
        schema = json.load(f)

    validate(instance=actual_report, schema=schema)


def test_cached_attrs():
    """Raises code coverage of our test suite by accessing cached attributes."""
    parser = DbtLogParser()
    parser.report
    parser.report


def test_failure_pre_summary_line():
    """Parse should fail on unexpected post-start pre-summary line."""
    log_filepath = os.path.join(cur_dir, "./fixtures/pre_summary_line/sample.log")

    with pytest.raises(Exception) as excinfo:
        parse(log_filepath=log_filepath, write_report=False)

    assert "I SHOULDN'T BE HERE" in str(excinfo.value)
    assert (
        "The first line searched when found_start_summary "
        "is false should be the summary line!"
    ) in str(excinfo.value)


def test_parse_string():
    """Parse should work as expected when `log_string` provided."""
    log_filepath = os.path.join(cur_dir, "./fixtures/simple_case/sample.log")
    with open(log_filepath, "r") as f:
        log_string = f.read()

    actual_report = parse(log_string=log_string, write_report=False)

    report_path = os.path.join(cur_dir, "./fixtures/simple_case/sample.json")
    with open(report_path, "r") as f:
        expected_report = json.load(f)

    assert expected_report == actual_report
