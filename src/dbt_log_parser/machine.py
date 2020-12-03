import dataclasses
import enum
import typing as T

from transitions import Machine, State


@dataclasses.dataclass
class Transition:
    """Lightweight wrapper class for `machine.add_transition` args and kwargs.

    Closely mimics transitions.Transition with the addition of the 'trigger'
    property.
    """

    trigger: str
    source: str
    dest: str
    conditions: T.List[str]
    unless: T.List[str]
    before: T.List[str]
    after: T.List[str]
    prepare: T.List[str]


class States(enum.Enum):
    """All states the parser can be in."""

    SEEK_START = 0
    SEEK_START_SUMMARY = 1
    SEEK_FINISH = 2
    SEEK_DONE = 3
    DONE = 4


def get_machine(model):
    """Create the parser state machine.

    :param model: An instance of DbtLogParser. The state machine will
        mutate the parser after this function is invoked.
    """
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

    # the states above are linear in order; by using `add_ordered_transitions`
    # we automatically make it such that the single trigger `process_next_line`
    # will move linearly between states as ordered above.
    m.add_ordered_transitions(
        trigger="process_next_line",
        # `condition` has a 1:1 mapping with states i.e.
        # we will not transition out of the first state until the first condition
        # is satisfied. conditions correspond to boolean attributes on the model
        # i.e. the parser
        conditions=[
            "found_start",
            "found_start_summary",
            "found_finish",
            "found_done",
            lambda *args, **kwargs: True,
        ],
        # before attempting to transition, the following functions will be
        # invoked with any args or kwargs passed to `process_next_line`;
        # `prepare` occurs before conditions are evaluated;
        # if conditions fail to pass, a transition is halted;
        # in this way, we assure each attempted transition processes another
        # log line
        prepare=["seek_start", "seek_summary", "seek_finish", "seek_done", None],
    )

    return m
