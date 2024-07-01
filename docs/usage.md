# Usage

## tach mod
Tach comes bundled with a command to set up your initial boundaries - `tach mod`.

```bash
usage: tach mod [-h] [-d [DEPTH]] [-e file_or_path,...]

Configure module boundaries interactively

options:
  -h, --help            show this help message and exit
  -d [DEPTH], --depth [DEPTH]
                        The number of child directories to expand from the root
  -e file_or_path,..., --exclude file_or_path,...
                        Comma separated path list to exclude. tests/, ci/, etc.
```

Running `tach mod` will open an editor in your terminal where you can mark your module boundaries.

You can navigate with the arrow keys, mark individual modules with `Enter`, and mark all siblings
as modules with `Ctrl + a`.

You can also mark your Python [source root](configuration.md#source-root) by pressing `s`.
This allows Tach to understand module paths and correctly identify first-party imports.

To save your modules, use `Ctrl + s`. Otherwise, to exit without saving, use `Ctrl + c`.

Any time you make changes with `tach mod`, run [`tach sync`](usage.md#tach-sync)
to automatically configure dependency rules.


## tach sync
Tach can automatically sync your project configuration (`tach.yml`) with your project's actual dependencies.

```bash
usage: tach sync [-h] [--prune] [-e file_or_path,...]

Sync constraints with actual dependencies in your project.

options:
  -h, --help            show this help message and exit
  --prune               Prune all existing constraints and re-sync dependencies.
  -e file_or_path,..., --exclude file_or_path,...
                        Comma separated path list to exclude. tests/, ci/, etc.
```

When this command runs, Tach will analyze the imports in your Python project.

Any undeclared dependencies will be automatically resolved by
adding the corresponding dependencies to your `tach.yml` file.

With `--prune`,
any dependency constraints in your `tach.yml` which are not necessary will also be removed.


## tach check
Tach will flag any unwanted imports between modules. We recommend you run `tach check` like a linter or test runner, e.g. in pre-commit hooks, on-save hooks, and in CI pipelines.

```bash
usage: tach check [-h] [--exact] [-e file_or_path,...]

Check existing boundaries against your dependencies and module interfaces

options:
  -h, --help            show this help message and exit
  --exact               Raise errors if any dependency constraints are unused.
  -e file_or_path,..., --exclude file_or_path,...
                        Comma separated path list to exclude. tests/, ci/, etc.
```

An error will indicate:

- the file path in which the error was detected
- the tag associated with that file
- the tag associated with the attempted import

If `--exact` is provided, additional errors will be raised if a dependency exists in `tach.yml` that does not exist in the code.

Example:
```bash
> tach check
❌ tach/check.py[L8]: Cannot import 'tach.filesystem'. Tag 'tach' cannot depend on 'tach.filesystem'. 
```

NOTE: If your terminal supports hyperlinks, you can click on the failing file path to go directly to the error.

## tach report
Tach can generate a report showing all the dependencies and usages of a given module.

```bash
usage: tach report [-h] [-e file_or_path,...] path

Create a report of dependencies and usages of the given path or directory.

positional arguments:
  path                  The path or directory path used to generate the report.

options:
  -h, --help            show this help message and exit
  -e file_or_path,..., --exclude file_or_path,...
                        Comma separated path list to exclude. tests/, ci/, etc.
```

This will generate a textual report showing the file and line number of each relevant import.

## tach show
Tach will generate a visual representation of your dependency graph!
```bash
usage: tach show [-h]

Visualize the dependency graph of your project on the web.

options:
  -h, --help  show this help message and exit
```

![tach show](assets/tach_show.png)


## tach test
Tach also functions as an intelligent test runner.

```
usage: tach test [-h] [--base [BASE]] [--head [HEAD]] [--disable-cache] ...

Run tests on modules impacted by the current changes.

positional arguments:
  pytest_args      Arguments forwarded to pytest. Use '--' to separate
                   these arguments. Ex: 'tach test -- -v'

options:
  -h, --help       show this help message and exit
  --base [BASE]    The base commit to use when determining which modules
                   are impacted by changes. [default: 'main']
  --head [HEAD]    The head commit to use when determining which modules
                   are impacted by changes. [default: current filesystem]
  --disable-cache  Do not check cache for results, and
                   do not push results to cache.
```

Using `pytest`, running `tach test` will perform [impact analysis](https://martinfowler.com/articles/rise-test-impact-analysis.html) on the changes between your current filesystem and your `main` branch to determine which test files need to be run.

This can dramatically speed up your test suite in CI, particularly when you make a small change to a large codebase.

This command also takes advantage of Tach's [computation cache](caching.md).


## tach install
Tach can be installed into your development workflow automatically as a pre-commit hook.


### With pre-commit framework
If you use the [pre-commit framework](https://github.com/pre-commit/pre-commit), you can add the following to your `.pre-commit-hooks.yaml`:

```yaml
repos:
-   repo: https://github.com/gauge-sh/tach-pre-commit
    rev: v0.6.6  # change this to the latest tag!
    hooks:
    -   id: tach
```

Note that you should specify the version you are using in the `rev` key.

### Standard install
If you don't already have pre-commit hooks set up, you can run:

```bash
tach install pre-commit
```

The command above will install `tach check` as a pre-commit hook, directly into `.git/hooks/pre-commit`.

If that file already exists, you will need to manually add `tach check` to your existing `.git/hooks/pre-commit` file.
