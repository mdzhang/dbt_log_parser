# dbt log parser

Python package and CLI tool for parsing structured (JSON) data from a dbt log.

## Table of Contents

* [Generated Report](#generated-report)
* [Usage](#usage)
  + [CLI](#cli)
  + [API](#api)
* [Contributing](#contributing)

## Generated Report

Example report structure:

```json
{
    "models_found": 469,
    "tests_found": 1658,
    "snapshots_found": 0,
    "analyses_found": 0,
    "macros_found": 300,
    "operations_found": 0,
    "seeds_found": 0,
    "sources_found": 204,
    "tests_run": 1100,
    "tests_runtime_seconds": 97.47,
    "tests": [
        {
            "number": 1,
            "name": "accepted_values_dim_order_state_open",
            "status": "PASS",
            "total_time": 2.11
        },
        {
            "status": "WARN",
            "number": 2,
            "name": "relationships_fact_contribution_goal_updates_contribution_page_id__contribution_page_id__ref_dim_contribution_page_",
            "total_time": 1.73,
            "query_results": {
                "found": 5,
                "expected": 0
            },
            "query": {
                "filepath": "target/compiled/core/schema_test/relationships_fact_contribution_goal_updates_34dae512835158ed459182c173a8c127.sql",
                "sql": null,
                "file_err": true
            }
        },
        {
            "status": "FAIL",
            "number": 548326,
            "name": "unique_int_home_page_display_resources_you_may_like_event_user_id",
            "total_time": 1.16,
            "query_results": {
                "found": 548326,
                "expected": 0
            },
            "query": {
                "filepath": "target/compiled/core/schema_test/unique_int_home_page_display_resources_you_may_like_event_user_id.sql",
                "sql": null,
                "file_err": true
            }
        }
    ]
}
```

See more in the [JSON schema](./schemas/report.json).

## Usage

### CLI

```sh
$ dbtlp --help
usage: dbtlp [-h] [--log-filepath LOG_FILEPATH] [--outfile OUTFILE]

DBT log parser

optional arguments:
  -h, --help            show this help message and exit
  --log-filepath LOG_FILEPATH
                        Path to dbt log to parse
  --outfile OUTFILE     File to write JSON results to
$ dbtlp --log-filepath dbt.log --outfile results.json
```

### API

```python
from dbt_log_parser import parse

report = parse(log_filepath='dbt.log', write_report=False)
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)
