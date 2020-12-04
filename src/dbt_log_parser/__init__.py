import argparse
import logging
import typing as T

from dbt_log_parser.parser import DbtLogParser

logging.basicConfig(level=logging.DEBUG)


def parse(
    log_filepath: str = None,
    outfile: str = None,
    write_report: bool = True,
    log_string: str = None,
) -> T.Dict:
    """Parse the dbt log at the given path and generate a report.

    :param log_filepath: Where dbt log exists on disk
    :param outfile: Where to write JSON report to
    :param log_string: String of dbt log text, if not using `log_filepath`
        Takes precedence over log_filepath.
    :param write_report: Whether to write JSON report to disk at all
    :return: Report as dict
    """
    if log_filepath is None and log_string is None:
        raise ValueError("One of log_filepath or log_string must be provided")

    if log_string is not None:
        log_lines = log_string.split("\n")
    elif log_filepath is not None:
        with open(log_filepath, "r") as f:
            log_lines = f.readlines()

    parser = DbtLogParser()

    for line_no, line in enumerate(log_lines):
        if parser.is_done:
            break

        # this method is added to the parser by the state machine
        parser.process_next_line(line=line, line_no=line_no)

    if write_report:
        parser.write_report(outfile)

    return parser.report


def get_parser():
    """Get a parser for pulling CLI arguments."""
    parser = argparse.ArgumentParser(description="DBT log parser")

    args = {
        "log_filepath": dict(flag="--log-filepath", help="Path to dbt log to parse"),
        "outfile": dict(
            flag="--outfile", help="File to write JSON results to", default="out.json"
        ),
        "log_string": dict(
            flag="--log-string",
            help=(
                "dbt log to parse as string. " "Takes precedence over --log-filepath. "
            ),
        ),
    }

    for arg, argspec in args.items():
        flag = argspec.pop("flag")
        parser.add_argument(flag, **argspec)

    return parser


def main():
    """Main CLI entrypoint."""
    parser = get_parser()
    args = parser.parse_args()

    parse(
        log_filepath=args.log_filepath, outfile=args.outfile, log_string=args.log_string
    )


if __name__ == "__main__":
    main()
