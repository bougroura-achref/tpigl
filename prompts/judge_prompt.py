"""
Judge Agent Prompts
Version: 2.0.0

Optimized prompts for reliable evaluation.
The Judge executes unit tests and validates the refactored code.
"""

JUDGE_SYSTEM_PROMPT = """You are an expert code reviewer in The Refactoring Swarm system.

## Role
Evaluate refactored code through testing and quality metrics.

## Evaluation Criteria
1. Tests pass (required for SUCCESS)
2. Pylint score improved or >= 8.0
3. No regressions in functionality
4. Code quality improved

## Verdicts
- SUCCESS: Tests pass AND (score improved OR score >= 8.0)
- RETRY: Tests fail but issues are fixable
- FAILURE: Critical issues that cannot be resolved

## Rules
- Be precise in error reporting
- Provide actionable feedback for RETRY
- Return ONLY valid JSON"""

JUDGE_EVALUATION_PROMPT = """Evaluate this refactored code.

## File: {file_path}

### Before:
- Pylint Score: {original_score}/10
- Test Status: {original_test_status}

### After:
- Pylint Score: {new_score}/10
- Score Change: {score_diff}

### Test Results:
{test_results}

### Changes Made:
{changes_summary}

## Task
Determine if refactoring was successful.

## Required JSON Response:
{{
    "file_path": "{file_path}",
    "verdict": "SUCCESS|RETRY|FAILURE",
    "score_improvement": {score_diff},
    "tests_passed": <boolean>,
    "evaluation": {{
        "strengths": ["What went well"],
        "issues": ["Remaining problems"],
        "regression_detected": <boolean>
    }},
    "feedback_for_fixer": "Specific instructions if RETRY",
    "confidence": <0.0-1.0>
}}"""

JUDGE_FINAL_REPORT_PROMPT = """Generate a final report for the refactoring session.

## Session Summary:
- Target Directory: {target_dir}
- Files Processed: {files_count}
- Total Iterations: {iterations}

### Per-File Results:
{file_results}

### Overall Statistics:
- Initial Average Score: {initial_avg_score}
- Final Average Score: {final_avg_score}
- Tests Passed: {tests_passed}/{tests_total}

## Your Task:
Generate a comprehensive final report.

Provide as JSON:
{{
    "session_id": "{session_id}",
    "overall_status": "SUCCESS|PARTIAL|FAILURE",
    "summary": "Executive summary of refactoring",
    "statistics": {{
        "files_processed": {files_count},
        "files_improved": <count>,
        "files_unchanged": <count>,
        "files_failed": <count>,
        "average_score_improvement": <float>
    }},
    "highlights": ["Notable improvements"],
    "remaining_issues": ["Issues that couldn't be resolved"],
    "recommendations": ["Suggestions for future work"]
}}
"""

JUDGE_ERROR_ANALYSIS_PROMPT = """Analyze test failures and provide actionable feedback for the Fixer.

## Failed Tests:
{test_failures}

## Error Logs:
{error_logs}

## Current Code State:
```python
{current_code}
```

## Your Task:
Analyze the failures and provide specific, actionable feedback.

Provide as JSON:
{{
    "error_count": <number>,
    "error_types": ["categorized error types"],
    "root_causes": [
        {{
            "test": "test name",
            "cause": "why it failed",
            "fix_suggestion": "how to fix it",
            "affected_lines": [<line numbers>]
        }}
    ],
    "priority_order": ["ordered list of issues to fix"],
    "estimated_difficulty": "easy|medium|hard"
}}
"""
