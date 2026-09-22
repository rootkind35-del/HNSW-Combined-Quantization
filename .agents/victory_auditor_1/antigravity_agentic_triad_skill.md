# Antigravity Agentic Triad Workflow (Auditor Copy)

Implements the research-backed Antigravity Agentic Triad orchestration workflow with Dynamic Model Switching and Harness-R1 Optimization.
Separates concerns into Architect, Routine Worker, Complex Worker, Independent Reviewer, and Harness Engineer to eliminate self-validation loops and evolve the runtime harness dynamically.

Key principles applied to victory audit:
- Independent verification: The auditor is completely separated from the worker/implementer.
- No self-validation: Re-run all tests independently and inspect code directly.
- Guardrails & git diff inspection: Verify only intended files were modified/deleted and out-of-scope files were untouched.
