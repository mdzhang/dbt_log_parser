import dataclasses
import enum
import typing as T

from transitions import Machine, State


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


def get_machine(model):
    m = Machine(
        model=model,
        states=[
            State(name=States.SEEK_START),
            State(name=States.SEEK_START_SUMMARY),
            State(name=States.SEEK_FINISH),
            State(name=States.SEEK_DONE),
            State(name=States.DONE),
        ],
        initial=States.SEEK_START,
    )

    m.add_ordered_transitions(
        trigger="process_next_line",
        conditions=[
            lambda *args, **kwargs: True,
            "found_start",
            "found_start_summary",
            "found_finish",
            "found_done",
        ],
        prepare=[None, "seek_start", "seek_summary", "seek_finish", "seek_done"],
    )

    return m
