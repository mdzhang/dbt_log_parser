import logging

from dbt_log_parser.parser import DbtLogParser

logging.basicConfig(level=logging.DEBUG)


def main(log_filepath: str = "dbt.log"):
    with open(log_filepath, "r") as f:
        log_lines = f.readlines()

    parser = DbtLogParser()

    for line_no, line in enumerate(log_lines):
        if parser.is_done:
            break

        parser.process_next_line(line=line, line_no=line_no)

    parser.report()


if __name__ == "__main__":
    main()
