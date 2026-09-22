---
name: antigravity-agentic-triad
description: "Implements the research-backed Antigravity Agentic Triad orchestration workflow with Dynamic Model Switching and Harness-R1 Optimization (grounded in 21 arXiv papers including Harness-R1, MetaGPT, Reflexion, FrugalGPT, LATS, SWE-agent, ReAct, and ToT). Separates concerns into Architect, Routine Worker, Complex Worker, Independent Reviewer, and Harness Engineer to eliminate self-validation loops and evolve the runtime harness dynamically."
---

# Antigravity Agentic Triad Workflow

**Antigravity Agentic Triad** is a research-backed Agentic Skill designed for **Google Antigravity**, featuring **Dynamic Model Switching & Escalation** at runtime and **Evolutionary Harness Patching**. Grounded in 21 peer-reviewed AI agent research papers (**Harness-R1**, **MetaGPT**, **Reflexion**, **FrugalGPT**, **LATS**, **SWE-agent**, **ReAct**, **Tree of Thoughts**, **SWE-bench**, **RouteLLM**, etc.).

As the primary agent, you act as the **Architect**. You do not write implementation code directly. Instead, you delegate work via structured Standard Operating Procedure (SOP) packets and mandate a fresh, independent review process.

## 🔬 Grounding in Research Papers & Reddit Pain Points Solved

| Reddit Developer Pain Point | AI Coding Flaw | Triad Solution | Scientific Grounding Paper |
|---|---|---|---|
| **1. Silent Hallucinations & Stubs** | Writing empty `// TODO` blocks | Independent Test Adequacy Audit | **CRITIC** (*ICLR 2024*) & **Reflexion** (*2023*) |
| **2. Out-of-Scope Code Pollution** | Modifying unrelated files | ACI Guardrails & `git diff` checking | **SWE-agent** (*NeurIPS 2024*) |
| **3. Cascading Chat Hallucinations** | Chat dialogue causing logic drift | SOP 5-part task packet artifacts | **MetaGPT** (*ICLR 2024*) & **ChatDev** (*ACL 2024*) |
| **4. Token & Cost Explosion** | Querying heavy models for simple edits | Dynamic Model Cascade (`flash` -> `pro`) | **FrugalGPT** (*Stanford 2023*) & **RouteLLM** (*LMSYS 2024*) |
| **5. Infinite Retry Loops** | Repeatedly trying broken fixes | Episodic memory ($\Omega \le 3$) & MCTS pruning | **LATS** (*ICML 2024*) & **Self-Refine** (*NeurIPS 2023*) |
| **6. Context Blindness** | Missing multi-file imports | Explicit public interface contracts | **RepoCoder** (*EMNLP 2023*) & **InterCode** (*NeurIPS 2023*) |
| **7. Static Environment Failure** | Failing same edge cases repeatedly | Dynamic Harness Patching Loop | **Harness-R1** (*arXiv 2026*) |
