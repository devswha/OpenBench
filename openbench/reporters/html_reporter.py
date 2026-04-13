from __future__ import annotations

from html import escape
from pathlib import Path

from openbench.metrics.statistics import (
    TaskRunResult,
    compute_task_stats,
    compute_difficulty_stats,
    compute_category_stats,
)
from openbench.reporters.models import (
    AgentCategoryMetrics,
    AgentDifficultyMetrics,
    AgentReport,
    PracticalAgentReport,
    PracticalTaskResult,
    ReportMetric,
    RuntimeReport,
    RUNTIME_METRICS,
)


class StaticHtmlReporter:
    def render(self, report: RuntimeReport) -> str:
        summary_cards = self._render_summary_cards(report)
        environment_rows = "".join(
            f"<tr><th>{escape(str(key))}</th><td>{escape(str(value))}</td></tr>"
            for key, value in sorted(report.environment.items())
        )
        runtime_comparison_rows = "".join(self._render_runtime_comparison_row(agent) for agent in report.agents)
        runtime_agent_cards = "".join(self._render_runtime_agent_card(agent) for agent in report.agents)
        practical_summary_rows = "".join(
            self._render_practical_summary_row(agent) for agent in report.practical_agents
        )
        practical_agent_cards = "".join(
            self._render_practical_agent_card(agent) for agent in report.practical_agents
        )
        metric_tab_panels = "".join(
            self._render_metric_tab_panel(report, metric) for metric in RUNTIME_METRICS
        )
        practical_panel = self._render_practical_tab_panel(report)
        tasks_panel = self._render_tasks_tab_panel(report)
        tab_buttons = self._render_tab_buttons(report)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>OpenBench Benchmark Report — {escape(report.run_id)}</title>
  <style>
    /* ── Design tokens (dark-only) ── */
    :root {{
      --bg:         #0d0d0d;
      --panel:      #161616;
      --panel-alt:  #1e1e1e;
      --text:       #e5e5e5;
      --muted:      #888;
      --border:     #2a2a2a;
      --accent:     #3b82f6;
      --ok-text:    #4ade80;
      --warn-text:  #fbbf24;
      --fail-text:  #f87171;
    }}
    /* ── Reset & base ── */
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }}
    main {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 64px;
    }}
    /* ── Typography ── */
    h1 {{
      margin: 0 0 4px;
      font-size: 1.25rem;
      font-weight: 600;
      color: var(--text);
    }}
    h2 {{
      margin: 0 0 12px;
      font-size: 1rem;
      font-weight: 600;
      color: var(--text);
    }}
    h3 {{
      margin: 0 0 8px;
      font-size: 0.9rem;
      font-weight: 600;
      color: var(--text);
    }}
    h4 {{
      margin: 0 0 8px;
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text);
    }}
    p {{
      margin: 0 0 6px;
      color: var(--muted);
      font-size: 0.875rem;
    }}
    p strong {{ color: var(--text); }}
    li {{ color: var(--muted); font-size: 0.875rem; }}
    code {{
      font-family: ui-monospace, monospace;
      font-size: 0.8em;
      background: var(--panel-alt);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 1px 5px;
      color: var(--accent);
    }}
    /* ── Layout ── */
    .grid {{ display: grid; gap: 12px; }}
    .summary-grid {{ grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }}
    .agent-grid {{ grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
    /* ── Cards ── */
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 16px;
    }}
    /* ── Tables ── */
    table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
    thead th {{
      text-align: left;
      padding: 8px 12px;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--muted);
      background: var(--panel-alt);
      border-bottom: 1px solid var(--border);
    }}
    tbody td, tbody th {{
      text-align: left;
      padding: 8px 12px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
      font-size: 0.8rem;
    }}
    tbody td {{ font-family: ui-monospace, monospace; font-variant-numeric: tabular-nums; }}
    tbody tr:last-child td,
    tbody tr:last-child th {{ border-bottom: none; }}
    tbody th {{ font-weight: 600; color: var(--text); font-family: inherit; font-size: 0.875rem; }}
    /* ── Metric & task lists ── */
    .metric-list, .task-list {{ list-style: none; padding: 0; margin: 0; }}
    .metric-list li, .task-list li {{
      margin-bottom: 12px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border);
    }}
    .metric-list li:last-child, .task-list li:last-child {{
      margin-bottom: 0;
      padding-bottom: 0;
      border-bottom: none;
    }}
    .metric-label, .task-label {{
      color: var(--text);
      font-weight: 600;
      font-size: 0.875rem;
    }}
    .metric-list div, .task-list div {{
      font-family: ui-monospace, monospace;
      font-size: 0.78rem;
      color: var(--muted);
      margin-top: 2px;
    }}
    /* ── Chips / badges ── */
    .chip {{
      display: inline-flex;
      align-items: center;
      padding: 1px 6px;
      border-radius: 4px;
      font-size: 0.7rem;
      font-weight: 600;
      margin-left: 6px;
      vertical-align: middle;
      border: 1px solid;
    }}
    .chip-ok   {{ color: var(--ok-text);   border-color: #166534; }}
    .chip-fail {{ color: var(--fail-text); border-color: #7f1d1d; }}
    .chip-warn {{ color: var(--warn-text); border-color: #78350f; }}
    /* ── Bar chart ── */
    .bar-track {{
      width: 100%;
      background: var(--panel-alt);
      border: 1px solid var(--border);
      border-radius: 2px;
      overflow: hidden;
      height: 8px;
      margin-top: 6px;
    }}
    .bar-fill {{
      height: 8px;
      background: var(--accent);
    }}
    /* ── Notes / muted text ── */
    .note {{
      font-size: 0.8rem;
      color: var(--muted);
      line-height: 1.6;
    }}
    .note div {{ margin-bottom: 4px; }}
    .note strong {{ color: var(--text); }}
    .failure {{
      color: var(--fail-text);
      font-size: 0.78rem;
      font-family: ui-monospace, monospace;
    }}
    /* ── Tab navigation ── */
    .tab-nav {{
      display: flex;
      gap: 0;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 6px;
      margin-bottom: 20px;
      overflow-x: auto;
      scrollbar-width: none;
      position: sticky;
      top: 8px;
      z-index: 10;
    }}
    .tab-nav::-webkit-scrollbar {{ display: none; }}
    .tab-btn {{
      flex-shrink: 0;
      padding: 8px 16px;
      border: none;
      border-bottom: 2px solid transparent;
      border-radius: 0;
      background: transparent;
      color: var(--muted);
      font-size: 0.85rem;
      font-weight: 500;
      cursor: pointer;
      white-space: nowrap;
      font-family: inherit;
      line-height: 1.4;
    }}
    .tab-btn:hover {{
      color: var(--text);
    }}
    .tab-btn.active {{
      color: var(--accent);
      border-bottom-color: var(--accent);
      font-weight: 600;
    }}
    /* ── Tab panels ── */
    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; }}
    /* ── Metric description ── */
    .metric-description {{
      font-size: 0.875rem;
      line-height: 1.6;
      margin: 0;
      color: var(--muted);
    }}
    .metric-description strong {{ color: var(--text); }}
    /* ── Metric detail grid/cards ── */
    .metric-detail-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 12px;
      margin-top: 12px;
    }}
    .metric-detail-card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 14px;
    }}
    .metric-detail-row {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      padding: 6px 0;
      border-bottom: 1px solid var(--border);
      font-size: 0.8rem;
      gap: 12px;
    }}
    .metric-detail-row:last-child {{ border-bottom: none; padding-bottom: 0; }}
    .metric-detail-key {{ color: var(--muted); flex-shrink: 0; }}
    .metric-detail-val {{
      color: var(--text);
      font-weight: 600;
      font-variant-numeric: tabular-nums;
      font-family: ui-monospace, monospace;
      font-size: 0.78rem;
      text-align: right;
    }}
    /* ── Bar chart label row ── */
    .bar-label-row {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 8px;
    }}
    .bar-label-agent {{
      font-weight: 600;
      font-size: 0.875rem;
      color: var(--text);
    }}
    .bar-label-value {{
      font-family: ui-monospace, monospace;
      font-size: 0.78rem;
      color: var(--muted);
      white-space: nowrap;
    }}
    /* ── Responsive ── */
    @media (max-width: 600px) {{
      .tab-btn {{ padding: 7px 12px; font-size: 0.8rem; }}
      main {{ padding: 16px 12px 48px; }}
    }}
  </style>
</head>
<body>
  <main>
    <nav class="tab-nav" role="tablist" aria-label="Report sections">
      {tab_buttons}
    </nav>

    <div id="tab-overview" class="tab-panel" role="tabpanel" aria-labelledby="btn-overview">
      <section class="grid summary-grid">
        {summary_cards}
      </section>

      <section class="card" style="margin-top: 20px;">
        <h2>Environment</h2>
        <table><tbody>{environment_rows}</tbody></table>
      </section>

      {self._render_runtime_overview(report, runtime_comparison_rows, runtime_agent_cards)}
      {self._render_practical_overview(report, practical_summary_rows, practical_agent_cards)}

      <section class="card" style="margin-top: 20px;">
        <h2>Notes</h2>
        <p class="note">
          Raw values remain visible alongside normalized scores. Lower values are better for startup, memory,
          and binary-size metrics. Binary-size currently reflects the resolved command path footprint, which may
          be a launcher wrapper rather than the full installation size.
        </p>
      </section>
    </div>

    {metric_tab_panels}
    {practical_panel}
    {tasks_panel}
  </main>

  <script>
    (function () {{
      var TABS = Array.from(document.querySelectorAll('.tab-btn')).map(function (b) {{ return b.dataset.tab; }});
      function activate(tabId) {{
        document.querySelectorAll('.tab-btn').forEach(function (btn) {{
          btn.classList.toggle('active', btn.dataset.tab === tabId);
          btn.setAttribute('aria-selected', btn.dataset.tab === tabId ? 'true' : 'false');
        }});
        document.querySelectorAll('.tab-panel').forEach(function (panel) {{
          panel.classList.toggle('active', panel.id === 'tab-' + tabId);
        }});
      }}
      function getActiveFromHash() {{
        var hash = window.location.hash.replace('#', '');
        return TABS.indexOf(hash) !== -1 ? hash : 'overview';
      }}
      document.querySelectorAll('.tab-btn').forEach(function (btn) {{
        btn.addEventListener('click', function () {{
          var tabId = btn.dataset.tab;
          history.replaceState(null, '', '#' + tabId);
          activate(tabId);
        }});
      }});
      window.addEventListener('hashchange', function () {{ activate(getActiveFromHash()); }});
      activate(getActiveFromHash());
    }})();
  </script>
</body>
</html>
"""

    def write(self, report: RuntimeReport, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render(report))
        return output_path

    def _render_tab_buttons(self, report: RuntimeReport) -> str:
        tabs = [("overview", "Overview")]
        if report.agents:
            tabs.extend((metric.key.replace("_", "-"), metric.label) for metric in RUNTIME_METRICS)
        if report.practical_agents:
            tabs.append(("practical", "Practical"))
            tabs.append(("tasks", "Tasks"))
        return "\n      ".join(
            f'<button class="tab-btn" id="btn-{escape(tab_id)}" role="tab" '
            f'data-tab="{escape(tab_id)}" aria-selected="false" '
            f'aria-controls="tab-{escape(tab_id)}">{escape(tab_label)}</button>'
            for tab_id, tab_label in tabs
        )

    def _render_summary_cards(self, report: RuntimeReport) -> str:
        suite_text = ", ".join(report.suites) if report.suites else report.suite
        total_agents = sorted({a.agent_name for a in report.agents} | {a.agent_name for a in report.practical_agents})
        practical_task_count = sum(agent.summary.get("task_count", 0) for agent in report.practical_agents)
        runtime_mode = report.runtime_execution_environment.get("mode", "n/a")
        practical_mode = report.practical_execution_environment.get("mode", "n/a")
        return f"""<article class="card">
        <h1>OpenBench Benchmark Report</h1>
        <p>Run ID: <strong>{escape(report.run_id)}</strong></p>
      </article>
      <article class="card">
        <h2>Suites</h2>
        <p><strong>{escape(suite_text)}</strong></p>
      </article>
      <article class="card">
        <h2>Agents</h2>
        <p><strong>{len(total_agents)}</strong></p>
      </article>
      <article class="card">
        <h2>Practical tasks</h2>
        <p><strong>{practical_task_count}</strong></p>
      </article>
      <article class="card">
        <h2>Runtime mode</h2>
        <p><strong>{escape(str(runtime_mode))}</strong></p>
      </article>
      <article class="card">
        <h2>Practical mode</h2>
        <p><strong>{escape(str(practical_mode))}</strong></p>
      </article>
      <article class="card">
        <h2>Timestamp</h2>
        <p><strong>{escape(report.timestamp)}</strong></p>
      </article>"""

    def _render_runtime_overview(self, report: RuntimeReport, comparison_rows: str, agent_cards: str) -> str:
        if not report.agents:
            return ""
        return f"""
      <section class="card" style="margin-top: 20px;">
        <h2>Runtime comparison</h2>
        <table>
          <thead>
            <tr>
              <th>Agent</th>
              <th>Startup</th>
              <th>Memory</th>
              <th>Binary size</th>
            </tr>
          </thead>
          <tbody>{comparison_rows}</tbody>
        </table>
      </section>

      <section style="margin-top: 20px;">
        <h2>Runtime agent cards</h2>
        <div class="grid agent-grid">{agent_cards}</div>
      </section>
"""

    def _render_practical_overview(
        self,
        report: RuntimeReport,
        summary_rows: str,
        agent_cards: str,
    ) -> str:
        if not report.practical_agents:
            return ""
        mode_details = ""
        if report.practical_execution_environment:
            parts = []
            for key in ("mode", "base_image", "agent_image", "setup_overhead_ms"):
                value = report.practical_execution_environment.get(key)
                if value not in (None, "", {}):
                    parts.append(f"<div><strong>{escape(key)}</strong>: {escape(str(value))}</div>")
            if parts:
                mode_details = f"<div class=\"note\">{''.join(parts)}</div>"
        return f"""
      <section class="card" style="margin-top: 20px;">
        <h2>Practical task summary</h2>
        {mode_details}
        <table>
          <thead>
            <tr>
              <th>Agent</th>
              <th>Successful tasks</th>
              <th>Failed tasks</th>
              <th>Total tasks</th>
            </tr>
          </thead>
          <tbody>{summary_rows}</tbody>
        </table>
      </section>

      <section style="margin-top: 20px;">
        <h2>Practical task cards</h2>
        <div class="grid agent-grid">{agent_cards}</div>
      </section>
"""

    def _render_runtime_agent_card(self, agent_report: AgentReport) -> str:
        metrics = "".join(self._render_metric_list_item(metric) for metric in agent_report.metrics)
        return f"""
<article class="card">
  <h3>{escape(agent_report.display_name)}</h3>
  <p>{escape(agent_report.agent_name)}</p>
  <ul class="metric-list">{metrics}</ul>
</article>
"""

    def _render_metric_list_item(self, metric: ReportMetric) -> str:
        status_class = "chip-ok" if metric.available and metric.status == "success" else "chip-fail"
        status_text = "OK" if metric.available and metric.status == "success" else metric.status.upper()
        detail_html = f'<div class="failure">Error: {escape(metric.error_message)}</div>' if metric.error_message else ""
        return f"""
<li>
  <span class="metric-label">{escape(metric.label)}</span>
  <span class="chip {status_class}">{escape(status_text)}</span>
  <div>Raw: {escape(metric.formatted_raw_value)}</div>
  <div>Normalized score: {escape(metric.formatted_score)}</div>
  {detail_html}
</li>
"""

    def _render_runtime_comparison_row(self, agent_report: AgentReport) -> str:
        metrics = {metric.key: metric for metric in agent_report.metrics}
        return f"""
<tr>
  <th>{escape(agent_report.agent_name)}</th>
  <td>{self._render_table_metric(metrics['startup_ms'])}</td>
  <td>{self._render_table_metric(metrics['memory_mb'])}</td>
  <td>{self._render_table_metric(metrics['binary_size_mb'])}</td>
</tr>
"""

    def _render_table_metric(self, metric: ReportMetric) -> str:
        text = f"{metric.formatted_raw_value} · score {metric.formatted_score}"
        if metric.error_message:
            text += f" · {metric.error_message}"
        return escape(text)

    def _render_metric_tab_panel(self, report: RuntimeReport, metric_spec) -> str:
        if not report.agents:
            return ""
        metric_id = metric_spec.key.replace("_", "-")
        bars = []
        detail_cards = []
        for agent_report in report.agents:
            metric = next(metric for metric in agent_report.metrics if metric.key == metric_spec.key)
            width = max(0.0, min(metric.normalized_score or 0.0, 100.0))
            bars.append(
                f"""
<div style="margin-bottom: 16px;">
  <div class="bar-label-row">
    <span class="bar-label-agent">{escape(agent_report.agent_name)}</span>
    <span class="bar-label-value">{escape(metric.formatted_raw_value)} &middot; score {escape(metric.formatted_score)}</span>
  </div>
  <div class="bar-track"><div class="bar-fill" style="width: {width:.2f}%"></div></div>
</div>
"""
            )
            status_class = "chip-ok" if metric.available and metric.status == "success" else "chip-fail"
            status_text = "OK" if metric.available and metric.status == "success" else metric.status.upper()
            error_row = (
                f"""
          <div class="metric-detail-row">
            <span class="metric-detail-key">Error</span>
            <span class="metric-detail-val failure">{escape(metric.error_message)}</span>
          </div>
"""
                if metric.error_message
                else ""
            )
            detail_cards.append(
                f"""
        <article class="metric-detail-card">
          <h4>{escape(agent_report.display_name)} <span class="chip {status_class}">{escape(status_text)}</span></h4>
          <div class="metric-detail-row">
            <span class="metric-detail-key">Raw value</span>
            <span class="metric-detail-val">{escape(metric.formatted_raw_value)}</span>
          </div>
          <div class="metric-detail-row">
            <span class="metric-detail-key">Normalized score</span>
            <span class="metric-detail-val">{escape(metric.formatted_score)}</span>
          </div>
          {error_row}
        </article>"""
            )
        return f"""
    <div id="tab-{metric_id}" class="tab-panel" role="tabpanel" aria-labelledby="btn-{metric_id}">
      <article class="card" style="margin-bottom: 16px;">
        <p class="metric-description">{escape(metric_spec.description)}</p>
      </article>
      <article class="card">
        <h2>{escape(metric_spec.label)}</h2>
        {''.join(bars)}
      </article>
      <div class="metric-detail-grid">{''.join(detail_cards)}</div>
    </div>
"""

    def _render_practical_tab_panel(self, report: RuntimeReport) -> str:
        if not report.practical_agents:
            return ""
        cards = "".join(self._render_practical_agent_card(agent) for agent in report.practical_agents)
        comparison_table = self._render_practical_comparison_table(report)
        difficulty_sections = self._render_difficulty_sections(report)
        category_heatmap = self._render_category_heatmap(report)
        return f"""
    <div id="tab-practical" class="tab-panel" role="tabpanel" aria-labelledby="btn-practical">
      <article class="card" style="margin-bottom: 16px;">
        <p class="metric-description">Each agent receives the same prompt and works in an identical sandboxed environment. Three independent axes are measured: <strong>correctness</strong> (did the task pass?), <strong>duration</strong> (time to completion), and <strong>token usage</strong> (cost efficiency). Lower duration and fewer tokens are better, given equal correctness.</p>
      </article>
      {difficulty_sections}
      {category_heatmap}
      {comparison_table}
      <div class="grid agent-grid" style="margin-top: 16px;">{cards}</div>
    </div>
"""

    def _compute_agent_difficulty_metrics(self, report: RuntimeReport) -> list[AgentDifficultyMetrics]:
        """Compute difficulty-level metrics per agent from existing PracticalAgentReport data."""
        results: list[AgentDifficultyMetrics] = []
        for agent in report.practical_agents:
            # Convert PracticalTaskResult objects to TaskRunResult objects
            runs: list[TaskRunResult] = []
            for task in agent.tasks:
                total_tokens = None
                if task.token_usage:
                    raw = task.token_usage.get("total_tokens")
                    if raw is not None and isinstance(raw, (int, float)):
                        total_tokens = int(raw)
                runs.append(TaskRunResult(
                    task_name=task.task_name,
                    run_index=0,
                    success=(task.status == "success"),
                    duration_ms=task.duration_ms,
                    total_tokens=total_tokens,
                    difficulty=getattr(task, "difficulty", None) or "easy",
                    category=getattr(task, "category", None) or "bugfix",
                ))

            if not runs:
                continue

            # Group by task name and compute per-task stats
            task_runs: dict[str, list[TaskRunResult]] = {}
            for run in runs:
                task_runs.setdefault(run.task_name, []).append(run)
            task_stats_list = [compute_task_stats(task_run_list) for task_run_list in task_runs.values()]

            # Compute per-difficulty stats and map to AgentDifficultyMetrics
            difficulties_present = sorted({ts.difficulty for ts in task_stats_list})
            has_multi_run = any(len(v) > 1 for v in task_runs.values())
            for difficulty in difficulties_present:
                ds = compute_difficulty_stats(task_stats_list, difficulty)
                if ds.task_count == 0:
                    continue
                results.append(AgentDifficultyMetrics(
                    agent_name=agent.agent_name,
                    difficulty=ds.difficulty,
                    task_count=ds.task_count,
                    pass_at_1=ds.pass_at_1_rate,
                    pass_at_5=ds.pass_at_n_rate if has_multi_run else None,
                    pass_at_5_strict=ds.pass_at_n_strict_rate if has_multi_run else None,
                    tokens_per_success=ds.mean_tokens_per_success,
                    duration_per_success=ds.median_duration_per_success,
                ))
        return results

    def _compute_agent_category_metrics(self, report: RuntimeReport) -> list[AgentCategoryMetrics]:
        """Compute Pass@1 per agent per category per difficulty from existing data."""
        results: list[AgentCategoryMetrics] = []
        for agent in report.practical_agents:
            # Convert PracticalTaskResult objects to TaskRunResult objects
            runs: list[TaskRunResult] = []
            for task in agent.tasks:
                total_tokens = None
                if task.token_usage:
                    raw = task.token_usage.get("total_tokens")
                    if raw is not None and isinstance(raw, (int, float)):
                        total_tokens = int(raw)
                runs.append(TaskRunResult(
                    task_name=task.task_name,
                    run_index=0,
                    success=(task.status == "success"),
                    duration_ms=task.duration_ms,
                    total_tokens=total_tokens,
                    difficulty=getattr(task, "difficulty", None) or "easy",
                    category=getattr(task, "category", None) or "bugfix",
                ))

            if not runs:
                continue

            # Group by task name and compute per-task stats
            task_runs: dict[str, list[TaskRunResult]] = {}
            for run in runs:
                task_runs.setdefault(run.task_name, []).append(run)
            task_stats_list = [compute_task_stats(task_run_list) for task_run_list in task_runs.values()]

            # Use compute_category_stats and map to AgentCategoryMetrics
            for cs in compute_category_stats(task_stats_list):
                results.append(AgentCategoryMetrics(
                    agent_name=agent.agent_name,
                    difficulty=cs.difficulty,
                    category=cs.category,
                    pass_at_1=cs.pass_at_1_rate,
                ))
        return results

    @staticmethod
    def _format_duration_ms(duration_ms: float | None) -> str:
        if duration_ms is None:
            return "—"
        if duration_ms < 1000:
            return f"{duration_ms:.0f} ms"
        seconds = duration_ms / 1000.0
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        remaining = seconds % 60
        return f"{minutes}m {remaining:.0f}s"

    def _render_difficulty_sections(self, report: RuntimeReport) -> str:
        if not report.practical_agents:
            return ""
        metrics_list = self._compute_agent_difficulty_metrics(report)
        if not metrics_list:
            return ""

        difficulties_present: list[str] = []
        for diff in ("easy", "medium", "hard"):
            if any(m.difficulty == diff for m in metrics_list):
                difficulties_present.append(diff)
        for m in metrics_list:
            if m.difficulty not in difficulties_present:
                difficulties_present.append(m.difficulty)

        if not difficulties_present:
            return ""

        agent_names = [a.agent_name for a in report.practical_agents]

        sections = []
        for difficulty in difficulties_present:
            diff_metrics = {m.agent_name: m for m in metrics_list if m.difficulty == difficulty}
            if not diff_metrics:
                continue

            agent_headers = "".join(f"<th>{escape(name)}</th>" for name in agent_names)

            def make_row(label: str, values: list[str]) -> str:
                cells = "".join(f"<td>{escape(v)}</td>" for v in values)
                return f"<tr><td>{escape(label)}</td>{cells}</tr>"

            pass1_vals = [
                f"{diff_metrics[n].pass_at_1:.1f}%" if n in diff_metrics else "—"
                for n in agent_names
            ]
            pass5_vals = [
                (f"{diff_metrics[n].pass_at_5:.1f}%" if diff_metrics[n].pass_at_5 is not None else "—")
                if n in diff_metrics else "—"
                for n in agent_names
            ]
            pass5s_vals = [
                (f"{diff_metrics[n].pass_at_5_strict:.1f}%" if diff_metrics[n].pass_at_5_strict is not None else "—")
                if n in diff_metrics else "—"
                for n in agent_names
            ]
            tok_vals = [
                (f"{int(diff_metrics[n].tokens_per_success):,}" if diff_metrics[n].tokens_per_success is not None else "—")
                if n in diff_metrics else "—"
                for n in agent_names
            ]
            dur_vals = [
                self._format_duration_ms(diff_metrics[n].duration_per_success if n in diff_metrics else None)
                for n in agent_names
            ]

            # Only show Pass@5 rows when at least one agent has actual multi-run data
            show_pass5 = any(v != "—" for v in pass5_vals)
            show_pass5_strict = any(v != "—" for v in pass5s_vals)

            rows = make_row("Pass@1", pass1_vals)
            if show_pass5:
                rows += make_row("Pass@5", pass5_vals)
            if show_pass5_strict:
                rows += make_row("Pass@5 strict", pass5s_vals)
            rows += make_row("Tokens/success", tok_vals)
            rows += make_row("Duration/success", dur_vals)

            sections.append(f"""
      <article class="card" style="margin-bottom: 16px;">
        <h3>{escape(difficulty.capitalize())}</h3>
        <div style="overflow-x: auto;">
        <table>
          <thead><tr><th>Metric</th>{agent_headers}</tr></thead>
          <tbody>{rows}</tbody>
        </table>
        </div>
      </article>""")

        if not sections:
            return ""
        return "\n      <h2 style=\"margin: 20px 0 12px;\">Results by difficulty</h2>" + "".join(sections)

    def _render_category_heatmap(self, report: RuntimeReport) -> str:
        if not report.practical_agents:
            return ""
        cat_metrics = self._compute_agent_category_metrics(report)
        if not cat_metrics:
            return ""

        all_categories = sorted({m.category for m in cat_metrics})
        if len(all_categories) <= 1:
            return ""

        agent_names = [a.agent_name for a in report.practical_agents]
        difficulties_present: list[str] = []
        for diff in ("easy", "medium", "hard"):
            if any(m.difficulty == diff for m in cat_metrics):
                difficulties_present.append(diff)
        for m in cat_metrics:
            if m.difficulty not in difficulties_present:
                difficulties_present.append(m.difficulty)

        lookup: dict[tuple[str, str, str], float] = {
            (m.agent_name, m.difficulty, m.category): m.pass_at_1
            for m in cat_metrics
        }

        cat_headers = "".join(f"<th>{escape(c)}</th>" for c in all_categories)
        rows = []
        for difficulty in difficulties_present:
            for agent_name in agent_names:
                if not any(m.agent_name == agent_name and m.difficulty == difficulty for m in cat_metrics):
                    continue
                cells = ""
                for cat in all_categories:
                    val = lookup.get((agent_name, difficulty, cat))
                    if val is None:
                        cells += "<td>—</td>"
                    else:
                        cells += f"<td>{val:.1f}%</td>"
                row_label = f"{escape(agent_name)} {escape(difficulty.capitalize())}"
                rows.append(f"<tr><th>{row_label}</th>{cells}</tr>")

        if not rows:
            return ""

        return f"""
      <h2 style="margin: 20px 0 12px;">Category heatmap (Pass@1)</h2>
      <article class="card" style="margin-bottom: 16px;">
        <div style="overflow-x: auto;">
        <table>
          <thead><tr><th></th>{cat_headers}</tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
        </div>
      </article>"""

    def _render_practical_comparison_table(self, report: RuntimeReport) -> str:
        if not report.practical_agents:
            return ""
        task_names: list[str] = []
        for agent in report.practical_agents:
            for task in agent.tasks:
                if task.task_name not in task_names:
                    task_names.append(task.task_name)

        agent_headers = "".join(
            f"<th colspan=\"4\">{escape(agent.agent_name)}</th>"
            for agent in report.practical_agents
        )
        sub_headers = "".join(
            "<th>Result</th><th>Duration</th><th>Input tok</th><th>Output tok</th>"
            for _ in report.practical_agents
        )

        rows = []
        for task_name in task_names:
            cells = ""
            for agent in report.practical_agents:
                task = next((t for t in agent.tasks if t.task_name == task_name), None)
                if task is None:
                    cells += "<td>—</td><td>—</td><td>—</td><td>—</td>"
                    continue
                if task.status == "success":
                    chip = '<span class="chip chip-ok">PASS</span>'
                elif task.status == "regression":
                    chip = '<span class="chip chip-warn">REGR</span>'
                else:
                    chip = '<span class="chip chip-fail">FAIL</span>'
                input_tok = "—"
                output_tok = "—"
                if task.token_usage:
                    it = task.token_usage.get("input_tokens")
                    ot = task.token_usage.get("output_tokens")
                    if isinstance(it, (int, float)):
                        input_tok = f"{int(it):,}"
                    if isinstance(ot, (int, float)):
                        output_tok = f"{int(ot):,}"
                cells += f"<td>{chip}</td><td>{escape(task.formatted_duration)}</td><td>{escape(input_tok)}</td><td>{escape(output_tok)}</td>"
            rows.append(f"<tr><td>{escape(task_name)}</td>{cells}</tr>")

        totals_row = "<tr style=\"font-weight: 600; border-top: 2px solid var(--border);\"><td>Total</td>"
        for agent in report.practical_agents:
            passed = sum(1 for t in agent.tasks if t.status == "success")
            total = len(agent.tasks)
            durations = [t.duration_ms for t in agent.tasks if t.duration_ms is not None]
            total_dur = sum(durations) if durations else None
            input_toks = [t.token_usage.get("input_tokens", 0) for t in agent.tasks if t.token_usage and isinstance(t.token_usage.get("input_tokens"), (int, float))]
            output_toks = [t.token_usage.get("output_tokens", 0) for t in agent.tasks if t.token_usage and isinstance(t.token_usage.get("output_tokens"), (int, float))]
            total_input = sum(input_toks) if input_toks else None
            total_output = sum(output_toks) if output_toks else None
            dur_str = "—"
            if total_dur is not None:
                if total_dur < 1000:
                    dur_str = f"{total_dur} ms"
                elif total_dur < 60000:
                    dur_str = f"{total_dur / 1000:.1f}s"
                else:
                    dur_str = f"{int(total_dur // 60000)}m {(total_dur % 60000) / 1000:.0f}s"
            input_str = f"{int(total_input):,}" if total_input is not None else "—"
            output_str = f"{int(total_output):,}" if total_output is not None else "—"
            totals_row += f"<td>{passed}/{total}</td><td>{escape(dur_str)}</td><td>{escape(input_str)}</td><td>{escape(output_str)}</td>"
        totals_row += "</tr>"

        return f"""
      <article class="card">
        <h2>Task comparison</h2>
        <div style="overflow-x: auto;">
        <table>
          <thead>
            <tr><th rowspan="2">Task</th>{agent_headers}</tr>
            <tr>{sub_headers}</tr>
          </thead>
          <tbody>
            {''.join(rows)}
            {totals_row}
          </tbody>
        </table>
        </div>
      </article>
"""

    def _render_practical_summary_row(self, agent_report: PracticalAgentReport) -> str:
        return f"""
<tr>
  <th>{escape(agent_report.agent_name)}</th>
  <td>{agent_report.summary.get('successful_tasks', 0)}</td>
  <td>{agent_report.summary.get('failed_tasks', 0)}</td>
  <td>{agent_report.summary.get('task_count', 0)}</td>
</tr>
"""

    def _render_practical_agent_card(self, agent_report: PracticalAgentReport) -> str:
        tasks = "".join(self._render_practical_task(task) for task in agent_report.tasks)
        return f"""
<article class="card">
  <h3>{escape(agent_report.display_name)}</h3>
  <p>{escape(agent_report.agent_name)} · {agent_report.summary.get('successful_tasks', 0)}/{agent_report.summary.get('task_count', 0)} passed</p>
  <ul class="task-list">{tasks}</ul>
</article>
"""

    def _render_practical_task(self, task: PracticalTaskResult) -> str:
        if task.status == "success":
            status_class = "chip-ok"
        elif task.status == "regression":
            status_class = "chip-warn"
        else:
            status_class = "chip-fail"
        violations = (
            f"<div class=\"failure\">Touchpoint violations: {escape(', '.join(task.touchpoint_violations))}</div>"
            if task.touchpoint_violations
            else ""
        )
        changed = ", ".join(task.changed_files) if task.changed_files else "none"
        error = f"<div class=\"failure\">Error: {escape(task.error_message)}</div>" if task.error_message else ""
        duration_line = f"<div>Duration: {escape(task.formatted_duration)}</div>"
        input_tok = "—"
        output_tok = "—"
        if task.token_usage:
            it = task.token_usage.get("input_tokens")
            ot = task.token_usage.get("output_tokens")
            if isinstance(it, (int, float)):
                input_tok = f"{int(it):,}"
            if isinstance(ot, (int, float)):
                output_tok = f"{int(ot):,}"
        token_line = f"<div>Tokens: {escape(input_tok)} in / {escape(output_tok)} out</div>"
        return f"""
<li>
  <span class="task-label">{escape(task.task_name)}</span>
  <span class="chip {status_class}">{escape(task.status.upper())}</span>
  <div>{escape(task.description)}</div>
  <div>Changed files: {escape(changed)}</div>
  {duration_line}
  {token_line}
  {violations}
  {error}
</li>
"""

    TASK_DESCRIPTIONS: dict[str, dict[str, str]] = {
        "single-file-bug-fix": {
            "title": "Single-file bug fix",
            "difficulty": "Easy",
            "category": "Bug Fix",
            "what": "The add_numbers() function uses subtraction (-) instead of addition (+).",
            "goal": "Fix the operator so the calculator returns correct sums.",
            "files": "calculator.py",
            "why": "Tests the most basic capability: reading code, spotting a single-character bug, and making a minimal fix.",
        },
        "failing-unit-test-repair": {
            "title": "Failing unit test repair",
            "difficulty": "Easy",
            "category": "Bug Fix",
            "what": "The slugify() function replaces spaces with underscores (_) but tests expect hyphens (-).",
            "goal": "Change the replacement character from underscore to hyphen.",
            "files": "text_utils.py",
            "why": "Tests whether the agent can infer the expected behavior from context without seeing the test file.",
        },
        "config-schema-migration": {
            "title": "Config schema migration",
            "difficulty": "Easy",
            "category": "Feature",
            "what": "load_timeout() only reads timeout_ms but the new schema uses timeout_seconds.",
            "goal": "Support both timeout_seconds (new) and timeout_ms (legacy) fields with backward compatibility.",
            "files": "config_loader.py",
            "why": "Tests the agent's ability to add a feature while preserving existing behavior — a common real-world pattern.",
        },
        "multi-file-import-repair": {
            "title": "Multi-file import repair",
            "difficulty": "Medium",
            "category": "Debug",
            "what": "Two files import from helpers.math_ops, but the module was moved to utils.math_ops.",
            "goal": "Update imports in both app.py and report.py to use the new path.",
            "files": "app.py, report.py",
            "why": "Tests multi-file awareness: the agent must find and fix the same broken import in two separate files.",
        },
        "validation-error-handling-patch": {
            "title": "Validation and error handling patch",
            "difficulty": "Easy",
            "category": "Feature",
            "what": "create_user() accepts any email including blank strings without validation.",
            "goal": "Add email trimming and raise ValueError for blank emails.",
            "files": "user_service.py",
            "why": "Tests the agent's ability to add input validation logic based on a natural-language description.",
        },
    }

    def _render_tasks_tab_panel(self, report: RuntimeReport) -> str:
        if not report.practical_agents:
            return ""

        task_cards = []
        for task_id, info in self.TASK_DESCRIPTIONS.items():
            task_cards.append(f"""
      <article class="card" style="margin-bottom: 12px;">
        <h3>{escape(info['title'])}</h3>
        <p style="margin: 4px 0;"><span class="chip chip-ok" style="margin-left: 0;">{escape(info['difficulty'])}</span> <span class="chip chip-warn" style="margin-left: 4px;">{escape(info['category'])}</span></p>
        <table style="margin-top: 8px;">
          <tbody>
            <tr><th style="width: 100px;">Bug</th><td style="font-family: inherit;">{escape(info['what'])}</td></tr>
            <tr><th>Goal</th><td style="font-family: inherit;">{escape(info['goal'])}</td></tr>
            <tr><th>Files</th><td><code>{escape(info['files'])}</code></td></tr>
            <tr><th>Why this test</th><td style="font-family: inherit;">{escape(info['why'])}</td></tr>
          </tbody>
        </table>
      </article>""")

        return f"""
    <div id="tab-tasks" class="tab-panel" role="tabpanel" aria-labelledby="btn-tasks">
      <article class="card" style="margin-bottom: 16px;">
        <p class="metric-description">Each task is a self-contained Python fixture with a deliberate bug or missing feature. Agents receive only a task description and the list of editable files. Tests are hidden and applied only during evaluation.</p>
      </article>
      {''.join(task_cards)}
    </div>
"""
