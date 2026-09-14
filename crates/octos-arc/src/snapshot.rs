//! Git-based workspace snapshot management for checkpoint and rollback.

use std::path::{Path, PathBuf};
use std::process::Command;

use eyre::{Result, ensure, eyre};
use serde::Serialize;

pub struct SnapshotManager {
    project: PathBuf,
}

#[derive(Debug, Clone, Serialize)]
pub struct SnapshotEntry {
    pub commit: String,
    pub message: String,
}

const GITIGNORE_CONTENT: &str = "node_modules/
.arc/
dist/
build/
.next/
.nuxt/
.output/
coverage/
*.log
.env
.env.*
";

impl SnapshotManager {
    /// Initialize git repo in the project directory if not already a repo.
    /// Writes a .gitignore and creates an initial commit.
    pub fn init(project: &Path) -> Result<Self> {
        let project = project.canonicalize()?;
        let mgr = Self {
            project: project.clone(),
        };

        if !project.join(".git").is_dir() {
            mgr.git(&["init"])?;

            let gitignore = project.join(".gitignore");
            if !gitignore.exists() {
                std::fs::write(&gitignore, GITIGNORE_CONTENT)?;
            }

            mgr.git(&["add", "-A"])?;
            mgr.git(&[
                "commit",
                "--allow-empty",
                "-m",
                "octos-arc: initial checkpoint",
            ])?;
        }

        // Configure git to avoid user identity errors in clean environments
        let _ = mgr.git(&["config", "user.email", "octos-arc@local"]);
        let _ = mgr.git(&["config", "user.name", "octos-arc"]);

        Ok(mgr)
    }

    /// Save current state as a git commit. Returns the commit hash.
    pub fn save(&self, message: &str) -> Result<String> {
        self.git(&["add", "-A"])?;

        // Check if there are changes to commit
        let status = self.git_output(&["status", "--porcelain"])?;
        if status.trim().is_empty() {
            // No changes, return current HEAD
            return self.current();
        }

        self.git(&["commit", "-m", message])?;
        self.current()
    }

    /// Restore workspace to a specific commit, discarding current changes.
    pub fn restore(&self, commit: &str) -> Result<()> {
        ensure!(
            !commit.is_empty() && commit.chars().all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '_'),
            "Invalid commit hash"
        );
        // Reset HEAD to the target commit, updating both index and working tree
        self.git(&["reset", "--hard", commit])?;
        // Remove any untracked files/dirs left behind
        self.git(&["clean", "-fd"])?;
        Ok(())
    }

    /// Get the current HEAD commit hash.
    pub fn current(&self) -> Result<String> {
        let output = self.git_output(&["rev-parse", "HEAD"])?;
        let hash = output.trim().to_string();
        ensure!(!hash.is_empty(), "No HEAD commit found");
        Ok(hash)
    }

    /// List all snapshot commits (most recent first).
    pub fn list(&self) -> Result<Vec<SnapshotEntry>> {
        let output = self.git_output(&["log", "--oneline", "--no-decorate", "-n", "50"])?;
        let entries = output
            .lines()
            .filter(|line| !line.trim().is_empty())
            .filter_map(|line| {
                let (hash, message) = line.split_once(' ')?;
                Some(SnapshotEntry {
                    commit: hash.to_string(),
                    message: message.to_string(),
                })
            })
            .collect();
        Ok(entries)
    }

    fn git(&self, args: &[&str]) -> Result<()> {
        let output = Command::new("git")
            .args(args)
            .current_dir(&self.project)
            .env("GIT_TERMINAL_PROMPT", "0")
            .output()
            .map_err(|e| eyre!("Failed to run git {}: {}", args.join(" "), e))?;
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(eyre!(
                "git {} failed: {}",
                args.join(" "),
                stderr.trim()
            ));
        }
        Ok(())
    }

    fn git_output(&self, args: &[&str]) -> Result<String> {
        let output = Command::new("git")
            .args(args)
            .current_dir(&self.project)
            .env("GIT_TERMINAL_PROMPT", "0")
            .output()
            .map_err(|e| eyre!("Failed to run git {}: {}", args.join(" "), e))?;
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(eyre!(
                "git {} failed: {}",
                args.join(" "),
                stderr.trim()
            ));
        }
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn should_init_and_save_snapshot() {
        let temp = tempfile::tempdir().unwrap();
        let project = temp.path().join("project");
        std::fs::create_dir_all(&project).unwrap();
        std::fs::write(project.join("hello.txt"), "world").unwrap();

        let mgr = SnapshotManager::init(&project).unwrap();
        let commit1 = mgr.save("first checkpoint").unwrap();
        assert!(!commit1.is_empty());

        std::fs::write(project.join("hello.txt"), "updated").unwrap();
        let commit2 = mgr.save("second checkpoint").unwrap();
        assert_ne!(commit1, commit2);

        let entries = mgr.list().unwrap();
        assert!(entries.len() >= 2);
    }

    #[test]
    fn should_restore_to_previous_snapshot() {
        let temp = tempfile::tempdir().unwrap();
        let project = temp.path().join("project");
        std::fs::create_dir_all(&project).unwrap();
        std::fs::write(project.join("file.txt"), "v1").unwrap();

        let mgr = SnapshotManager::init(&project).unwrap();
        let v1 = mgr.save("v1").unwrap();

        std::fs::write(project.join("file.txt"), "v2").unwrap();
        std::fs::write(project.join("new.txt"), "added").unwrap();
        let _v2 = mgr.save("v2").unwrap();

        mgr.restore(&v1).unwrap();
        assert_eq!(std::fs::read_to_string(project.join("file.txt")).unwrap(), "v1");
        assert!(!project.join("new.txt").exists());
    }

    #[test]
    fn should_save_no_op_when_no_changes() {
        let temp = tempfile::tempdir().unwrap();
        let project = temp.path().join("project");
        std::fs::create_dir_all(&project).unwrap();
        std::fs::write(project.join("file.txt"), "content").unwrap();

        let mgr = SnapshotManager::init(&project).unwrap();
        let c1 = mgr.save("first").unwrap();
        let c2 = mgr.save("second (no change)").unwrap();
        assert_eq!(c1, c2);
    }
}
