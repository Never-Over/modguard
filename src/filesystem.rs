use std::fmt;
use std::fs;
use std::io;
use std::io::Read;
use std::path::StripPrefixError;
use std::path::{Path, PathBuf, MAIN_SEPARATOR, MAIN_SEPARATOR_STR};

use globset::Glob;
use globset::GlobSetBuilder;
use walkdir::{DirEntry, WalkDir};

use crate::exclusion::is_path_excluded;

#[derive(Debug, Clone)]
pub struct FileSystemError {
    pub message: String,
}

impl fmt::Display for FileSystemError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", &self.message)
    }
}

impl From<io::Error> for FileSystemError {
    fn from(_: io::Error) -> Self {
        FileSystemError {
            message: "Encountered unexpected I/O error.".to_string(),
        }
    }
}

impl From<StripPrefixError> for FileSystemError {
    fn from(_: StripPrefixError) -> Self {
        FileSystemError {
            message: "Path does not appear to be within project root.".to_string(),
        }
    }
}

pub type Result<T> = std::result::Result<T, FileSystemError>;

pub fn relative_to<P: AsRef<Path>>(path: P, root: P) -> Result<PathBuf> {
    let diff_path = path.as_ref().strip_prefix(root)?;
    Ok(diff_path.to_owned())
}

pub fn file_to_module_path(source_root: &str, file_path: &str) -> Result<String> {
    let relative_file_path = relative_to(file_path, source_root)?;
    if relative_file_path
        .file_name()
        .is_some_and(|name| name == ".")
    {
        return Ok(String::new());
    }

    let module_path = relative_file_path
        .as_os_str()
        .to_str()
        .unwrap()
        .replace(MAIN_SEPARATOR, ".");

    let mut module_path = if module_path.ends_with(".py") {
        module_path.trim_end_matches(".py").to_string()
    } else {
        module_path
    };

    if module_path.ends_with(".__init__") {
        module_path.truncate(module_path.len() - 9);
    }

    if module_path == "__init__" {
        return Ok(String::new());
    }

    Ok(module_path)
}

#[derive(Debug)]
pub struct ResolvedModule {
    pub file_path: PathBuf,
    pub member_name: Option<String>,
}

pub fn module_to_file_path<P: AsRef<Path>>(root: P, mod_path: &str) -> Option<ResolvedModule> {
    let mod_as_file_path = mod_path.replace('.', MAIN_SEPARATOR_STR);
    let fs_path = root.as_ref().join(&mod_as_file_path);
    let file_path = fs_path.display().to_string();

    // mod_path may refer to a package
    if fs_path.join("__init__.py").exists() {
        return Some(ResolvedModule {
            file_path: fs_path,
            member_name: None,
        });
    }

    // mod_path may refer to a file
    let py_file_path = format!("{}.py", &file_path);
    if Path::new(&py_file_path).exists() {
        return Some(ResolvedModule {
            file_path: PathBuf::from(py_file_path),
            member_name: None,
        });
    }

    // If the original file path does not contain a separator (e.g. 'os', 'ast')
    // then we are done checking. Further checks work by removing the lowest portion
    // to see if the import may refer to a member within a module.
    // TODO: An improvement would be to also filter out StmtImport from the following checks,
    // since 'import a.b.c' must not be referring to a member
    if !mod_as_file_path.contains(MAIN_SEPARATOR) {
        return None;
    }

    if let Some(last_sep_index) = file_path.rfind(MAIN_SEPARATOR) {
        // mod_path may refer to a member within a file
        let py_file_path = format!("{}.py", &file_path[..last_sep_index]);
        if Path::new(&py_file_path).exists() {
            let member_name = file_path[last_sep_index + 1..].to_string();
            return Some(ResolvedModule {
                file_path: PathBuf::from(py_file_path),
                member_name: Some(member_name),
            });
        }

        // mod_path may refer to a member within a package
        let init_py_file_path = format!(
            "{}{}__init__.py",
            &file_path[..last_sep_index],
            MAIN_SEPARATOR
        );
        if Path::new(&init_py_file_path).exists() {
            let member_name = file_path[last_sep_index + 1..].to_string();
            return Some(ResolvedModule {
                file_path: PathBuf::from(init_py_file_path),
                member_name: Some(member_name),
            });
        }
    }

    None
}

pub fn read_file_content<P: AsRef<Path>>(path: P) -> Result<String> {
    let mut file = fs::File::open(path.as_ref()).map_err(|_| FileSystemError {
        message: format!("Could not open path: {}", path.as_ref().display()),
    })?;
    let mut content = String::new();
    file.read_to_string(&mut content)
        .map_err(|_| FileSystemError {
            message: format!("Could not read path: {}", path.as_ref().display()),
        })?;
    Ok(content)
}

pub fn is_project_import<P: AsRef<Path>>(
    project_root: P,
    source_root: P,
    mod_path: &str,
) -> Result<bool> {
    let resolved_module = module_to_file_path(source_root, mod_path);
    if let Some(module) = resolved_module {
        // This appears to be a project import, verify it is not excluded
        return match is_path_excluded(
            relative_to(module.file_path.as_path(), project_root.as_ref())?
                .to_str()
                .unwrap(),
        ) {
            Ok(true) => Ok(false),
            Ok(false) => Ok(true),
            Err(_) => Err(FileSystemError {
                message: "Failed to check if path is excluded".to_string(),
            }),
        };
    } else {
        // This is not a project import
        Ok(false)
    }
}

fn is_hidden(entry: &DirEntry) -> bool {
    entry
        .file_name()
        .to_str()
        .map(|s| s.starts_with('.'))
        .unwrap_or(false)
}

fn direntry_is_excluded(root: &str, entry: &DirEntry) -> bool {
    let path = entry.path();
    // TODO: too much unwrapping
    let adjusted_path = relative_to(path.to_str().unwrap(), root).unwrap();
    is_path_excluded(adjusted_path.to_str().unwrap()).unwrap_or(false)
}

fn is_pyfile_or_dir(entry: &DirEntry) -> bool {
    if entry.path().is_dir() {
        return true;
    }
    match entry.path().extension() {
        Some(ext) => ext == "py",
        None => false,
    }
}

pub fn walk_pyfiles(root: &str) -> impl Iterator<Item = PathBuf> {
    let walker = WalkDir::new(root).into_iter();
    let prefix_root = String::from(root);
    let filter_root = prefix_root.clone();
    walker
        .filter_entry(move |e| {
            !is_hidden(e) && !direntry_is_excluded(&filter_root, e) && is_pyfile_or_dir(e)
        })
        .map(|res| res.unwrap().into_path())
        .filter(|path: &PathBuf| path.is_file()) // filter_entry would skip dirs if they were excluded earlier
        .map(move |path| path.strip_prefix(&prefix_root).unwrap().to_path_buf())
}

pub fn walk_globbed_files(root: &str, patterns: Vec<String>) -> impl Iterator<Item = PathBuf> {
    let mut glob_builder = GlobSetBuilder::new();

    for pattern in patterns {
        glob_builder.add(Glob::new(&pattern).unwrap());
    }

    let glob_set = glob_builder.build().unwrap();

    let walker = WalkDir::new(root).into_iter();
    let owned_root = root.to_string();
    walker
        .filter_entry(|e| !is_hidden(e))
        .map(|res| res.unwrap().into_path())
        .filter(move |path| {
            path.is_file()
                && glob_set.is_match(
                    relative_to(path, &PathBuf::from(&owned_root)).unwrap_or(path.to_path_buf()),
                )
        })
}
