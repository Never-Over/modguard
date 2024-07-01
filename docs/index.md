# Overview

## What is tach?
Tach allows you to control dependencies between your Python modules.
Modules can also define an explicit public interface to prevent deep coupling.

This creates a decoupled, modular architecture, which makes maintenance and development easier.

If a module tries to import from another module that is not listed as a dependency, Tach will report an error.

When a module is in ['strict mode'](strict-mode.md), if another module tries to import from it without using its public interface, Tach will report an error.

Tach is a CLI tool, and is ideal for pre-commit hooks and CI checks.

Tach is:

- 🌎 Open source
- 🐍 Installable via pip
- 🔧 Able to be adopted incrementally
- ⚡ Implemented with no runtime impact
- ♾️ Interoperable with your existing systems (cli, hooks, ci, etc.)

## Commands
* [`tach mod`](usage.md#tach-mod) - Interactively define module boundaries.
* [`tach check`](usage.md#tach-check) - Check that boundaries are respected.
* [`tach sync`](usage.md#tach-sync) - Sync constraints with the actual dependencies in your project.
* [`tach show`](usage.md#tach-show) - Visualize your project's dependency graph.
* [`tach report`](usage.md#tach-report) - Generate a dependency report for a file or module.
* [`tach test`](usage.md#tach-test) - Run only the tests impacted by your changes
* [`tach install`](usage.md#tach-install) - Install Tach into your development workflow (e.g. pre-commit)
