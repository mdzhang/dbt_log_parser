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

## Setup

### Requirements

- [HomeBrew](https://brew.sh/)
- [asdf](https://asdf-vm.com/#/core-manage-asdf-vm): `brew install asdf`
  - `asdf` Python plugin: `asdf plugin-add python`

### Steps

- install Python runtime: `asdf install && asdf reshim`
- install Python dependency manager [pipenv](https://pipenv.readthedocs.io/en/latest/): `pip install pipenv`
- create a Pipenv environment specific to this project, and install Python packages, including developer packages: `pipenv install --dev`

## Testing

Uses `pytest`.

```sh
$ pipenv shell
$ pytest tests
```

## Releasing

- update `CHANGELOG.md`
- commit using the title e.g. "[release] v0.1.0a0: Initial release"
- add git tags and push to remote e.g. `./bin/git-tag -v v0.1.1a0 -m "Testing GA release on tag create"`
- let GitHub actions take it from there; see [.github/workflows/release-github.yml](.github/workflows/release-github.yml)

## Hygiene

Abide by the `pre-commit` hook:

```sh
$ pre-commit install
```

Enforced by CI checks.

## Reporting Bugs

Create a [GitHub issue](https://github.com/mdzhang/dbt_log_parser/issues) and use the Bug Report template.
