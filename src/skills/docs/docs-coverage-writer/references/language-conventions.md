# Language Conventions

Test framework patterns by language. Use this to locate and interpret test files during Phase 1 scanning.

## Python

| Convention | Pattern |
|---|---|
| Framework | pytest (primary), unittest |
| Test files | `test_*.py`, `*_test.py` |
| Test directories | `tests/`, `test/` |
| Test functions | `test_*`, methods in `Test*` classes |
| Fixtures | `conftest.py` (not tests themselves — skip during scanning) |
| Run command | `pytest tests/ -v` |

## SystemVerilog / UVM

| Convention | Pattern |
|---|---|
| Framework | UVM (Universal Verification Methodology) |
| Test files | `*_test.sv`, `*_tb.sv`, `tb_*.sv` |
| Test directories | `tb/`, `testbench/`, `verif/`, `sim/` |
| Test cases | Classes extending `uvm_test`, tasks in testbench modules |
| Sequences | `*_seq.sv` — drive stimulus, not assertions (skip during scanning unless they contain assertions) |
| Run command | Simulator-dependent (VCS, Questa, Xcelium) |

**Note:** UVM testbenches often separate stimulus (sequences) from checking (scoreboards, monitors). When scanning, focus on test classes and scoreboard assertions, not sequence definitions.

## TypeScript / JavaScript

| Convention | Pattern |
|---|---|
| Framework | Jest, Vitest, Mocha |
| Test files | `*.test.ts`, `*.spec.ts`, `*.test.js`, `*.spec.js` |
| Test directories | `__tests__/`, `test/`, `tests/` |
| Test functions | `it()`, `test()`, `describe()` blocks |
| Run command | `npm test`, `npx jest`, `npx vitest` |

## Shell / Bash

| Convention | Pattern |
|---|---|
| Framework | bats (Bash Automated Testing System) |
| Test files | `*.bats` |
| Test directories | `test/`, `tests/` |
| Test functions | `@test` blocks |
| Run command | `bats tests/` |

**Note:** Shell scripts without bats tests are a coverage gap — flag as "no dedicated test framework" in the register.

## Docker / Containers

| Convention | Pattern |
|---|---|
| Framework | container-structure-test (Google), dgoss/goss |
| Test files | `container-structure-test.yaml`, `goss.yaml`, `*.goss.yaml` |
| Test directories | alongside Dockerfile or in `test/` |
| Assertions | File existence, command output, port exposure, metadata |
| Run command | `container-structure-test test --image img --config test.yaml` |

## Makefile

| Convention | Pattern |
|---|---|
| Framework | bats (testing make targets as shell commands) |
| Test files | `*.bats` targeting make invocations |
| Test directories | `test/` |
| Assertions | Exit codes, file output, stdout content |
| Run command | `bats tests/test_makefile.bats` |

## YAML / Configuration

| Convention | Pattern |
|---|---|
| Framework | Schema validation (jsonschema, yamllint), kubeval, custom pytest |
| Test files | pytest tests that load and validate configs, or schema files |
| Assertions | Schema conformance, required fields, valid references |

## When a Language Has No Test Framework

If test files cannot be found for a module's language:
- Check if tests exist in a different language (e.g., Python tests for a Dockerfile)
- Check if the module is tested transitively by integration tests
- If no tests exist at all, the module appears in the **Unfound Modules** section of the register
