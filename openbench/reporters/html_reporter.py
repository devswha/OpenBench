from __future__ import annotations

from html import escape
from pathlib import Path

from openbench.reporters.models import (
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
        tab_buttons = self._render_tab_buttons(report)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>OpenBench Benchmark Report — {escape(report.run_id)}</title>
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #0b1020;
      --panel: #131a2d;
      --text: #edf2ff;
      --muted: #9fb0d8;
      --border: #2a3558;
      --accent: #61dafb;
      --ok: #21c55d;
      --warn: #f59e0b;
      --fail: #ef4444;
    }}
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 20px 64px;
    }}
    h1, h2, h3, h4 {{ margin: 0 0 12px; }}
    p, li {{ color: var(--muted); }}
    .grid {{ display: grid; gap: 16px; }}
    .summary-grid {{ grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
    .agent-grid {{ grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{
      text-align: left;
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    .metric-list, .task-list {{ list-style: none; padding: 0; margin: 0; }}
    .metric-list li, .task-list li {{ margin-bottom: 10px; }}
    .metric-label, .task-label {{ color: var(--text); font-weight: 600; }}
    .chip {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      margin-left: 8px;
    }}
    .chip-ok {{ background: rgba(33, 197, 93, 0.18); color: #7bed9f; }}
    .chip-fail {{ background: rgba(239, 68, 68, 0.18); color: #fda4af; }}
    .chip-warn {{ background: rgba(245, 158, 11, 0.18); color: #fde68a; }}
    .bar-track {{
      width: 100%;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 999px;
      overflow: hidden;
      height: 14px;
      margin-top: 6px;
    }}
    .bar-fill {{
      height: 14px;
      border-radius: 999px;
      background: linear-gradient(90deg, #3b82f6, #61dafb);
    }}
    .note {{ font-size: 14px; color: var(--muted); }}
    .failure {{ color: #fecaca; }}
    .tab-nav {{
      display: flex;
      gap: 4px;
      padding: 4px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      margin-bottom: 24px;
      overflow-x: auto;
      scrollbar-width: none;
    }}
    .tab-nav::-webkit-scrollbar {{ display: none; }}
    .tab-btn {{
      flex-shrink: 0;
      padding: 8px 20px;
      border: none;
      border-radius: 8px;
      background: transparent;
      color: var(--muted);
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
      white-space: nowrap;
      font-family: inherit;
    }}
    .tab-btn:hover {{ background: rgba(97, 218, 251, 0.08); color: var(--text); }}
    .tab-btn.active {{ background: rgba(97, 218, 251, 0.14); color: var(--accent); font-weight: 600; }}
    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; }}
    .metric-description {{ font-size: 14px; line-height: 1.6; margin: 0; }}
    .metric-detail-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-top: 16px;
    }}
    .metric-detail-card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px;
    }}
    .metric-detail-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 0;
      border-bottom: 1px solid var(--border);
      font-size: 13px;
    }}
    .metric-detail-row:last-child {{ border-bottom: none; }}
    .metric-detail-key {{ color: var(--muted); }}
    .metric-detail-val {{ color: var(--text); font-weight: 600; font-variant-numeric: tabular-nums; }}
    code {{ color: #c4b5fd; }}
    @media (max-width: 600px) {{
      .tab-btn {{ padding: 7px 14px; font-size: 13px; }}
      main {{ padding: 20px 12px 48px; }}
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
        return f"""
      <section class="card" style="margin-top: 20px;">
        <h2>Practical task summary</h2>
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
<div style="margin-bottom: 12px;">
  <div><strong>{escape(agent_report.agent_name)}</strong> — {escape(metric.formatted_raw_value)} (score {escape(metric.formatted_score)})</div>
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
        return f"""
    <div id="tab-practical" class="tab-panel" role="tabpanel" aria-labelledby="btn-practical">
      <article class="card" style="margin-bottom: 16px;">
        <p class="metric-description">Shows the deterministic practical coding task outcomes for this run, including pass/failure/regression classification, changed files, and allowed touchpoint enforcement.</p>
      </article>
      <div class="grid agent-grid">{cards}</div>
    </div>
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
        return f"""
<li>
  <span class="task-label">{escape(task.task_name)}</span>
  <span class="chip {status_class}">{escape(task.status.upper())}</span>
  <div>{escape(task.description)}</div>
  <div>Classification: {escape(task.classification)}</div>
  <div>Changed files: {escape(changed)}</div>
  <div>Score: {escape(task.formatted_score)}</div>
  {violations}
  {error}
</li>
"""
