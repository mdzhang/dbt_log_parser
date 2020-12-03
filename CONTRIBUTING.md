# Contributing

## Bird's Eye View

This package presently works by reading in a log file, and iteratively parsing lines. This is orchestrated by a primary `DbtLogParser` class.

`dbt` logs are structured in that they have distinct text patterns that demarcate where dbt logging starts, when it's logging that tests have started or have passed/failed, when it logs additional failure/warning details, and when it logs a full summary.

Each of these stages are implemented as stages in a [state machine](https://en.wikipedia.org/wiki/Finite-state_machine), and depending on which stage the process is in, different methods on a `DbtLogParser` will be invoked.

The `DbtLogParser` maintains internal state that is used to eventually generate the final report.

## Where to start

See the [`main` function here](./src/dbt_log_parser/__init__.py).

## Also Useful

The `DbtLogParser` heavily uses, or expects to be used by, the state machine class from [`pytransitions`](https://github.com/pytransitions/transitions), so reading the Quick Start on that package is advised.

## Testing

TODO

## Releasing

- update CHANGELOG.md
- ensure you have the [GitHub CLI](https://github.com/cli/cli) installed
- ensure `$PYPI_USER` and `$PYPI_PASSWORD` environment variables are set
- run `bin/release`

## Hygiene

Using the [`black`](https://github.com/psf/black) code formatter is advised.

## Reporting Bugs

TODO
