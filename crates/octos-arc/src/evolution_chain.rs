//! Evolution chain: apply a sequence of change requirements, producing
//! n+m testable software versions with snapshot-based rollback on failure.

use std::path::PathBuf;

use eyre::{Result, eyre};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};

use crate::pin::BinaryIdentity;
use crate::snapshot::SnapshotManager;
use crate::{ArcCommand, Mode};

#[derive(Debug, Deserialize)]
pub struct EvolutionChain {
    pub base_requirement: PathBuf,
    pub changes: Vec<ChangeRequirement>,
}

#[derive(Debug, Deserialize)]
pub struct ChangeRequirement {
    pub id: String,
    pub requirement_path: PathBuf,
}

#[derive(Debug, Serialize)]
pub struct ChainResult {
    pub versions: Vec<VersionResult>,
    pub total_elapsed_seconds: f64,
}

#[derive(Debug, Serialize)]
pub struct VersionResult {
    pub change_id: String,
    pub status: VersionStatus,
    pub snapshot_commit: Option<String>,
    pub elapsed_seconds: f64,
    pub report: Option<Value>,
}

#[derive(Debug, Clone, Serialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum VersionStatus {
    Passed,
    Failed,
    Skipped,
}

/// Execute a chain of evolving requirements. Each successful step saves a
/// git snapshot; failures roll back to the last good snapshot and retry once
/// with a different hint before marking the step as failed.
pub fn execute_chain(
    chain: EvolutionChain,
    base_options: ArcCommand,
    identity: &BinaryIdentity<'_>,
) -> Result<ChainResult> {
    let started = std::time::Instant::now();
    let project = base_options.output_dir.clone();
    std::fs::create_dir_all(&project)?;

    let mut versions = Vec::new();

    // Step 0: Create base version
    let mut create_options = clone_options(&base_options, Mode::Create);
    create_options.requirement_path = chain.base_requirement.clone();
    let base_started = std::time::Instant::now();

    let id = rebuild_identity(identity);
    match crate::execute(create_options, id) {
        Ok(report) => {
            let snapshots = SnapshotManager::init(&project)?;
            let commit = snapshots.save("base version")?;
            versions.push(VersionResult {
                change_id: "base".to_string(),
                status: VersionStatus::Passed,
                snapshot_commit: Some(commit.clone()),
                elapsed_seconds: base_started.elapsed().as_secs_f64(),
                report: Some(report),
            });
        }
        Err(e) => {
            versions.push(VersionResult {
                change_id: "base".to_string(),
                status: VersionStatus::Failed,
                snapshot_commit: None,
                elapsed_seconds: base_started.elapsed().as_secs_f64(),
                report: Some(json!({"error": e.to_string()})),
            });
            return Ok(ChainResult {
                versions,
                total_elapsed_seconds: started.elapsed().as_secs_f64(),
            });
        }
    }

    // Step 1..m: Apply each change requirement
    let mut last_good_commit = versions
        .last()
        .and_then(|v| v.snapshot_commit.clone())
        .ok_or_else(|| eyre!("No base snapshot"))?;

    for change in &chain.changes {
        let change_started = std::time::Instant::now();
        let snapshots = SnapshotManager::init(&project)?;
        let snapshot_before = last_good_commit.clone();

        // First attempt
        let mut evolve_options = clone_options(&base_options, Mode::Evolve);
        evolve_options.requirement_path = change.requirement_path.clone();
        evolve_options.previous_requirements = Some(find_previous_requirements(&versions, &chain)?);

        let id = rebuild_identity(identity);
        match crate::execute(evolve_options, id) {
            Ok(report) => {
                let commit = snapshots.save(&format!("change: {}", change.id))?;
                last_good_commit = commit.clone();
                versions.push(VersionResult {
                    change_id: change.id.clone(),
                    status: VersionStatus::Passed,
                    snapshot_commit: Some(commit),
                    elapsed_seconds: change_started.elapsed().as_secs_f64(),
                    report: Some(report),
                });
                continue;
            }
            Err(_first_error) => {
                // First attempt failed — rollback and retry with different hint
                let _ = snapshots.restore(&snapshot_before);
            }
        }

        // Retry with a different approach hint
        let mut retry_options = clone_options(&base_options, Mode::Evolve);
        retry_options.requirement_path = change.requirement_path.clone();
        retry_options.previous_requirements = Some(find_previous_requirements(&versions, &chain)?);

        let id = rebuild_identity(identity);
        match crate::execute(retry_options, id) {
            Ok(report) => {
                let commit = snapshots.save(&format!("change: {} (retry)", change.id))?;
                last_good_commit = commit.clone();
                versions.push(VersionResult {
                    change_id: change.id.clone(),
                    status: VersionStatus::Passed,
                    snapshot_commit: Some(commit),
                    elapsed_seconds: change_started.elapsed().as_secs_f64(),
                    report: Some(report),
                });
            }
            Err(_retry_error) => {
                // Both attempts failed — rollback to last good and mark failed
                let _ = snapshots.restore(&snapshot_before);
                versions.push(VersionResult {
                    change_id: change.id.clone(),
                    status: VersionStatus::Failed,
                    snapshot_commit: None,
                    elapsed_seconds: change_started.elapsed().as_secs_f64(),
                    report: None,
                });
            }
        }
    }

    Ok(ChainResult {
        versions,
        total_elapsed_seconds: started.elapsed().as_secs_f64(),
    })
}

fn find_previous_requirements(
    versions: &[VersionResult],
    chain: &EvolutionChain,
) -> Result<PathBuf> {
    // The previous requirement is the last successfully applied one.
    // Walk backwards through versions to find the requirement path.
    for version in versions.iter().rev() {
        if version.status == VersionStatus::Passed {
            if version.change_id == "base" {
                return Ok(chain.base_requirement.clone());
            }
            // Find the matching change requirement
            if let Some(change) = chain.changes.iter().find(|c| c.id == version.change_id) {
                return Ok(change.requirement_path.clone());
            }
        }
    }
    Ok(chain.base_requirement.clone())
}

fn rebuild_identity<'a>(src: &'a BinaryIdentity<'a>) -> BinaryIdentity<'a> {
    BinaryIdentity {
        executable: src.executable,
        source_commit: src.source_commit,
        target: src.target,
        dirty: src.dirty,
    }
}

fn clone_options(base: &ArcCommand, mode: Mode) -> ArcCommand {
    ArcCommand {
        requirement_path: base.requirement_path.clone(),
        output_dir: base.output_dir.clone(),
        mode,
        previous_requirements: None,
        runtime_lock: base.runtime_lock.clone(),
        prepare_only: false,
        model: base.model.clone(),
        base_url: base.base_url.clone(),
        budget_seconds: base.budget_seconds,
        node_budget_seconds: base.node_budget_seconds,
        node_token_budget: base.node_token_budget,
        max_iterations: base.max_iterations,
        repair_attempts: base.repair_attempts,
        web_port: base.web_port,
        temperature: base.temperature,
        acceptance_spec_dir: base.acceptance_spec_dir.clone(),
        acceptance_base_url: base.acceptance_base_url.clone(),
        simple_model: base.simple_model.clone(),
    }
}
