//! Structured parsing of build and test output for precise repair feedback.

use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
pub struct ValidationResult {
    pub passed: bool,
    pub exit_code: Option<i32>,
    pub total_tests: Option<usize>,
    pub passed_tests: Option<usize>,
    pub failed_tests: Vec<FailedTest>,
    pub build_errors: Vec<BuildError>,
    pub summary: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct FailedTest {
    pub name: String,
    pub file: Option<String>,
    pub message: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct BuildError {
    pub file: String,
    pub line: Option<usize>,
    pub col: Option<usize>,
    pub code: Option<String>,
    pub message: String,
}

impl ValidationResult {
    pub fn to_feedback(&self) -> String {
        let mut parts = Vec::new();

        if !self.build_errors.is_empty() {
            parts.push(format!("Build: {} error(s)", self.build_errors.len()));
            for e in &self.build_errors {
                let loc = match (e.line, e.col) {
                    (Some(l), Some(c)) => format!("{}:{}:{}", e.file, l, c),
                    (Some(l), None) => format!("{}:{}", e.file, l),
                    _ => e.file.clone(),
                };
                let code = e.code.as_deref().unwrap_or("");
                parts.push(format!("  {loc} — {code} {}", e.message));
            }
        }

        if let (Some(total), Some(passed)) = (self.total_tests, self.passed_tests) {
            let failed_count = total.saturating_sub(passed);
            parts.push(format!(
                "Tests: {failed_count} failed / {passed} passed / {total} total"
            ));
        }

        for t in &self.failed_tests {
            let loc = t
                .file
                .as_deref()
                .map(|f| format!(" ({f})"))
                .unwrap_or_default();
            parts.push(format!("  FAIL{loc} {} — {}", t.name, t.message));
        }

        if parts.is_empty() {
            if self.passed {
                return "All checks passed.".to_string();
            }
            return self.summary.clone();
        }

        parts.join("\n")
    }
}

/// Parse combined stdout + stderr from a build or test command.
pub fn parse_validation_output(
    stdout: &str,
    stderr: &str,
    exit_code: Option<i32>,
) -> ValidationResult {
    let combined = format!("{stdout}\n{stderr}");
    let passed = exit_code == Some(0);

    let mut build_errors = Vec::new();
    let mut failed_tests = Vec::new();
    let mut total_tests: Option<usize> = None;
    let mut passed_tests: Option<usize> = None;

    for line in combined.lines() {
        let trimmed = line.trim();

        // TypeScript errors: src/file.ts(12,5): error TS2322: message
        if let Some(err) = parse_ts_error(trimmed) {
            build_errors.push(err);
            continue;
        }

        // Jest/Vitest FAIL line: FAIL src/file.test.ts
        if let Some(test) = parse_jest_fail(trimmed, &combined) {
            failed_tests.push(test);
            continue;
        }

        // Playwright expect failures: expect(locator).toHaveText(expected)
        if let Some(test) = parse_playwright_fail(trimmed) {
            failed_tests.push(test);
            continue;
        }

        // Jest/Vitest summary: Tests: N failed, M passed, T total
        // parse_test_summary takes priority over parse_vitest_summary
        if let Some((total, pass)) = parse_test_summary(trimmed) {
            total_tests = Some(total);
            passed_tests = Some(pass);
        } else if let Some((total, pass)) = parse_vitest_summary(trimmed) {
            total_tests = Some(total);
            passed_tests = Some(pass);
        }
    }

    let summary = if !passed {
        let tail_lines: Vec<&str> = combined
            .lines()
            .filter(|l| !l.trim().is_empty())
            .collect();
        let start = tail_lines.len().saturating_sub(5);
        tail_lines[start..].join("\n")
    } else {
        "All checks passed.".to_string()
    };

    ValidationResult {
        passed,
        exit_code,
        total_tests,
        passed_tests,
        failed_tests,
        build_errors,
        summary,
    }
}

fn parse_ts_error(line: &str) -> Option<BuildError> {
    // Pattern: src/file.ts(12,5): error TS2322: Type 'x' is not assignable
    // Also handles: src/file.ts:12:5 - error TS2322: message
    let (file_loc, rest) = if let Some(idx) = line.find("): error TS") {
        let before = &line[..idx + 1];
        let after = &line[idx + 3..]; // skip "): "
        (before, after)
    } else if let Some(idx) = line.find(" - error TS") {
        let before = &line[..idx];
        let after = &line[idx + 3..]; // skip " - "
        (before, after)
    } else {
        return None;
    };

    let (file, line_num, col) = parse_file_location(file_loc)?;

    let (code, message) = if let Some(colon) = rest.find(": ") {
        let code_part = &rest[..colon];
        let msg_part = &rest[colon + 2..];
        (Some(code_part.trim().to_string()), msg_part.to_string())
    } else {
        (None, rest.to_string())
    };

    Some(BuildError {
        file,
        line: line_num,
        col,
        code,
        message,
    })
}

fn parse_file_location(loc: &str) -> Option<(String, Option<usize>, Option<usize>)> {
    // Handle src/file.ts(12,5) format
    if let Some(paren) = loc.find('(') {
        let file = loc[..paren].to_string();
        let inner = loc[paren + 1..].trim_end_matches(')');
        let parts: Vec<&str> = inner.split(',').collect();
        let line = parts.first().and_then(|s| s.trim().parse().ok());
        let col = parts.get(1).and_then(|s| s.trim().parse().ok());
        return Some((file, line, col));
    }

    // Handle src/file.ts:12:5 format
    let parts: Vec<&str> = loc.rsplitn(3, ':').collect();
    if parts.len() >= 2 {
        if let Ok(line) = parts[0].parse::<usize>() {
            let file = if parts.len() == 3 {
                parts[2].to_string()
            } else {
                parts[1].to_string()
            };
            let col = if parts.len() == 3 {
                parts[1].parse().ok()
            } else {
                None
            };
            return Some((file, Some(line), col));
        }
    }

    Some((loc.to_string(), None, None))
}

fn parse_jest_fail(line: &str, full_output: &str) -> Option<FailedTest> {
    // FAIL src/auth.test.ts
    let path = line.strip_prefix("FAIL ")?;
    let path = path.trim();
    if path.is_empty() || !path.contains('.') {
        return None;
    }

    // Look for specific assertion failures after this line
    let message = find_assertion_after(full_output, path);

    Some(FailedTest {
        name: path.to_string(),
        file: Some(path.to_string()),
        message: message.unwrap_or_else(|| "test failed".to_string()),
    })
}

fn find_assertion_after(output: &str, test_file: &str) -> Option<String> {
    let mut found_file = false;
    for line in output.lines() {
        if line.contains(test_file) && line.contains("FAIL") {
            found_file = true;
            continue;
        }
        if found_file {
            let trimmed = line.trim();
            if trimmed.starts_with("●")
                || trimmed.starts_with("✕")
                || trimmed.starts_with("×")
                || trimmed.starts_with("✗")
                || trimmed.contains("Expected")
                || trimmed.contains("Received")
                || trimmed.contains("expect(")
                || trimmed.contains("assert")
            {
                return Some(trimmed.to_string());
            }
            // Stop scanning after a few lines
            if trimmed.starts_with("FAIL ") || trimmed.starts_with("PASS ") {
                break;
            }
        }
    }
    None
}

fn parse_playwright_fail(line: &str) -> Option<FailedTest> {
    // expect(locator).toHaveText("expected")
    // Error: expect(received).toEqual(expected)
    if !line.contains("expect(") {
        return None;
    }
    if !line.contains("toHaveText")
        && !line.contains("toBeVisible")
        && !line.contains("toEqual")
        && !line.contains("toBe")
        && !line.contains("toContainText")
        && !line.contains("toHaveCount")
        && !line.contains("toHaveValue")
        && !line.contains("toHaveAttribute")
        && !line.contains("Error:")
    {
        return None;
    }
    Some(FailedTest {
        name: "playwright assertion".to_string(),
        file: None,
        message: line.trim().to_string(),
    })
}

fn parse_test_summary(line: &str) -> Option<(usize, usize)> {
    // Jest: Tests:  1 failed, 15 passed, 16 total
    // Also: Test Suites: 1 failed, 3 passed, 4 total
    if !line.starts_with("Tests:") && !line.starts_with("Test Suites:") {
        return None;
    }
    let mut total = 0usize;
    let mut pass = 0usize;
    for segment in line.split(',') {
        let segment = segment.trim();
        if let Some(rest) = segment.strip_suffix(" total") {
            total = rest.trim().parse().ok()?;
        } else if let Some(rest) = segment.strip_suffix(" passed") {
            pass = rest
                .trim()
                .rsplit_once(' ')
                .map(|(_, n)| n)
                .unwrap_or(rest.trim())
                .parse()
                .ok()?;
        }
    }
    if total > 0 { Some((total, pass)) } else { None }
}

fn parse_vitest_summary(line: &str) -> Option<(usize, usize)> {
    // Vitest: ✓ 15 passed | ✗ 1 failed (16)
    // Or:     Tests  15 passed | 1 failed (16)
    // Must contain pipe separator to distinguish from Jest format
    if !line.contains('|') || !line.contains("passed") || !line.contains("failed") {
        return None;
    }
    let mut pass = 0usize;
    let mut fail = 0usize;
    for segment in line.split('|') {
        let segment = segment.trim();
        if segment.contains("passed") {
            for word in segment.split_whitespace() {
                if let Ok(n) = word.parse::<usize>() {
                    pass = n;
                    break;
                }
            }
        } else if segment.contains("failed") {
            for word in segment.split_whitespace() {
                if let Ok(n) = word.parse::<usize>() {
                    fail = n;
                    break;
                }
            }
        }
    }
    let total = pass + fail;
    if total > 0 { Some((total, pass)) } else { None }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn should_parse_typescript_error_paren_format() {
        let result = parse_validation_output(
            "src/api/auth.ts(42,5): error TS2322: Type 'string' is not assignable to type 'number'",
            "",
            Some(1),
        );
        assert!(!result.passed);
        assert_eq!(result.build_errors.len(), 1);
        assert_eq!(result.build_errors[0].file, "src/api/auth.ts");
        assert_eq!(result.build_errors[0].line, Some(42));
        assert_eq!(result.build_errors[0].col, Some(5));
        assert_eq!(
            result.build_errors[0].code.as_deref(),
            Some("error TS2322")
        );
    }

    #[test]
    fn should_parse_typescript_error_colon_format() {
        let result = parse_validation_output(
            "src/api/auth.ts:42:5 - error TS2322: Type 'string' is not assignable",
            "",
            Some(1),
        );
        assert_eq!(result.build_errors.len(), 1);
        assert_eq!(result.build_errors[0].file, "src/api/auth.ts");
    }

    #[test]
    fn should_parse_jest_summary() {
        let result = parse_validation_output(
            "Tests:        2 failed, 15 passed, 17 total",
            "",
            Some(1),
        );
        assert_eq!(result.total_tests, Some(17));
        assert_eq!(result.passed_tests, Some(15));
    }

    #[test]
    fn should_parse_vitest_summary() {
        let result = parse_validation_output(
            "✓ 15 passed | ✗ 2 failed (17)",
            "",
            Some(1),
        );
        assert_eq!(result.total_tests, Some(17));
        assert_eq!(result.passed_tests, Some(15));
    }

    #[test]
    fn should_parse_jest_fail_line() {
        let stdout = "FAIL src/auth.test.ts\n  ✕ should reject expired tokens\n    Expected: 401\n    Received: 200\nPASS src/utils.test.ts";
        let result = parse_validation_output(stdout, "", Some(1));
        assert_eq!(result.failed_tests.len(), 1);
        assert_eq!(result.failed_tests[0].name, "src/auth.test.ts");
    }

    #[test]
    fn should_parse_playwright_assertion() {
        let result = parse_validation_output(
            "Error: expect(received).toEqual(expected)",
            "",
            Some(1),
        );
        assert_eq!(result.failed_tests.len(), 1);
        assert!(result.failed_tests[0].message.contains("toEqual"));
    }

    #[test]
    fn should_produce_structured_feedback() {
        let result = parse_validation_output(
            "src/api/auth.ts(42,5): error TS2322: Type 'string' is not assignable to type 'number'\nTests:        1 failed, 15 passed, 16 total\nFAIL src/auth.test.ts\n  ✕ should reject expired tokens",
            "",
            Some(1),
        );
        let feedback = result.to_feedback();
        assert!(feedback.contains("Build: 1 error(s)"));
        assert!(feedback.contains("42:5"));
        assert!(feedback.contains("TS2322"));
        assert!(feedback.contains("1 failed / 15 passed"));
    }

    #[test]
    fn should_report_all_passed_when_exit_zero() {
        let result = parse_validation_output("all tests passed", "", Some(0));
        assert!(result.passed);
        assert_eq!(result.to_feedback(), "All checks passed.");
    }
}
