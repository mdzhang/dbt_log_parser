import logging
import pdb
import re

logging.basicConfig(level=logging.DEBUG)


with open("dbt.log", "r") as f:
    log_lines = f.readlines()


DBT_LOG_TEST_PASS_PATTERN = r"\d{2}:\d{2}:\d{2} \| (\d+) of \d+ PASS (\w+)(\.)* .*"
DBT_LOG_TEST_FAIL_PATTERN = (
    r"\d{2}:\d{2}:\d{2} \| (\d+) of \d+ FAIL (\d+) (\w+)(\.)* .*"
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

for line_no, line in enumerate(log_lines):
    line = escape_ansi(line)

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
            test_metadata["number"] = int(m.group(1))
            test_metadata["name"] = m.group(3)

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
            metadata["tests_runtime"] = float(m.group(2))
            continue

        logging.debug(f"Tossing unrecognized filler line: {line}")


# special handling for error messages

# TODO: error message parsing
pdb.set_trace()

m = re.search(DBT_LOG_DONE_PATTERN, line)
if m is not None:
    found_complete = True
    metadata["total_passed"] = m.group(1)
    metadata["total_errors"] = m.group(2)
    metadata["total_warnings"] = m.group(3)
    metadata["total_skipped"] = m.group(4)

raise Exception(f"Unrecognized line after done check: {line}")