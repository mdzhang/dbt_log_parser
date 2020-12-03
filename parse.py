import json
import logging
import pdb
import pprint
import re

logging.basicConfig(level=logging.DEBUG)


with open("dbt.log", "r") as f:
    log_lines = f.readlines()


DBT_LOG_TEST_PASS_PATTERN = r"\d{2}:\d{2}:\d{2} \| (\d+) of \d+ PASS (\w+)(\.)* .*"
DBT_LOG_TEST_FAIL_PATTERN = (
    r"\d{2}:\d{2}:\d{2} \| (\d+) of \d+ (FAIL|WARN) (\d+) (\w+)(\.)* .*"
)

DBT_LOG_TEST_START_PATTERN = (
    r"\d{2}:\d{2}:\d{2} \| (\d+) of \d+ START test (\w+)(\.)* \[RUN\]"
)

# in case dbt is wrapped in some other service e.g. Airflow, k8s,
# we want to skip any log lines they may add
DBT_LOG_START_PATTERN = "Running with dbt"
found_start = False

# the summary has data about the DAG of models dbt has parsed
DBT_LOG_START_SUMMARY_PATTERN = r"Found (\d+) models, (\d+) tests, (\d+) snapshots, (\d+) analyses, (\d+) macros, (\d+) operations, (\d+) seed files, (\d+) sources"
found_start_summary = False
# once tests are finished running a finish line is logged;
# then error reporting begins
DBT_LOG_FINISH_PATTERN = r"Finished running (\d+) tests in (\d+\.\d+)s"
found_finish = False
# dbt has finished error reporting and is completely done
DBT_LOG_DONE_PATTERN = r"Done. PASS=(\d+) WARN=(\d+) ERROR=(\d+) SKIP=(\d+) TOTAL=(\d+)"
found_done = False

# all the metadata we will extract from the logs will go into this dict
metadata = {}
all_test_metadata = {}
finished_line_no = -1
last_error_detail = {}
has_incomplete_error_detail = False

for line_no, line in enumerate(log_lines):
    if not found_start:
        m = re.search(DBT_LOG_START_PATTERN, line)
        if m is not None:
            logging.info(f"Found starting dbt log line at line {line_no}")
            found_start = True
            continue
        else:
            logging.debug(f"Tossing pre-start line: {line}")

    if found_start and not found_start_summary:
        m = re.search(DBT_LOG_START_SUMMARY_PATTERN, line)
        if m is None:
            msg = (
                "The first line searched when found_start_summary is false should be the summary line!"
                + " But got:\n"
                + line
                + "\ninstead."
            )
            raise Exception(msg)
        else:
            found_start_summary = True
            # maps regex capture group indices to the metadata key to store
            # the extracted value under
            cap_grp_map = {
                1: "models_found",
                2: "tests_found",
                3: "snapshots_found",
                4: "analyses_found",
                5: "macros_found",
                6: "operations_found",
                7: "seeds_found",
                8: "sources_found",
            }

            for cap_grp, key in cap_grp_map.items():
                metadata[key] = int(m.group(cap_grp))

            continue

    if found_start and not found_finish:
        m = re.search(DBT_LOG_TEST_START_PATTERN, line)
        if m is not None:
            logging.debug(f"Tossing test start line: {line}")
            continue

        m = re.search(DBT_LOG_TEST_PASS_PATTERN, line)
        if m is not None:
            logging.debug(f"Found a test pass line: {line}")
            test_metadata = {}
            test_metadata["number"] = int(m.group(1))
            test_metadata["name"] = m.group(2)
            test_metadata["status"] = "PASS"

            # bash ansi escape codes are tricky to unescape if the dbt log
            # has been wrapped by another service that backslash escapes the
            # ansi escapes, so use a simpler match here, instead of adding to
            # DBT_LOG_TEST_PASS_PATTERN
            m2 = re.search(r" in (\d+\.\d+)s\]", line[line.index(m.group(0)) :])
            test_metadata["total_time"] = float(m2.group(1))

            all_test_metadata[test_metadata["name"]] = test_metadata
            continue

        m = re.search(DBT_LOG_TEST_FAIL_PATTERN, line)
        if m is not None:
            logging.debug(f"Found a test fail line: {line}")
            test_metadata = {}
            test_metadata["status"] = m.group(2)
            test_metadata["number"] = int(m.group(3))
            test_metadata["name"] = m.group(4)

            # same comment as above for DBT_LOG_TEST_PASS_PATTERN
            m2 = re.search(r" in (\d+\.\d+)s\]", line[line.index(m.group(0)) :])
            test_metadata["total_time"] = float(m2.group(1))

            all_test_metadata[test_metadata["name"]] = test_metadata
            continue

        m = re.search(DBT_LOG_FINISH_PATTERN, line)
        if m is not None:
            logging.debug(f"Found finish line: {line}")
            found_finish = True
            finished_line_no = line_no
            metadata["tests_run"] = int(m.group(1))
            metadata["tests_runtime_seconds"] = float(m.group(2))
            continue

        logging.debug(f"Tossing unrecognized pre-finish line: {line}")

    if found_finish:
        if has_incomplete_error_detail:
            m = re.search(r"Got (\d+) results?, expected (\d+)", line)
            if m is not None:
                last_error_detail["query_results"] = {
                    "found": int(m.group(1)),
                    "expected": int(m.group(2)),
                }
                continue

            m = re.search(r"compiled SQL at ([\w\.\/]+)\.sql", line)
            if m is not None:
                sql_filepath = m.group(1) + ".sql"

                try:
                    with open(sql_filepath, "r") as f:
                        sql = f.read()
                except FileNotFoundError:
                    sql = None

                last_error_detail["query"] = {
                    "filepath": sql_filepath,
                    "sql": sql,
                    "file_err": True if sql is None else False,
                }

                all_test_metadata[last_error_detail["name"]].update(last_error_detail)
                last_error_detail = {}
                has_incomplete_error_detail = False
                continue

            logging.debug(f"Tossing unrecognized intra error detail line: {line}")
        else:
            m = re.search(r"(Failure|Warning) in test (\w+)", line)

            if m is not None:
                has_incomplete_error_detail = True
                last_error_detail["name"] = m.group(2)
                continue

            m = re.search(DBT_LOG_DONE_PATTERN, line)
            if m is not None:
                metadata["total_passed"] = m.group(1)
                metadata["total_errors"] = m.group(2)
                metadata["total_warnings"] = m.group(3)
                metadata["total_skipped"] = m.group(4)
                break

metadata["tests"] = list(all_test_metadata.values())

with open("out.json", "w") as f:
    json.dump(metadata, f)