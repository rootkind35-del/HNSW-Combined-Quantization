# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: [none — teamwork routes from the description]

Finalize and audit the refactored Vector Search dashboard and backend pipeline on the `main` branch. The core integration, UI cleanup, and pipeline optimization (Milestones 1, 2, 3) were previously implemented, but the final independent audit was interrupted. Conduct a strict post-victory audit to ensure all UI routing metrics (Shard IDs, latency) are properly displayed, the pipeline (`run_pipeline.py`) uses the new IVF K-Means logic, and no redundant 3D assets or memmap logic remain. Fix any outstanding issues discovered during the audit.

Working directory: f:\ANN
Integrity mode: demo

## Requirements

### R1. Final Dashboard UI & Asset Audit
Ensure all bloated, unused resources from `dashboard/` (heavy unused CSS/JS, 3D engines) are completely removed. Verify that the UI code (`app.js`, `index.html`) cleanly displays search results, including Shard IDs hit, shards probed, and execution latency.

### R2. Pipeline Refactoring Audit
Verify that `scripts/run_pipeline.py` uses the new IVF K-Means clustering logic from the updated backend, seamlessly integrating with the `ShardedIVFHNSW` router, and contains zero monolithic graph building or `memmap` logic.

### R3. Preserved Data Configuration
Confirm that the existing dataset structure and data loading configurations remain completely intact and unaltered.

## Acceptance Criteria

### Codebase Cleanliness & UI Functionality
- [ ] An independent judge agent strictly verifies that redundant UI/dashboard script files are deleted and the core frontend runs without errors.
- [ ] The dashboard UI is manually or programmatically verified to ensure Shard routing metrics and execution latency are successfully wired and visible.

### Pipeline Execution
- [ ] An independent judge agent executes or reviews `scripts/run_pipeline.py` to confirm it initializes the `ShardedIVFHNSW` router correctly and passes adversarial checks for legacy code.

---
*Next: when approved → delegate via invoke_subagent (see Delegation Protocol)*
