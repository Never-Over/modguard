pub mod cache;
pub mod cli;
pub mod colors;
pub mod exclusion;
pub mod filesystem;
pub mod imports;
pub mod parsing;
pub mod reports;

use cache::ComputationCacheValue;
use pyo3::exceptions::{PyOSError, PySyntaxError, PyValueError};
use pyo3::prelude::*;

impl From<imports::ImportParseError> for PyErr {
    fn from(err: imports::ImportParseError) -> Self {
        match err.err_type {
            imports::ImportParseErrorType::FILESYSTEM => PyOSError::new_err(err.message),
            imports::ImportParseErrorType::PARSING => PySyntaxError::new_err(err.message),
        }
    }
}

impl From<exclusion::PathExclusionError> for PyErr {
    fn from(err: exclusion::PathExclusionError) -> Self {
        PyValueError::new_err(err.message)
    }
}

impl From<reports::ReportCreationError> for PyErr {
    fn from(err: reports::ReportCreationError) -> Self {
        PyValueError::new_err(err.message)
    }
}

impl From<cache::CacheError> for PyErr {
    fn from(_: cache::CacheError) -> Self {
        PyValueError::new_err("Failure accessing computation cache.")
    }
}

/// Get first-party imports from file_path relative to project_root
#[pyfunction]
#[pyo3(signature = (project_root, source_root, file_path, ignore_type_checking_imports=false))]
fn get_project_imports(
    project_root: String,
    source_root: String,
    file_path: String,
    ignore_type_checking_imports: bool,
) -> imports::Result<imports::ProjectImports> {
    imports::get_project_imports(
        project_root,
        source_root,
        file_path,
        ignore_type_checking_imports,
    )
}

/// Set excluded paths globally.
/// This is called separately in order to set up a singleton instance holding regexes,
/// since they would be expensive to build for every call.
#[pyfunction]
#[pyo3(signature = (exclude_paths))]
fn set_excluded_paths(exclude_paths: Vec<String>) -> exclusion::Result<()> {
    exclusion::set_excluded_paths(exclude_paths)
}

/// Create a report of dependencies and usages of a given path
#[pyfunction]
#[pyo3(signature = (project_root, source_root, path, ignore_type_checking_imports=false))]
fn create_dependency_report(
    project_root: String,
    source_root: String,
    path: String,
    ignore_type_checking_imports: bool,
) -> reports::Result<String> {
    reports::create_dependency_report(
        project_root,
        source_root,
        path,
        ignore_type_checking_imports,
    )
}

#[pyfunction]
#[pyo3(signature = (project_root, source_root, action, py_interpreter_version, file_dependencies, env_dependencies, backend))]
fn create_computation_cache_key(
    project_root: String,
    source_root: String,
    action: String,
    py_interpreter_version: String,
    file_dependencies: Vec<String>,
    env_dependencies: Vec<String>,
    backend: String,
) -> String {
    cache::create_computation_cache_key(
        project_root,
        source_root,
        action,
        py_interpreter_version,
        file_dependencies,
        env_dependencies,
        backend,
    )
}

#[pyfunction]
#[pyo3(signature = (project_root, cache_key))]
fn check_computation_cache(
    project_root: String,
    cache_key: String,
) -> cache::Result<Option<ComputationCacheValue>> {
    cache::check_computation_cache(project_root, cache_key)
}

#[pyfunction]
#[pyo3(signature = (project_root, cache_key, value))]
fn update_computation_cache(
    project_root: String,
    cache_key: String,
    value: ComputationCacheValue,
) -> cache::Result<Option<ComputationCacheValue>> {
    cache::update_computation_cache(project_root, cache_key, value)
}

#[pymodule]
fn extension(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_project_imports, m)?)?;
    m.add_function(wrap_pyfunction!(set_excluded_paths, m)?)?;
    m.add_function(wrap_pyfunction!(create_dependency_report, m)?)?;
    m.add_function(wrap_pyfunction!(create_computation_cache_key, m)?)?;
    m.add_function(wrap_pyfunction!(check_computation_cache, m)?)?;
    m.add_function(wrap_pyfunction!(update_computation_cache, m)?)?;
    Ok(())
}
