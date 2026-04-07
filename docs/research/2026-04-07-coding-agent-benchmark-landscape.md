# Coding-Agent Benchmark Landscape Notes

- **Date:** 2026-04-07
- **Project:** OpenBench
- **Purpose:** Capture current research conclusions about other coding-agent benchmarking systems and extract implications for OpenBench roadmap decisions.

## Executive Summary

There is no single canonical benchmark for coding agents today. The current ecosystem splits across several benchmark families with different goals, scoring models, cost structures, and contamination risks.

The most useful high-level taxonomy is:

1. **Repo-level issue resolution** — SWE-bench family
2. **Terminal / long-horizon agent execution** — Terminal-Bench, RALPHBench
3. **Repository-level code generation / dependency-aware evaluation** — RepoExec, SWE-PolyBench
4. **Broader software-engineering workflow benchmarks** — DevBench / DevEval, GitTaskBench, RExBench, OmniCode
5. **General agent / deterministic workflow benchmarks** — AgentBench-style systems

The main caution is that leaderboard numbers across these systems are **not directly comparable**. Differences in task freshness, contamination controls, horizon length, runtime environment, evaluation harness, and budget/scaffold assumptions make “X% on benchmark A” fundamentally different from “X% on benchmark B.”

## Benchmark Families

### 1. SWE-bench / SWE-bench Verified

**What it measures**
- Real GitHub issue resolution inside real repositories
- Ability to produce patches that satisfy hidden/held-out test expectations

**Evaluation style**
- Test-based patch validation
- `FAIL_TO_PASS` / `PASS_TO_PASS` framing

**Strengths**
- Closest thing to a canonical repo-level software-fixing benchmark
- Strong grounding in real maintenance tasks
- Very useful as a reference point for serious coding-agent evaluation

**Weaknesses / blind spots**
- Heavy execution cost and environment complexity
- Original dataset quality variability motivated Verified subset work
- Not ideal for lightweight local benchmarking loops

**OpenBench takeaway**
- Borrow the discipline of explicit test-based success criteria
- Treat SWE-bench-style evaluation as a later heavy-weight tier, not the first expansion beyond runtime

**Sources**
- https://github.com/SWE-bench/SWE-bench
- https://openai.com/index/introducing-swe-bench-verified/

### 2. SWE-PolyBench

**What it measures**
- Multi-language repository-level issue solving / repair behavior
- Retrieval quality in addition to task success

**Evaluation style**
- Pass/fail style task metrics
- Retrieval/node metrics for repository understanding

**Strengths**
- Expands beyond Python-centric repo evaluation
- Good model for multi-language agent assessment
- Explicitly values retrieval quality, not just final patch success

**Weaknesses / blind spots**
- Expensive and operationally heavy
- Harder to keep as a lightweight reproducible local loop

**OpenBench takeaway**
- Useful reference for a later multi-language repo-task tier
- Suggests OpenBench should eventually expose retrieval/usefulness signals in addition to task success

**Source**
- https://github.com/amazon-science/SWE-PolyBench

### 3. DevBench / DevEval

**What it measures**
- Broader software-engineering lifecycle work rather than only bug fixing
- Design, implementation, environment setup, testing, acceptance checking, etc.

**Evaluation style**
- Composite task evaluation across multiple software-development stages

**Strengths**
- Better reflects the real breadth of software engineering
- Useful if the goal is “software engineer agent” rather than “issue repair agent”

**Weaknesses / blind spots**
- More complex to reason about
- Harder to keep deterministic and cheap
- Less suited to narrow runtime-first benchmark positioning

**OpenBench takeaway**
- Good long-term roadmap inspiration
- Not the right immediate next step after runtime reporting

**Source**
- https://github.com/open-compass/DevEval

### 4. GitTaskBench

**What it measures**
- Repository understanding, environment setup, incremental coding/bug-fixing, and task delivery
- Emphasizes efficiency/cost-aware evaluation

**Evaluation style**
- Practical repo tasks with an explicit cost-aware perspective

**Strengths**
- Closer to realistic repo workflows than pure function-generation benchmarks
- Highlights the importance of cost-aware benchmarking

**Weaknesses / blind spots**
- Harness/scaffold choices can heavily influence results
- Still less standardized than SWE-bench family systems

**OpenBench takeaway**
- Strong argument for later cost-aware reporting in OpenBench
- Useful reference for practical repo-task benchmark design

**Source**
- https://github.com/QuantaAlpha/GitTaskBench

### 5. Terminal-Bench

**What it measures**
- Multi-step terminal task execution by coding/agentic systems
- Software engineering plus other terminal-heavy workflows

**Evaluation style**
- Task suites executed inside terminal/tool-use environments

**Strengths**
- Strong fit for CLI and tool-using agents
- Captures orchestration/tool-use ability better than patch-only benchmarks

**Weaknesses / blind spots**
- Less purely “coding benchmark” and more “terminal workflow benchmark”
- Harder to compare to repo repair or codegen-only systems

**OpenBench takeaway**
- Best reference for a later orchestration/terminal tier
- Not the immediate next step, but strategically important

**Source**
- https://www.tbench.ai/benchmarks

### 6. RALPHBench

**What it measures**
- Extremely long-horizon software-engineering tasks

**Evaluation style**
- Very long tasks stressing planning, persistence, and end-to-end completion

**Strengths**
- Good for frontier-agent long-horizon evaluation
- More realistic for “agent as persistent engineer” scenarios

**Weaknesses / blind spots**
- Very expensive and slow
- Hard to make lightweight and reproducible
- Unsuitable as an early-stage local benchmark layer

**OpenBench takeaway**
- Long-term inspiration only for now
- Too costly to be the next practical benchmark step

**Source**
- https://www.ralphbench.org/

### 7. LiveCodeBench

**What it measures**
- Contamination-resistant code evaluation
- Freshness-aware code problem solving and execution

**Evaluation style**
- Time-windowed benchmark logic
- `pass@k`-style problem solving metrics

**Strengths**
- Strong contamination/freshness story
- Useful when guarding against benchmark overfitting and training leakage

**Weaknesses / blind spots**
- Not repo-maintenance-oriented in the same way as SWE-bench
- Less about multi-file repository repair

**OpenBench takeaway**
- OpenBench should consider adding freshness/time-window metadata later
- Especially useful for future benchmark result annotation and trust signaling

**Source**
- https://github.com/LiveCodeBench/LiveCodeBench

### 8. RepoExec

**What it measures**
- Repository-level code generation with executability and dependency-aware correctness

**Evaluation style**
- Focus on whether generated code works in real repository contexts
- Cross-file / dependency-aware evaluation emphasis

**Strengths**
- Good fit for repository-level generation and dependency-sensitive tasks
- Strong “executability” framing

**Weaknesses / blind spots**
- More codegen/repo-exec focused than full autonomous software-agent workflow

**OpenBench takeaway**
- Good inspiration for cross-file and dependency-aware metrics
- Suggests OpenBench should not stop at top-line task pass rates later

**Source**
- https://github.com/FSoft-AI4Code/RepoExec

### 9. CCBench

**What it measures**
- Real-world coding tasks on small codebases that are intentionally outside common training exposure

**Evaluation style**
- Practical codebase tasks with deterministic checking

**Strengths**
- Good realism/tractability balance
- Excellent inspiration for small realistic coding-task tiers

**Weaknesses / blind spots**
- Not a substitute for large-repo maintenance benchmarks
- Focuses on smaller codebases rather than heavy repo ecosystems

**OpenBench takeaway**
- Strong reference for OpenBench’s likely “practical deterministic task” tier
- Probably one of the best immediate inspirations after runtime work

**Source**
- https://ccbench.org/

### 10. AgentBench-style systems

**What it measures**
- Broader agent behavior in deterministic workflows, often beyond just coding

**Evaluation style**
- Rule-based / deterministic scoring across varied environments

**Strengths**
- Helpful for setup and workflow reproducibility ideas
- Trace-driven scoring can reduce judge ambiguity

**Weaknesses / blind spots**
- Not a pure coding benchmark family
- Too broad if OpenBench wants to stay coding-centric

**OpenBench takeaway**
- OpenBench can borrow trace and deterministic scoring ideas
- But should avoid becoming a general-purpose agent benchmark too early

**Sources**
- https://www.agentbench.app/
- https://github.com/THUDM/AgentBench

### 11. SWE-rebench

**What it measures**
- Ongoing leaderboard/evaluation infrastructure around SWE-style tasks
- Emphasizes decontamination, cost, and efficiency reporting

**Evaluation style**
- Leaderboard plus operational benchmark metadata

**Strengths**
- Strong example of reporting more than just pass rate
- Includes cost/problem, tokens/problem, and contamination-oriented framing

**Weaknesses / blind spots**
- More evaluation ops / leaderboard layer than a fundamentally new benchmark family

**OpenBench takeaway**
- Very relevant for future OpenBench reporting columns and dashboard design
- Cost and token metadata should likely be first-class later

**Source**
- https://swe-rebench.com/

### 12. OmniCode and RExBench (emerging / specialized)

**What they suggest**
- Benchmarks are expanding beyond bug-fix and toy generation into broader software engineering and research-extension tasks

**OpenBench takeaway**
- The ecosystem is moving toward more realistic, process-heavy tasks
- OpenBench should keep modular expansion paths rather than overfitting to runtime forever

**Sources**
- https://arxiv.org/abs/2602.02262
- https://rexbench.com/

## Cross-System Comparison Notes

### Major comparison caution

Do **not** compare leaderboard numbers from these systems as if they were interchangeable.

Important dimensions that differ:
- contamination/freshness risk
- public vs private / held-out codebases
- repo repair vs terminal workflow vs code generation
- task horizon length
- determinism of the environment
- hidden test rigor
- influence of harness/tooling/scaffold budget
- whether the benchmark reflects raw model quality or full system engineering quality

### One especially important mismatch to avoid

`CCBench` and `AgentBench` should not be grouped as if they were the same benchmark class:
- `CCBench` is fundamentally a coding benchmark on small real codebases
- `AgentBench` is a broader agent benchmark, not a private-codebase coding benchmark

Likewise, `LiveCodeBench` and `RepoExec` are not the same thing:
- `LiveCodeBench` emphasizes contamination-resistant coding evaluation
- `RepoExec` emphasizes repository-level executable correctness and dependency-aware behavior

## Implications for OpenBench

### What OpenBench should keep as its niche right now

OpenBench’s current strengths are:
- lightweight runtime measurement
- reproducible artifacts
- static report generation
- local, inspectable execution

This is a useful niche because many heavyweight benchmark systems are costly, slow, or hard to reproduce locally.

### Recommended OpenBench expansion order

1. **Strengthen runtime layer**
   - repeat runs / variance
   - cold vs warm
   - better install-footprint semantics
   - richer report output

2. **Add deterministic practical coding tasks**
   - inspired by CCBench / small realistic repo tasks
   - should remain cheap and reproducible

3. **Add repo-level maintenance tier**
   - SWE-bench-style tasks later
   - probably smaller curated subset first

4. **Add terminal/orchestration tier**
   - inspired by Terminal-Bench
   - multi-step workflow execution rather than just patch success

5. **Add long-horizon or specialized tiers later**
   - RALPHBench / RExBench style work only after stronger infrastructure exists

### Specific ideas OpenBench should borrow

- **From SWE-bench**: strict test-based success definitions
- **From SWE-PolyBench / RepoExec**: retrieval and cross-file usefulness metrics
- **From LiveCodeBench**: freshness / contamination-aware metadata
- **From SWE-rebench**: cost/problem, tokens/problem, cache ratio reporting
- **From CCBench**: realistic but tractable small-codebase task design
- **From Terminal-Bench**: terminal/tool-use workflow evaluation

## Recommended Next Research / Planning Questions

1. What is the best first deterministic practical task tier for OpenBench after runtime?
2. Should OpenBench add cost/token metadata to its current runtime manifest/report schema now or later?
3. What minimal retrieval/cross-file metrics are worth adding once repo tasks exist?
4. How should OpenBench annotate contamination/freshness once live or recent tasks are introduced?

## Sources

- SWE-bench: https://github.com/SWE-bench/SWE-bench
- SWE-bench Verified announcement: https://openai.com/index/introducing-swe-bench-verified/
- SWE-PolyBench: https://github.com/amazon-science/SWE-PolyBench
- DevEval / DevBench: https://github.com/open-compass/DevEval
- GitTaskBench: https://github.com/QuantaAlpha/GitTaskBench
- Terminal-Bench: https://www.tbench.ai/benchmarks
- RALPHBench: https://www.ralphbench.org/
- LiveCodeBench: https://github.com/LiveCodeBench/LiveCodeBench
- RepoExec: https://github.com/FSoft-AI4Code/RepoExec
- CCBench: https://ccbench.org/
- AgentBench app: https://www.agentbench.app/
- AgentBench repo: https://github.com/THUDM/AgentBench
- SWE-rebench: https://swe-rebench.com/
- OmniCode: https://arxiv.org/abs/2602.02262
- RExBench: https://rexbench.com/
