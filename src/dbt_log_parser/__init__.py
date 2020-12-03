import argparse
import logging

from dbt_log_parser.parser import DbtLogParser

logging.basicConfig(level=logging.DEBUG)


def parse(log_filepath: str = "dbt.log", outfile: str = "out.json"):
    with open(log_filepath, "r") as f:
        log_lines = f.readlines()

    parser = DbtLogParser()

    for line_no, line in enumerate(log_lines):
        if parser.is_done:
            break

        parser.process_next_line(line=line, line_no=line_no)

    parser.report(outfile)


def get_parser():
    """Get a parser for pulling CLI arguments."""
    parser = argparse.ArgumentParser(description="DBT log parser")

    args = {
        "log_filepath": dict(
            flag="--log-filepath", help="Path to dbt log to parse", default="dbt.log"
        ),
        "outfile": dict(
            flag="--outfile", help="File to write JSON results to", default="out.json"
        ),
    }

    for arg, argspec in args.items():
        flag = argspec.pop("flag")
        parser.add_argument(flag, **argspec)

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    parse(args.log_filepath, args.outfile)


if __name__ == "__main__":
    main()
