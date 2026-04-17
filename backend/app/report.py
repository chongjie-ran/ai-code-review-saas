"""
CodeLens AI - Report Generator
Generate HTML and PDF analysis reports
"""
import datetime
from .models.schemas import AnalyzeResponse, Issue


def _severity_badge(severity: str) -> str:
    """Return emoji badge for severity level"""
    badges = {
        "high": "🔴 HIGH",
        "medium": "🟡 MEDIUM",
        "low": "🟢 LOW",
    }
    return badges.get(severity, severity.upper())


def _severity_color(severity: str) -> str:
    """Return color for severity level"""
    colors = {
        "high": "#dc2626",
        "medium": "#f59e0b",
        "low": "#16a34a",
    }
    return colors.get(severity, "#6b7280")


def _type_icon(type_: str) -> str:
    """Return icon for issue type"""
    icons = {
        "logic": "🧠",
        "security": "🔒",
        "debt": "📝",
    }
    return icons.get(type_, "❓")


def _score_color(score: int) -> str:
    """Return color class based on score"""
    if score >= 90:
        return "#16a34a"  # green
    elif score >= 70:
        return "#f59e0b"  # amber
    elif score >= 50:
        return "#f97316"  # orange
    else:
        return "#dc2626"  # red


def generate_html_report(response: AnalyzeResponse, session_id: str) -> str:
    """Generate HTML report from analysis response"""
    summary = response.summary
    issues = response.issues
    score_color = _score_color(response.score)

    # Group issues by severity
    issues_by_sev = {
        "high": [i for i in issues if i.severity == "high"],
        "medium": [i for i in issues if i.severity == "medium"],
        "low": [i for i in issues if i.severity == "low"],
    }

    # Build issues HTML
    issues_html = ""
    for severity in ["high", "medium", "low"]:
        group = issues_by_sev[severity]
        if not group:
            continue
        for issue in group:
            badge = _severity_badge(issue.severity)
            icon = _type_icon(issue.type)
            fix_html = (
                f'<div class="fix"><strong>🔧 修复建议:</strong> {issue.fix or "无"}</div>'
                if issue.fix
                else ""
            )
            issues_html += f"""
        <div class="issue-card" style="border-left: 4px solid {_severity_color(issue.severity)}">
            <div class="issue-header">
                <span class="severity-badge" style="background:{_severity_color(issue.severity)}">{badge}</span>
                <span class="issue-type">{icon} {issue.type.upper()}</span>
                <span class="issue-rule">#{issue.rule_id}</span>
            </div>
            <div class="issue-message">{issue.message}</div>
            <div class="issue-location">📍 第 {issue.line} 行</div>
            {fix_html}
        </div>"""

    if not issues_html:
        issues_html = '<div class="no-issues">🎉 未发现任何问题！代码质量优秀！</div>'

    # Quality gate status
    quality_gate_passed = summary.high == 0
    gate_badge = "✅ 通过" if quality_gate_passed else "❌ 未通过"
    gate_color = "#16a34a" if quality_gate_passed else "#dc2626"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CodeLens AI - 分析报告 #{session_id}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
  .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 32px; border-radius: 12px; margin-bottom: 24px; text-align: center; }}
  .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
  .header .subtitle {{ opacity: 0.85; font-size: 14px; }}
  .meta {{ display: flex; justify-content: center; gap: 24px; flex-wrap: wrap; margin-top: 16px; font-size: 13px; opacity: 0.9; }}
  .card {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .card-title {{ font-size: 16px; font-weight: 600; margin-bottom: 16px; color: #475569; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; }}
  .stat-card {{ text-align: center; padding: 16px; border-radius: 8px; background: #f8fafc; }}
  .stat-value {{ font-size: 32px; font-weight: 700; }}
  .stat-label {{ font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }}
  .score-card {{ text-align: center; padding: 24px; }}
  .score-value {{ font-size: 72px; font-weight: 800; color: {score_color}; line-height: 1; }}
  .score-label {{ font-size: 14px; color: #64748b; margin-top: 8px; }}
  .quality-gate {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 20px; font-weight: 600; font-size: 14px; color: white; background: {gate_color}; margin-top: 12px; }}
  .issues-list {{ display: flex; flex-direction: column; gap: 12px; }}
  .issue-card {{ background: #f8fafc; border-radius: 8px; padding: 16px; }}
  .issue-header {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; }}
  .severity-badge {{ padding: 2px 10px; border-radius: 12px; color: white; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; }}
  .issue-type {{ font-size: 12px; color: #64748b; }}
  .issue-rule {{ font-size: 11px; color: #94a3b8; margin-left: auto; }}
  .issue-message {{ font-size: 14px; color: #334155; margin-bottom: 6px; }}
  .issue-location {{ font-size: 12px; color: #64748b; }}
  .fix {{ margin-top: 8px; padding: 10px; background: #eff6ff; border-radius: 6px; font-size: 13px; color: #1d4ed8; }}
  .no-issues {{ text-align: center; padding: 40px; font-size: 18px; color: #16a34a; }}
  .footer {{ text-align: center; padding: 20px; color: #94a3b8; font-size: 12px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🤖 CodeLens AI 代码审查报告</h1>
    <div class="subtitle">AI代码质量分析报告</div>
    <div class="meta">
      <span>📋 Session: <strong>{session_id}</strong></span>
      <span>📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
      <span>🔤 {response.language.upper()}</span>
      <span>📄 {response.lines_of_code} 行代码</span>
    </div>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-value" style="color: #dc2626">{summary.high}</div>
      <div class="stat-label">🔴 高危问题</div>
    </div>
    <div class="stat-card">
      <div class="stat-value" style="color: #f59e0b">{summary.medium}</div>
      <div class="stat-label">🟡 中危问题</div>
    </div>
    <div class="stat-card">
      <div class="stat-value" style="color: #16a34a">{summary.low}</div>
      <div class="stat-label">🟢 低危问题</div>
    </div>
    <div class="stat-card">
      <div class="stat-value" style="color: #64748b">{summary.total}</div>
      <div class="stat-label">📊 总问题数</div>
    </div>
  </div>

  <div class="card">
    <div class="score-card">
      <div class="score-value">{response.score}</div>
      <div class="score-label">代码质量评分</div>
      <div class="quality-gate">{gate_badge} 质量门 (无高危漏洞)</div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">🐛 问题详情 ({summary.total} 项)</div>
    <div class="issues-list">
      {issues_html}
    </div>
  </div>
</div>
<div class="footer">
  由 CodeLens AI 生成 · {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
</body>
</html>"""
    return html


def generate_text_summary(response: AnalyzeResponse, session_id: str) -> str:
    """Generate plain text summary"""
    summary = response.summary
    quality_passed = summary.high == 0
    gate = "✅ PASSED" if quality_passed else "❌ FAILED"

    lines = [
        f"CodeLens AI Report #{session_id}",
        "=" * 40,
        f"Score: {response.score}/100 | Quality Gate: {gate}",
        f"Language: {response.language} | LOC: {response.lines_of_code}",
        "",
        f"Issues: 🔴 {summary.high}  🟡 {summary.medium}  🟢 {summary.low}  (Total: {summary.total})",
        "",
        "Details:",
    ]

    for issue in response.issues:
        badge = _severity_badge(issue.severity)
        lines.append(f"  {badge} #{issue.rule_id} [{issue.type}] L{issue.line}: {issue.message}")

    lines.append("")
    lines.append(f"Generated at {datetime.datetime.now().isoformat()}")
    return "\n".join(lines)
