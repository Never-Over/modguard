
# Tach

[![downloads](https://static.pepy.tech/badge/tach/month)](https://pepy.tech/project/tach)
[![version](https://img.shields.io/pypi/v/tach.svg)](https://pypi.Python.org/pypi/tach)
[![license](https://img.shields.io/pypi/l/tach.svg)](https://pypi.Python.org/pypi/tach)
[![python](https://img.shields.io/pypi/pyversions/tach.svg)](https://pypi.Python.org/pypi/tach)
[![ci](https://github.com/gauge-sh/tach/actions/workflows/ci.yml/badge.svg)](https://github.com/gauge-sh/tach/actions/workflows/ci.yml)
[![pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

a Python tool to enforce dependencies, written in Rust. Inspired by modular monolithic architecture.

[Docs](https://gauge-sh.github.io/tach/)

[Discord](https://discord.gg/a58vW8dnmw)

<div align="center">
    <img src="docs/assets/logo_black_background.png" alt="gauge-logo" width="30%"  style="border-radius: 50%; padding-bottom: 20px"/>
</div>

Tach lets you define and enforce dependencies between Python modules within your project.

Here's an example:

![tach_demo](https://github.com/gauge-sh/tach/assets/10570340/6fc1e9b4-5a78-4330-a329-9187bd9c374d)

If a module tries to import from another module that is not listed as a dependency, Tach can prevent it.

Tach is:
- 🌎 Open source
- 🐍 Installable via pip
- 🔧 Able to be adopted incrementally
- ⚡  Implemented with no runtime impact
- ♾️ Interoperable with your existing systems (cli, hooks, ci, etc.)

## Getting Started

### Installation
```bash
pip install tach
```
### Setup
Tach allows you to configure where you want to place module boundaries in your project.

You can do this interactively - run:
```bash
 tach mod
# Up/Down: Navigate  Enter: Mark/unmark module  Right: Expand  Left: Collapse  Ctrl + Up: Jump to parent
# Ctrl + s: Exit and save  Ctrl + c: Exit without saving  Ctrl + a: Mark/unmark all
```
Mark each module boundary with 'Enter'. You can mark all of your top-level Python source packages, or just a few which you want to isolate.

If your Python code lives below your project root, mark your Python [source root](https://gauge-sh.github.io/tach/configuration#source-root) using the 's' key.

This will create the config file for your project, `tach.yml`.

Once you've marked all the modules you want to enforce dependencies between, run:
```bash
tach sync
```
Dependencies that exist between each module you've marked will be written to `tach.yml`.

Check out what Tach has found! 
```
cat tach.yml | less
```

Note: Your [source root](https://gauge-sh.github.io/tach/configuration#source-root) directory will implicitly be treated as a module boundary, and can show up as `<root>`.

### Enforcement
Tach comes with a cli command to enforce the boundaries that you just set up! From the root of your Python project, run:
```bash
tach check
```
You will see:
```bash
✅ All module dependencies validated!
```

You can validate that Tach is working by either:
1. Commenting out an item in a `depends_on` key in `tach.yml`
2. By adding an import between modules that didn't previously import from each other. 

Give both a try and run `tach check` again. This will generate an error:
```bash
❌ tach/check.py[L8]: Cannot import 'tach.filesystem'. Tag 'tach' cannot depend on 'tach.filesystem'. 
```

Each error indicates an import which violates your dependencies. If your terminal supports hyperlinks, click on the file path to go directly to the error.

When an error is detected, `tach check` will exit with a non-zero code. It can be easily integrated with CI/CD, [Pre-commit hooks](https://gauge-sh.github.io/tach/usage/#tach-install), and [VS Code](https://marketplace.visualstudio.com/items?itemName=Gauge.tach), and more!

### Extras

Visualize your dependency graph.
```bash
tach show
```
Tach will generate a graph of your dependencies. Here's what this looks like for Tach itself:

![tach show](docs/assets/tach_show.png)

Note that this graph is generated remotely based on the contents of your `tach.yml`.

You can view the dependencies and usages for a given path:
```bash
tach report my_package/
# OR
tach report my_module.py
```
e.g.:
```bash
> tach report python/tach/filesystem
[Dependencies of 'python/tach/filesystem']
python/tach/filesystem/install.py[L6]: Import 'tach.hooks.build_pre_commit_hook_content'
python/tach/filesystem/project.py[L5]: Import 'tach.constants.CONFIG_FILE_NAME'
...
-------------------------------
[Usages of 'python/tach/filesystem']
python/tach/cache/access.py[L8]: Import 'tach.filesystem.find_project_config_root'
python/tach/cache/setup.py[L7]: Import 'tach.filesystem.find_project_config_root'
...
```

Tach also supports:

- [Manual file configuration](https://gauge-sh.github.io/tach/configuration/)
- [Strict public interfaces for modules](https://gauge-sh.github.io/tach/strict-mode/)
- [Inline exceptions](https://gauge-sh.github.io/tach/tach-ignore/)
- [Pre-commit hooks](https://gauge-sh.github.io/tach/usage/#tach-install)


More info in the [docs](https://gauge-sh.github.io/tach/). Tach logs anonymized usage statistics which can be [opted out](https://gauge-sh.github.io/tach/faq/) of.
If you have any feedback, we'd love to talk!

If you have any questions or run into any issues, let us know by either reaching out on [Discord](https://discord.gg/a58vW8dnmw) or submitting a [Github Issue](https://github.com/gauge-sh/tach/issues)!

---

### Contributors

<a href="https://github.com/gauge-sh/tach/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=gauge-sh/tach" />
</a>