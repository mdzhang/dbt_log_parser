from dbt_log_parser.machine import States, get_machine


def main(log_filepath: str = "dbt.log"):
    with open(log_filepath, "r") as f:
        log_lines = f.readlines()

    m = get_machine()

    for line_no, line in enumerate(log_lines):
        if m.state == States.DONE:
            break

        m.process_next_line(line=line, line_no=line_no)

    m.report()


if __name__ == "__main__":
    main()
