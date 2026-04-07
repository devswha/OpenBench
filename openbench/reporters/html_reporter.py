from __future__ import annotations

from html import escape
from pathlib import Path

from openbench.reporters.models import AgentReport, ReportMetric, RuntimeReport, RUNTIME_METRICS


class StaticHtmlReporter:
    def render(self, report: RuntimeReport) -> str:
        metric_sections = "".join(self._render_metric_chart_section(report, metric.key) for metric in RUNTIME_METRICS)
        agent_cards = "".join(self._render_agent_card(agent_report) for agent_report in report.agents)
        comparison_rows = "".join(self._render_comparison_row(agent_report) for agent_report in report.agents)
        environment_rows = "".join(
            f"<tr><th>{escape(str(key))}</th><td>{escape(str(value))}</td></tr>"
            for key, value in sorted(report.environment.items())
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>OpenBench Runtime Report — {escape(report.run_id)}</title>
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
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    main {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 64px;
    }}
    h1, h2, h3 {{
      margin: 0 0 12px;
    }}
    p, li {{
      color: var(--muted);
    }}
    .grid {{
      display: grid;
      gap: 16px;
    }}
    .summary-grid {{
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }}
    .agent-grid {{
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th, td {{
      text-align: left;
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    .metric-list {{
      list-style: none;
      padding: 0;
      margin: 0;
    }}
    .metric-list li {{
      margin-bottom: 10px;
    }}
    .metric-label {{
      color: var(--text);
      font-weight: 600;
    }}
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
    .note {{
      font-size: 14px;
      color: var(--muted);
    }}
    .failure {{
      color: #fecaca;
    }}
  </style>
</head>
<body>
  <main>
    <section class="grid summary-grid">
      <article class="card">
        <h1>OpenBench Runtime Report</h1>
        <p>Run ID: <strong>{escape(report.run_id)}</strong></p>
      </article>
      <article class="card">
        <h2>Suite</h2>
        <p><strong>{escape(report.suite)}</strong></p>
      </article>
      <article class="card">
        <h2>Agents</h2>
        <p><strong>{len(report.agents)}</strong></p>
      </article>
      <article class="card">
        <h2>Timestamp</h2>
        <p><strong>{escape(report.timestamp)}</strong></p>
      </article>
    </section>

    <section class="card" style="margin-top: 20px;">
      <h2>Environment</h2>
      <table>
        <tbody>
          {environment_rows}
        </tbody>
      </table>
    </section>

    <section style="margin-top: 20px;">
      <h2>Agent cards</h2>
      <div class="grid agent-grid">
        {agent_cards}
      </div>
    </section>

    <section class="card" style="margin-top: 20px;">
      <h2>Comparison table</h2>
      <table>
        <thead>
          <tr>
            <th>Agent</th>
            <th>Startup</th>
            <th>Memory</th>
            <th>Binary size</th>
          </tr>
        </thead>
        <tbody>
          {comparison_rows}
        </tbody>
      </table>
    </section>

    <section style="margin-top: 20px;">
      <h2>Metric charts</h2>
      <div class="grid">
        {metric_sections}
      </div>
    </section>

    <section class="card" style="margin-top: 20px;">
      <h2>Notes</h2>
      <p class="note">
        Raw values remain visible alongside normalized scores. Lower values are better for startup, memory,
        and binary-size metrics. Binary-size currently reflects the resolved command path footprint, which may
        be a launcher wrapper rather than the full installation size.
      </p>
    </section>
  </main>
</body>
</html>
"""

    def write(self, report: RuntimeReport, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render(report))
        return output_path

    def _render_agent_card(self, agent_report: AgentReport) -> str:
        metrics = "".join(self._render_metric_list_item(metric) for metric in agent_report.metrics)
        return f"""
<article class="card">
  <h3>{escape(agent_report.display_name)}</h3>
  <p>{escape(agent_report.agent_name)}</p>
  <ul class="metric-list">
    {metrics}
  </ul>
</article>
"""

    def _render_metric_list_item(self, metric: ReportMetric) -> str:
        status_class = "chip-ok" if metric.available and metric.status == "success" else "chip-fail"
        status_text = "OK" if metric.available and metric.status == "success" else metric.status.upper()
        detail_html = ""
        if metric.error_message:
            detail_html = f'<div class="failure">Error: {escape(metric.error_message)}</div>'
        return f"""
<li>
  <span class="metric-label">{escape(metric.label)}</span>
  <span class="chip {status_class}">{escape(status_text)}</span>
  <div>Raw: {escape(metric.formatted_raw_value)}</div>
  <div>Normalized score: {escape(metric.formatted_score)}</div>
  {detail_html}
</li>
"""

    def _render_comparison_row(self, agent_report: AgentReport) -> str:
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

    def _render_metric_chart_section(self, report: RuntimeReport, metric_key: str) -> str:
        label = next(metric.label for metric in RUNTIME_METRICS if metric.key == metric_key)
        bars = []
        for agent_report in report.agents:
            metric = next(metric for metric in agent_report.metrics if metric.key == metric_key)
            width = max(0.0, min(metric.normalized_score or 0.0, 100.0))
            bars.append(
                f"""
<div style="margin-bottom: 12px;">
  <div><strong>{escape(agent_report.agent_name)}</strong> — {escape(metric.formatted_raw_value)} (score {escape(metric.formatted_score)})</div>
  <div class="bar-track"><div class="bar-fill" style="width: {width:.2f}%"></div></div>
</div>
"""
            )
        return f"""
<article class="card">
  <h3>{escape(label)}</h3>
  {''.join(bars)}
</article>
"""

