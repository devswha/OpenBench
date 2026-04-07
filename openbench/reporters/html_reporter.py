from __future__ import annotations

from html import escape
from pathlib import Path

from openbench.reporters.models import AgentReport, ReportMetric, RuntimeReport, RUNTIME_METRICS


class StaticHtmlReporter:
    def render(self, report: RuntimeReport) -> str:
        # Overview tab content
        summary_cards = self._render_summary_cards(report)
        environment_rows = "".join(
            f"<tr><th>{escape(str(key))}</th><td>{escape(str(value))}</td></tr>"
            for key, value in sorted(report.environment.items())
        )
        comparison_rows = "".join(self._render_comparison_row(agent_report) for agent_report in report.agents)
        agent_cards = "".join(self._render_agent_card(agent_report) for agent_report in report.agents)

        # Per-metric tab content
        metric_tab_panels = "".join(
            self._render_metric_tab_panel(report, metric) for metric in RUNTIME_METRICS
        )

        # Tab bar buttons
        tab_buttons = self._render_tab_buttons()

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
    *, *::before, *::after {{
      box-sizing: border-box;
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

    /* ── Tab navigation ── */
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
    .tab-nav::-webkit-scrollbar {{
      display: none;
    }}
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
    .tab-btn:hover {{
      background: rgba(97, 218, 251, 0.08);
      color: var(--text);
    }}
    .tab-btn.active {{
      background: rgba(97, 218, 251, 0.14);
      color: var(--accent);
      font-weight: 600;
    }}

    /* ── Tab panels ── */
    .tab-panel {{
      display: none;
    }}
    .tab-panel.active {{
      display: block;
    }}

    /* ── Metric description card ── */
    .metric-description {{
      font-size: 14px;
      line-height: 1.6;
      margin: 0;
    }}

    /* ── Per-agent detail table in metric tab ── */
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
    .metric-detail-card h4 {{
      margin: 0 0 8px;
      font-size: 15px;
    }}
    .metric-detail-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 0;
      border-bottom: 1px solid var(--border);
      font-size: 13px;
    }}
    .metric-detail-row:last-child {{
      border-bottom: none;
    }}
    .metric-detail-key {{
      color: var(--muted);
    }}
    .metric-detail-val {{
      color: var(--text);
      font-weight: 600;
      font-variant-numeric: tabular-nums;
    }}

    @media (max-width: 600px) {{
      .tab-btn {{
        padding: 7px 14px;
        font-size: 13px;
      }}
      main {{
        padding: 20px 12px 48px;
      }}
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
        <table>
          <tbody>
            {environment_rows}
          </tbody>
        </table>
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
        <h2>Agent cards</h2>
        <div class="grid agent-grid">
          {agent_cards}
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
    </div>

    {metric_tab_panels}
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

      window.addEventListener('hashchange', function () {{
        activate(getActiveFromHash());
      }});

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

    def _render_tab_buttons(self) -> str:
        tabs = [("overview", "Overview")] + [
            (metric.key.replace("_", "-"), metric.label) for metric in RUNTIME_METRICS
        ]
        buttons = []
        for tab_id, tab_label in tabs:
            buttons.append(
                f'<button class="tab-btn" id="btn-{escape(tab_id)}" role="tab" '
                f'data-tab="{escape(tab_id)}" aria-selected="false" '
                f'aria-controls="tab-{escape(tab_id)}">{escape(tab_label)}</button>'
            )
        return "\n      ".join(buttons)

    def _render_summary_cards(self, report: RuntimeReport) -> str:
        return f"""<article class="card">
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
      </article>"""

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

    def _render_metric_tab_panel(self, report: RuntimeReport, metric_spec) -> str:
        tab_id = metric_spec.key.replace("_", "-")
        bars = self._render_metric_bars(report, metric_spec.key)
        agent_details = "".join(
            self._render_metric_agent_detail(agent_report, metric_spec.key)
            for agent_report in report.agents
        )
        description_html = ""
        if metric_spec.description:
            description_html = f"""
      <article class="card" style="margin-bottom: 16px;">
        <p class="metric-description">{escape(metric_spec.description)}</p>
      </article>"""

        return f"""
    <div id="tab-{escape(tab_id)}" class="tab-panel" role="tabpanel" aria-labelledby="btn-{escape(tab_id)}">
      {description_html}
      <article class="card">
        <h2>{escape(metric_spec.label)}</h2>
        {bars}
      </article>

      <div class="metric-detail-grid">
        {agent_details}
      </div>
    </div>
"""

    def _render_metric_bars(self, report: RuntimeReport, metric_key: str) -> str:
        bars = []
        for agent_report in report.agents:
            metric = next(m for m in agent_report.metrics if m.key == metric_key)
            width = max(0.0, min(metric.normalized_score or 0.0, 100.0))
            bars.append(
                f"""
<div style="margin-bottom: 12px;">
  <div><strong>{escape(agent_report.agent_name)}</strong> — {escape(metric.formatted_raw_value)} (score {escape(metric.formatted_score)})</div>
  <div class="bar-track"><div class="bar-fill" style="width: {width:.2f}%"></div></div>
</div>
"""
            )
        return "".join(bars)

    def _render_metric_agent_detail(self, agent_report: AgentReport, metric_key: str) -> str:
        metric = next(m for m in agent_report.metrics if m.key == metric_key)
        status_class = "chip-ok" if metric.available and metric.status == "success" else "chip-fail"
        status_text = "OK" if metric.available and metric.status == "success" else metric.status.upper()
        error_row = ""
        if metric.error_message:
            error_row = f"""
        <div class="metric-detail-row">
          <span class="metric-detail-key">Error</span>
          <span class="metric-detail-val failure">{escape(metric.error_message)}</span>
        </div>"""
        return f"""
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
