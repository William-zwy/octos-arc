//! Completion Gate — lightweight node-level validation before accepting a node
//! as "done". Runs build + test (no HTTP startup or Playwright) to catch
//! failures early rather than discovering them only at the final full validate().

use std::ffi::OsString;
use std::path::Path;
use std::time::{Duration, Instant};

use eyre::Result;
use serde_json::Value;

use crate::process;
use crate::validation_parser::{self, ValidationResult};

pub enum CompletionDecision {
    Allow,
    Continue { feedback: String },
    BudgetExhausted,
}

/// Run a lightweight validation (build + unit tests, no HTTP/Playwright).
/// Returns a structured ValidationResult.
pub fn lightweight_validate(
    project: &Path,
    env: &[(OsString, OsString)],
    deadline: Instant,
) -> Result<ValidationResult> {
    let mut stdout_parts = Vec::new();
    let mut stderr_parts = Vec::new();
    let mut last_exit_code = Some(0i32);

    // 1. Build frontend (catches TypeScript / compilation errors)
    if project.join("frontend/package.json").is_file() {
        let build_result = run_npm(project, "frontend", &["run", "build"], env, deadline);
        match build_result {
            Ok(output) => {
                stdout_parts.push(output.stdout.clone());
                stderr_parts.push(output.stderr.clone());
                if !output.succeeded() {
                    last_exit_code = output.exit_code;
                }
            }
            Err(e) => {
                stderr_parts.push(e.to_string());
                last_exit_code = Some(1);
            }
        }
    }

    // 2. Run tests (frontend + backend) if configured
    for part in ["frontend", "backend"] {
        if Instant::now() >= deadline {
            break;
        }
        let pkg_path = project.join(part).join("package.json");
        if !pkg_path.is_file() {
            continue;
        }
        let Ok(pkg_bytes) = std::fs::read(&pkg_path) else {
            continue;
        };
        let Ok(pkg): Result<Value, _> = serde_json::from_slice(&pkg_bytes) else {
            continue;
        };
        let has_test = pkg
            .get("scripts")
            .and_then(|s| s.get("test"))
            .and_then(Value::as_str)
            .is_some_and(|v| !v.trim().is_empty());
        if !has_test {
            continue;
        }

        let test_result = run_npm(project, part, &["test"], env, deadline);
        match test_result {
            Ok(output) => {
                stdout_parts.push(output.stdout.clone());
                stderr_parts.push(output.stderr.clone());
                if !output.succeeded() {
                    last_exit_code = output.exit_code;
                }
            }
            Err(e) => {
                stderr_parts.push(e.to_string());
                last_exit_code = Some(1);
            }
        }
    }

    let combined_stdout = stdout_parts.join("\n");
    let combined_stderr = stderr_parts.join("\n");

    Ok(validation_parser::parse_validation_output(
        &combined_stdout,
        &combined_stderr,
        last_exit_code,
    ))
}

/// Evaluate whether a node should be considered complete based on validation.
pub fn evaluate_completion(
    validation: &ValidationResult,
    attempt: u8,
    max_attempts: u8,
    deadline: Instant,
) -> CompletionDecision {
    if Instant::now() >= deadline {
        return CompletionDecision::BudgetExhausted;
    }

    if validation.passed {
        return CompletionDecision::Allow;
    }

    if attempt >= max_attempts {
        return CompletionDecision::BudgetExhausted;
    }

    let feedback = validation.to_feedback();
    CompletionDecision::Continue {
        feedback: format!(
            "Node validation failed after implementation. Fix these issues:\n\n{feedback}\n\nRepair only this node, do not re-scaffold."
        ),
    }
}

fn run_npm(
    project: &Path,
    part: &str,
    args: &[&str],
    env: &[(OsString, OsString)],
    deadline: Instant,
) -> Result<process::Output> {
    let npm_args: Vec<OsString> = args.iter().map(OsString::from).collect();
    process::run(
        Path::new("npm"),
        &npm_args,
        &project.join(part),
        env,
        deadline.min(Instant::now() + Duration::from_secs(60)),
    )
}
