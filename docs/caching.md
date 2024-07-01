# Caching

Tach makes use of a 'computation cache' to speed up certain tasks, such as [testing](usage.md#tach-test).

When Tach finds cached results for a given task, you will see the terminal output enclosed in:

```
============ Cached results found!  ============
...
============ END Cached results  ============
```

Caching is done at the command-level, meaning a single invocation of `tach test` can only ever result in a single cache hit or a single cache miss; individual tests are not cached separately.

## Cache content

The computation cache contains the output from `stdout` and `stderr` from a previous task invocation.

This is done to enable 'replaying' cached tasks so that their output can be reused seamlessly.

## Determining cache hits

Tach uses several pieces of information to determine cache hits. These include:

- Python interpreter version (`major.minor.micro`)
- All Python file contents beneath the [source root](https://gauge-sh.github.io/tach/configuration#source-root)
- Declared versions of 3rd party dependencies in project requirements (`requirements.txt` or `pyproject.toml`)
- File contents of explicitly configured [file dependencies](configuration.md#cache)
- Explicitly configured [environment variable values](configuration.md#cache)

When all of these pieces of information match a previous cache entry, the cached results are printed directly to the terminal.


## Cache storage

The computation cache currently exists within the `.tach` directory in your project root. The directory is managed by Tach, which means that your cached results are stored on-disk on each machine where tasks are run.

We are currently working on a *remote cache* backend, which will allow multiple developers and CI environments to share a centralized cache to maximize the hit rate. If you are interested in this functionality, tell us on [Discord](https://discord.gg/a58vW8dnmw), through a [GitHub issue](https://github.com/gauge-sh/tach/issues), or reach out via email: [evan@gauge.sh](mailto://evan@gauge.sh); [caelean@gauge.sh](mailto://caelean@gauge.sh)

## Disabling the cache

The computation cache is enabled by default for commands such as [tach test](usage.md#tach-test). For any command which utilizes the cache, it can be disabled using the `--disable-cache` CLI flag. This will prevent all access to the cache and run the underlying command unconditionally.