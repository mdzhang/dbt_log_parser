import json
import logging
import re


class LoggingMixin:
    def __init__(self):
        self.log = logging.getLogger(f"dbt_log_parser.{__name__}")


class DbtLogParser(LoggingMixin):
    def __init__(self):
        super().__init__()

        self.found_start = False
        self.found_start_summary = False
        self.found_finish = False
        self.found_done = False
        self.metadata = {}
        self.all_test_metadata = {}
        self.last_error_detail = {}
        self.has_incomplete_error_detail = False

        # TODO: reader

    def seek_start(self, line: str, line_no: int):
        m = re.search("Running with dbt", line)
        if m is not None:
            self.log.info(f"Found starting dbt log line at line {line_no}")
            self.found_start = True
        else:
            self.log.debug(f"Tossing pre-start line: {line}")

    def seek_summary(self, line: str, line_no: int):
        m = re.search(
            r"Found (\d+) models, (\d+) tests, (\d+) snapshots, (\d+) analyses, "
            + r"(\d+) macros, (\d+) operations, (\d+) seed files, (\d+) sources",
            line,
        )

        if m is not None:
            self.found_start_summary = True
            # maps regex capture group indices to the metadata key
            # to store the extracted value under
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
                self.metadata[key] = int(m.group(cap_grp))
        else:
            msg = (
                "The first line searched when found_start_summary "
                + "is false should be the summary line!"
                + +" But got:\n"
                + line
                + "\ninstead."
            )
            raise Exception(msg)

    def seek_finish(self, line: str, line_no: int):
        m = re.search(
            r"\d{2}:\d{2}:\d{2} \| (\d+) of \d+ START test (\w+)(\.)* \[RUN\]", line
        )
        if m is not None:
            self.log.debug(f"Tossing test start line: {line}")
            return

        m = re.search(r"\d{2}:\d{2}:\d{2} \| (\d+) of \d+ PASS (\w+)(\.)* .*", line)
        if m is not None:
            self.log.debug(f"Found a test pass line: {line}")
            test_metadata = {}
            test_metadata["number"] = int(m.group(1))
            test_metadata["name"] = m.group(2)
            test_metadata["status"] = "PASS"

            # bash ansi escape codes are tricky to unescape if the dbt log
            # has been wrapped by another service that backslash escapes the
            # ansi escapes, so use a simpler match here, instead of adding to
            # original regex
            m2 = re.search(r" in (\d+\.\d+)s\]", line[line.index(m.group(0)) :])
            test_metadata["total_time"] = float(m2.group(1))

            self.all_test_metadata[test_metadata["name"]] = test_metadata
            return

        m = re.search(
            r"\d{2}:\d{2}:\d{2} \| (\d+) of \d+ (FAIL|WARN) (\d+) (\w+)(\.)* .*", line
        )
        if m is not None:
            self.log.debug(f"Found a test fail line: {line}")
            test_metadata = {}
            test_metadata["status"] = m.group(2)
            test_metadata["number"] = int(m.group(3))
            test_metadata["name"] = m.group(4)

            # same comment as above for DBT_LOG_TEST_PASS_PATTERN
            m2 = re.search(r" in (\d+\.\d+)s\]", line[line.index(m.group(0)) :])
            test_metadata["total_time"] = float(m2.group(1))

            self.all_test_metadata[test_metadata["name"]] = test_metadata
            return

        m = re.search(r"Finished running (\d+) tests in (\d+\.\d+)s", line)
        if m is not None:
            self.log.debug(f"Found finish line: {line}")
            self.found_finish = True
            self.metadata["tests_run"] = int(m.group(1))
            self.metadata["tests_runtime_seconds"] = float(m.group(2))
            return

        self.log.debug(f"Tossing unrecognized pre-finish line: {line}")

    def seek_done(self, line: str, line_no: int):
        if self.has_incomplete_error_detail:
            m = re.search(r"Got (\d+) results?, expected (\d+)", line)
            if m is not None:
                self.last_error_detail["query_results"] = {
                    "found": int(m.group(1)),
                    "expected": int(m.group(2)),
                }
                return

            m = re.search(r"compiled SQL at ([\w\.\/]+)\.sql", line)
            if m is not None:
                sql_filepath = m.group(1) + ".sql"

                try:
                    with open(sql_filepath, "r") as f:
                        sql = f.read()
                except FileNotFoundError:
                    sql = None

                self.last_error_detail["query"] = {
                    "filepath": sql_filepath,
                    "sql": sql,
                    "file_err": True if sql is None else False,
                }

                self.all_test_metadata[self.last_error_detail["name"]].update(
                    self.last_error_detail
                )
                last_error_detail = {}
                self.has_incomplete_error_detail = False
                return

            self.log.debug(f"Tossing unrecognized intra error detail line: {line}")
        else:
            m = re.search(r"(Failure|Warning) in test (\w+)", line)

            if m is not None:
                self.has_incomplete_error_detail = True
                last_error_detail["name"] = m.group(2)
                return

            m = re.search(
                r"Done. PASS=(\d+) WARN=(\d+) ERROR=(\d+) SKIP=(\d+) TOTAL=(\d+)", line
            )
            if m is not None:
                self.metadata["total_passed"] = m.group(1)
                self.metadata["total_errors"] = m.group(2)
                self.metadata["total_warnings"] = m.group(3)
                self.metadata["total_skipped"] = m.group(4)
                self.found_done = True

    def report(self):
        self.metadata["tests"] = list(self.all_test_metadata.values())
        with open("out.json", "w") as f:
            json.dump(self.metadata, f)
