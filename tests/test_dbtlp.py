import json
import os

from jsonschema import validate

from dbt_log_parser import parse


def test_sample_log():
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    log_filepath = os.path.join(cur_dir, "./fixtures/simple_case/sample.log")

    actual_report = parse(log_filepath=log_filepath, write_report=False)

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
