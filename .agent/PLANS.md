# NovaBW ExecPlans

Use an ExecPlan for work that is likely to span multiple source files, introduce a new action family, change protocol/schema structure, refactor core runtime architecture, or require several debugging/test iterations.

Small registry-only capability additions do not need a separate ExecPlan when the implementation path is already established.

## Plan location

Create active plans under:

`.agent/plans/active/<short-name>.md`

Move completed plans to:

`.agent/plans/completed/<short-name>.md`

## Required sections

Each plan should contain:

1. **Goal**
   - concrete user-visible/research outcome

2. **Current state**
   - relevant files
   - validated baseline
   - known constraints

3. **Design**
   - architecture/API choices
   - why the chosen approach fits NovaBW

4. **Implementation steps**
   - ordered, testable milestones

5. **Validation**
   - targeted tests
   - core regression
   - exact success criteria

6. **Risks / rollback**
   - likely failure modes
   - how working state is preserved

7. **Progress**
   - checked items and important discoveries

8. **Result**
   - files changed
   - tests run
   - PASS/FAIL
   - commit SHA
   - remaining debt

## Execution rules

- Keep the plan updated as facts change.
- Record exact failing logs when they alter the approach.
- Do not silently weaken tests to obtain PASS.
- Prefer state-based validation over command acceptance.
- Run targeted tests before broad regression.
- Preserve unrelated local changes.
- Do not force-push or rewrite history.
- A plan is complete only when its stated validation criteria pass.
