import copy
import json
import logging
import re
import typing as T

from dbt_log_parser.machine import States, get_machine


class LoggingMixin(type):
    """Adds logger that automatically prefixes log lines with module and class name."""

    def __init__(cls, *args):
        super().__init__(*args)

        cls.log = logging.getLogger(f"{__name__}.{cls.__name__}")


class DbtLogParser(metaclass=LoggingMixin):
    def __init__(self):
        """Contains core dbt log parsing logic.

        :param _machine: State machine that will determine which
            instance method to invoke.
        :param found_start: We found the dbt log start line. In case
            the log is wrapped in another service e.g. k8s, Airflow, additional
            non-dbt log lines may appear in the log we want to avoid.
        :param found_start_summary: We found the dbt summary line that describes
            what models, tests, etc. were parsed from the dbt project.
        :param found_finish: dbt finished logging whether tests PASSed, FAILed,
            or WARNed.
        :param found_done: dbt printed its done line. This happens after a finish
            line is logged and after warning and error detail lines are logged.
        :param metadata: Metadata parsed from logs to use to generate report.
        :param all_test_metadata: Test warning/failure details are contained
            here. Keys are test names and values are dicts containing
            test details. See report schema for more.
        :param last_error_detail: Some error details are spread across multiple
            lines. This dict tracks the latest warning/error detail.
        :param has_incomplete_error_detail: True iff we've started parsing
            warning or error details but have not yet finished.
        """
        self._machine = get_machine(model=self)
        self.found_start = False
        self.found_start_summary = False
        self.found_finish = False
        self.found_done = False
        self.metadata = {}
        self.all_test_metadata = {}
        self.last_error_detail = {}
        self.has_incomplete_error_detail = False

    def seek_start(self, line: str, line_no: int):
        """See if the log line is a dbt start line."""
        m = re.search("Running with dbt", line)
        if m is not None:
            self.log.info(f"Found starting dbt log line at line {line_no}")
            self.found_start = True
        else:
            self.log.debug(f"Tossing pre-start line: {line}")

    def seek_summary(self, line: str, line_no: int):
        """See if the log line is a dbt summary line.

        This should normally occur immediately after a dbt start line is found.
        """
        m = re.search("Running with dbt", line)

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
                + " But got:\n"
                + line
                + "\ninstead."
            )
            raise Exception(msg)

    def seek_finish(self, line: str, line_no: int):
        """See if the log line is a dbt finish line.

        Between a start summary and finish line, we may see test START, PASS,
        WARN, or FAIL lines; note those if they occur and add them to
        self.all_test_metadata.
        """
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

            # same comment as above when parsing total_time
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
        """See if the log line is a dbt done line.

        Between a dbt finish and done line, we may see multiline error/warning
        details, so take note of those and merge into their existing entry
        in self.all_test_metadata.
        """
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
                self.last_error_detail = {}
                self.has_incomplete_error_detail = False
                return

            self.log.debug(f"Tossing unrecognized intra error detail line: {line}")
        else:
            m = re.search(r"(Failure|Warning) in test (\w+)", line)

            if m is not None:
                self.has_incomplete_error_detail = True
                self.last_error_detail["name"] = m.group(2)
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

    @property
    def report(self) -> T.Dict:
        """Return a JSON report by merging metadata."""
        if hasattr(self, "_report"):
            return self._report

        report = copy.deepcopy(self.metadata)
        report["tests"] = list(self.all_test_metadata.values())
        self._report = report

        return self._report

    def write_report(self, outfile: str = "out.json"):
        """Write report as JSON to a file on disk."""
        self.metadata["tests"] = list(self.all_test_metadata.values())
        with open(outfile, "w") as f:
            json.dump(self.report, f)
        self.log.info(f"Wrote results to {outfile}.")

    @property
    def is_done(self):
        """Return true if we have encountered the end of a dbt log."""
        return self.state == States.DONE
