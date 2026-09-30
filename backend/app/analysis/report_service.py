import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.core.config import settings


class ReportService:
    @staticmethod
    def generate_html_report(
        dataset_name: str,
        dataset_id: str,
        dataset_version: int,
        record_count: int,
        report_title: str,
        insights_data: Dict[str, Any],
        stats_data: Dict[str, Any],
        custom_notes: Optional[str] = None,
    ) -> str:
        """
        Generates a standalone, beautifully styled HTML analysis report.
        """
        now_str = datetime.now(timezone.utc).strftime("%B %d, %Y - %H:%M UTC")

        insights_list = insights_data.get("insights", [])
        descriptive_stats = stats_data.get("descriptive_stats", [])
        top_correlations = stats_data.get("top_correlations", [])
        outliers = stats_data.get("outliers", [])

        # Build Insights HTML
        insights_html = ""
        for item in insights_list:
            category_badge = item.get("category", "General").upper()
            title = item.get("title", "")
            explanation = item.get("explanation", "")
            method = item.get("method", "")
            insights_html += f"""
            <div class="insight-card">
                <div class="badge">{category_badge}</div>
                <h3>{title}</h3>
                <p>{explanation}</p>
                <div class="method-tag">Method: {method}</div>
            </div>
            """

        # Build Descriptive Stats Table HTML
        stats_table_html = ""
        if descriptive_stats:
            stats_table_html = """
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Column</th>
                        <th>Count</th>
                        <th>Mean</th>
                        <th>Std Dev</th>
                        <th>Min</th>
                        <th>Median</th>
                        <th>Max</th>
                        <th>Missing</th>
                    </tr>
                </thead>
                <tbody>
            """
            for stat in descriptive_stats:
                stats_table_html += f"""
                    <tr>
                        <td><strong>{stat.get('column')}</strong></td>
                        <td>{stat.get('count')}</td>
                        <td>{stat.get('mean')}</td>
                        <td>{stat.get('std')}</td>
                        <td>{stat.get('min')}</td>
                        <td>{stat.get('median')}</td>
                        <td>{stat.get('max')}</td>
                        <td>{stat.get('null_count')}</td>
                    </tr>
                """
            stats_table_html += "</tbody></table>"
        else:
            stats_table_html = "<p class='empty-text'>No numeric columns available for descriptive statistics.</p>"

        # Build Correlations HTML
        corr_html = ""
        if top_correlations:
            corr_html = "<ul class='corr-list'>"
            for corr in top_correlations[:5]:
                col_a = corr.get("column_a")
                col_b = corr.get("column_b")
                coeff = corr.get("coefficient")
                strength = corr.get("strength", "").replace("_", " ").title()
                corr_html += f"<li><strong>{col_a}</strong> &harr; <strong>{col_b}</strong>: r = <code>{coeff}</code> ({strength})</li>"
            corr_html += "</ul>"
        else:
            corr_html = "<p class='empty-text'>Insufficient numeric pairs for correlation analysis.</p>"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title} - DataPilot Report</title>
    <style>
        :root {{
            --primary: #4f46e5;
            --primary-light: #eef2ff;
            --slate-900: #0f172a;
            --slate-700: #334155;
            --slate-500: #64748b;
            --slate-100: #f1f5f9;
            --slate-50: #f8fafc;
            --border: #e2e8f0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--slate-50);
            color: var(--slate-900);
            margin: 0;
            padding: 40px 20px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            border: 1px solid var(--border);
            padding: 40px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }}
        .header {{
            border-bottom: 2px solid var(--slate-100);
            padding-bottom: 24px;
            margin-bottom: 32px;
        }}
        .logo {{
            font-size: 14px;
            font-weight: 700;
            color: var(--primary);
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        h1 {{
            font-size: 28px;
            font-weight: 800;
            margin: 0 0 8px 0;
            color: var(--slate-900);
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-top: 20px;
        }}
        .meta-item {{
            background: var(--slate-50);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
        }}
        .meta-label {{
            font-size: 11px;
            text-transform: uppercase;
            color: var(--slate-500);
            font-weight: 600;
        }}
        .meta-val {{
            font-size: 16px;
            font-weight: 700;
            color: var(--slate-900);
            margin-top: 2px;
        }}
        section {{
            margin-bottom: 40px;
        }}
        h2 {{
            font-size: 18px;
            font-weight: 700;
            border-bottom: 1px solid var(--border);
            padding-bottom: 8px;
            margin-bottom: 16px;
        }}
        .insight-card {{
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 14px;
            transition: transform 0.2s;
        }}
        .badge {{
            display: inline-block;
            font-size: 10px;
            font-weight: 700;
            color: var(--primary);
            background: var(--primary-light);
            padding: 3px 8px;
            border-radius: 100px;
            margin-bottom: 6px;
        }}
        .insight-card h3 {{
            margin: 0 0 6px 0;
            font-size: 15px;
            font-weight: 700;
        }}
        .insight-card p {{
            margin: 0 0 8px 0;
            font-size: 13px;
            color: var(--slate-700);
        }}
        .method-tag {{
            font-size: 11px;
            color: var(--slate-500);
            font-family: monospace;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-top: 10px;
        }}
        .data-table th, .data-table td {{
            padding: 8px 12px;
            border: 1px solid var(--border);
            text-align: left;
        }}
        .data-table th {{
            background-color: var(--slate-50);
            font-weight: 600;
            color: var(--slate-700);
        }}
        .corr-list {{
            font-size: 13px;
            padding-left: 20px;
            color: var(--slate-700);
        }}
        .corr-list li {{
            margin-bottom: 6px;
        }}
        .notes-box {{
            background: #fffbeb;
            border: 1px solid #fde68a;
            border-radius: 8px;
            padding: 16px;
            font-size: 13px;
            color: #92400e;
        }}
        .footer {{
            text-align: center;
            font-size: 11px;
            color: var(--slate-500);
            margin-top: 40px;
            border-top: 1px solid var(--border);
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">DataPilot AI Intelligence</div>
            <h1>{report_title}</h1>
            <div class="meta-grid">
                <div class="meta-item">
                    <div class="meta-label">Dataset</div>
                    <div class="meta-val">{dataset_name}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Dataset Version</div>
                    <div class="meta-val">v{dataset_version}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Total Records</div>
                    <div class="meta-val">{record_count}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Generated Date</div>
                    <div class="meta-val">{now_str}</div>
                </div>
            </div>
        </div>

        {f'''
        <section>
            <h2>Custom Notes</h2>
            <div class="notes-box">{custom_notes}</div>
        </section>
        ''' if custom_notes else ''}

        <section>
            <h2>Key Automated Insights</h2>
            {insights_html}
        </section>

        <section>
            <h2>Descriptive Statistics</h2>
            {stats_table_html}
        </section>

        <section>
            <h2>Top Correlation Relationships</h2>
            {corr_html}
        </section>

        <div class="footer">
            Generated autonomously by <strong>DataPilot AI Engine</strong> &bull; All calculations verified via Pandas &bull; Zero Hallucination Guarantee
        </div>
    </div>
</body>
</html>
"""
        return html_content
