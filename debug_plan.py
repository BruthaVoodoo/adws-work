from scripts.adw_modules.plan_validator import cross_reference_plan_output, extract_executed_steps_from_output, parse_plan_steps
import logging

logging.basicConfig(level=logging.INFO)

plan = """# Chore: Add timestamped comment to README.md for ADW build pipeline verification

## Chore Description
This chore involves adding a simple timestamped comment to the project's README.md file...

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Examine Current README.md Structure
- Review the current README.md file to understand its structure and content

### Step 2: Generate Timestamp and Format Comment
- Generate a current timestamp in an appropriate format (ISO 8601 or similar)

### Step 3: Add Timestamped Comment to README.md
- Append the formatted timestamped comment to the end of the README.md file

### Step 4: Verify File Modification Detection
- Check that the README.md file is now showing as a modified/uncommitted file in git status

### Step 5: Validation and Testing
- Run the validation commands to ensure no regressions are introduced
"""

output = """
Appending a timestamped ADW verification HTML comment to the end of README.md and running the requested validation commands to confirm the change and test results.

✓ $ echo '--- Step 1: Current README tail ---' && tail -n 20 README.md || true
   TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
   printf "\n<!-- ADW Verification Test: %s -->\n" "$TIMESTAMP" >> README.md
   echo '--- Step 3: Appended comment (tail 5) ---' && tail -n 5 README.md || true...

Reviewing the README.md file content to ensure comment formatting is correct before committing. Then will commit the change and re-run validations.

✓ Read README.md

Replacing the malformed lines with a single correctly formatted timestamped comment and committing the change, then re-running validation commands.

✓ Edit README.md

✓ $ git add README.md && git commit -m "chore: add ADW verification timestamp to README.md" ||
    true

   echo '--- git status ---' && git --no-pager status || true...

Step summary: Appended a timestamped ADW verification HTML comment to README.md, committed the change, and ran validation commands.

Validation results:
- git status: README.md committed and branch ahead of remote by 2 commits.
"""

result = cross_reference_plan_output(plan, output)
print(f"Executed: {result.executed_steps}/{result.total_steps}")
print(f"Missing: {result.missing_steps}")
print(f"Steps: {[s.title for s in parse_plan_steps(plan)]}")
print(f"Executed List: {extract_executed_steps_from_output(output)}")