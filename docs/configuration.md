# Configuration

Aside from running `tach mod` and `tach sync`, you can configure Tach by creating or modifying the configuration file as described below.

## `tach.yml`

This is the project-level configuration file which should be in the root of your project.

`modules` defines the modules in your project, and accepts the keys described [below.](#modules)

`exclude` accepts a list of directory patterns to exclude from checking. These are treated as regex patterns which match from the beginning of a given file path. For example: `project/.*tests` would match any path beginning with `project/` and ending with `tests`.

`ignore_type_checking_imports` is a boolean which, when enabled, silences `tach check` failures caused by imports under a `TYPE_CHECKING` conditional block


```yaml
modules:
  - path: tach
    depends_on: []
    strict: true
  - path: tach.cache
    depends_on:
      - tach.filesystem
    strict: true
  - path: tach.filesystem
    depends_on: []
    strict: true
exclude:
  - .*__pycache__/
  - build/
  - dist/
  - docs/
  - tach.egg-info/
  - tests/
cache:
  file_dependencies:
    - python/tests/**
    - src/*.rs
  env_dependencies:
    - DEBUG
source_root: backend
exact: true
disable_logging: false
ignore_type_checking_imports: true
```

## Modules
Each module listed under the `modules` key above can accept the following attributes:

- `path`: the Python import path to the module (e.g. `a.b` for `<root>/a/b.py`)
- `depends_on`: a list of the other modules which the module is allowed to import from, using their 'paths' to identify them
- `strict`: enables [strict mode](strict-mode.md) for the module

## Source Root
The `source_root` key is required for Tach to understand the imports within your project.
If it is not set explicitly, `source_root` defaults to `'.'`.
This means Tach will expect that your Python imports are resolved relative to the directory in which `tach.yml` exists (the 'project root').

Below is a typical case in which `source_root` is necessary.

### Example

Suppose your repository contains a subfolder where all of your Python code lives. This could be a web server, a collection of serverless functions, or even utility scripts.
In this example we will assume the Python code in our repo lives in the `backend/` folder.
```
my_repo/
  tach.yml
  backend/
    module1.py
    module2/
      __init__.py
      service.py
    module3.py
  docs/
  tests/
```

In a Python module such as `backend/module1.py`, we can see imports from other modules.
```python
# In backend/module1.py

import module3
from module2.service import MyService
```

Notice that these import paths (`module3`, `module2.service.MyService`) are rooted in the `backend/` folder, NOT the project root.

To indicate this structure to Tach, set `source_root: backend` in your `tach.yml`, or use [`tach mod`](usage.md#tach-mod) and mark the `backend` folder as the source root.

In `tach.yml`, the `source_root` is always interpreted as a relative path from the project root.


## Cache

Tach allows configuration of the [computation cache](caching.md) it uses to speed up tasks like [testing](usage.md#tach-test).

The `file_dependencies` key accepts a list of glob patterns to indicate additional file contents that should be considered when [checking for cache hits](caching.md#determining-cache-hits). This should typically include files outside of your [source root](#source-root) which affect your project's behavior under test, including the tests themselves. Additionally, if you have non-Python files which affect your project's behavior (such as Rust or C extensions), these should be included as well.

The `env_dependencies` key accepts a list of environment variable names whose values affect your project's behavior under test. This may include a `DEBUG` flag, or database connection parameters in the case of tests which use a configurable database.
