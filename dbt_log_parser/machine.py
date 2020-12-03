import dataclasses
import enum
import typing as T

from transitions import Machine, State

from dbt_log_parser.model import DbtLogParser


@dataclasses.dataclass
class Transition:
    trigger: str
    source: str
    dest: str
    conditions: T.List[str]
    unless: T.List[str]
    before: T.List[str]
    after: T.List[str]
    prepare: T.List[str]


class States(enum.Enum):
    SEEK_START = 0
    SEEK_START_SUMMARY = 1
    SEEK_FINISH = 2
    SEEK_DONE = 3
    DONE = 4


def get_machine(model=None):
    if model is None:
        model = DbtLogParser()

    m = Machine(
        model=model,
        states=[
            State(name=State.SEEK_START),
            State(name=State.SEEK_START_SUMMARY),
            State(name=State.SEEK_FINISH),
            State(name=State.SEEK_DONE),
            State(name=State.DONE),
        ],
        transitions=[
            Transition(
                trigger="start_seek_summary",
                source=States.SEEK_START,
                dest=States.SEEK_START_SUMMARY,
                conditions=["found_start"],
                before="read_next_line",
            ),
            Transition(
                trigger="start_seek_finish",
                source=States.SEEK_START_SUMMARY,
                dest=States.SEEK_FINISH,
                conditions=["found_summary"],
                before="read_next_line",
            ),
            Transition(
                trigger="seek_done",
                source=States.SEEK_FINISH,
                dest=States.SEEK_DONE,
                conditions=["found_finish"],
                before="read_next_line",
            ),
            Transition(
                trigger="is_done",
                source=States.SEEK_DONE,
                dest=States.DONE,
                before="report",
            ),
        ],
        initial=States.SEEK_START,
    )

    return m
