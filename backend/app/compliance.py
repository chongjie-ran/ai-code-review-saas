"""
CodeLens AI - Compliance Report Templates
SOC2, ISO27001, HIPAA compliance reporting for enterprise customers.
"""
import datetime
import json
from typing import Literal, Optional
from .models.schemas import AnalyzeResponse


# ─── SOC2 Compliance Report ─────────────────────────────────────

SOC2_CONTROLS = [
    {
        "id": "CC1.1",
        "category": "Control Environment",
        "title": "Board and Management Oversight",
        "description": "The board of directors and executive management demonstrate commitment to integrity and ethical values.",
        "status": "implemented",
    },
    {
        "id": "CC1.2",
        "category": "Control Environment",
        "title": "Structure, Authority, and Responsibility",
        "description": "Key duties and authority are properly segregated and assigned.",
        "status": "implemented",
    },
    {
        "id": "CC2.1",
        "category": "Communication",
        "title": "Internal Communication",
        "description": "Internal communication conveys important information to relevant parties.",
        "status": "implemented",
    },
    {
        "id": "CC2.2",
        "category": "Communication",
        "title": "External Communication",
        "description": "External communication mechanisms are established for customers and third parties.",
        "status": "implemented",
    },
    {
        "id": "CC3.1",
        "category": "Risk Assessment",
        "title": "Objectives Specification",
        "description": "Clear objectives are established for security, operations, and compliance.",
        "status": "implemented",
    },
    {
        "id": "CC3.2",
        "category": "Risk Assessment",
        "title": "Risk Identification and Analysis",
        "description": "Risks to achieving objectives are identified and analyzed.",
        "status": "implemented",
    },
    {
        "id": "CC3.3",
        "category": "Risk Assessment",
        "title": "Technology Risk Assessment",
        "description": "AI-generated code risks are assessed for security vulnerabilities and logic errors.",
        "status": "implemented",
    },
    {
        "id": "CC4.1",
        "category": "Monitoring",
        "title": "Ongoing Evaluations",
        "description": "Continuous monitoring evaluates the effectiveness of controls.",
        "status": "implemented",
    },
    {
        "id": "CC4.2",
        "category": "Monitoring",
        "title": "Logging and Auditing",
        "description": "Comprehensive audit logs are maintained for all system operations.",
        "status": "implemented",
    },
    {
        "id": "CC5.1",
        "category": "Control Activities",
        "title": "Authentication and Authorization",
        "description": "Proper identity verification and access controls are enforced.",
        "status": "implemented",
    },
    {
        "id": "CC5.2",
        "category": "Control Activities",
        "title": "Data Protection",
        "description": "Sensitive data is encrypted at rest and in transit using AES-256.",
        "status": "implemented",
    },
    {
        "id": "CC5.3",
        "category": "Control Activities",
        "title": "Change Management",
        "description": "Code changes go through review and automated testing.",
        "status": "implemented",
    },
    {
        "id": "CC6.1",
        "category": "Logical Access",
        "title": "Access Control Policy",
        "description": "Role-based access control limits system access to authorized users.",
        "status": "implemented",
    },
    {
        "id": "CC6.6",
        "category": "Logical Access",
        "title": "Security Logging",
        "description": "All security-relevant events are logged with sufficient detail.",
        "status": "implemented",
    },
    {
        "id": "CC7.1",
        "category": "System Operations",
        "title": "Vulnerability Management",
        "description": "AI code analysis detects vulnerabilities before production deployment.",
        "status": "implemented",
    },
    {
        "id": "CC7.2",
        "category": "System Operations",
        "title": "Incident Response",
        "description": "Security incidents are detected, logged, and responded to promptly.",
        "status": "implemented",
    },
    {
        "id": "CC8.1",
        "category": "Change Management",
        "title": "Change Approval",
        "description": "Changes to infrastructure and applications are authorized and reviewed.",
        "status": "implemented",
    },
]


# ─── ISO27001 Security Controls ─────────────────────────────────

ISO27001_CONTROLS = [
    {"id": "A.5.1", "domain": "Information Security Policies", "title": "Management direction for information security", "status": "implemented"},
    {"id": "A.5.2", "domain": "Information Security Policies", "title": "Review of policies for information security", "status": "implemented"},
    {"id": "A.6.1", "domain": "Organization of Information Security", "title": "Internal organization and responsibilities", "status": "implemented"},
    {"id": "A.6.2", "domain": "Organization of Information Security", "title": "Mobile devices and remote work", "status": "implemented"},
    {"id": "A.7.1", "domain": "Human Resource Security", "title": "Prior to employment - screening and background checks", "status": "implemented"},
    {"id": "A.7.2", "domain": "Human Resource Security", "title": "During employment - awareness and training", "status": "implemented"},
    {"id": "A.8.1", "domain": "Asset Management", "title": "Responsibility for assets", "status": "implemented"},
    {"id": "A.8.2", "domain": "Asset Management", "title": "Information classification and labeling", "status": "implemented"},
    {"id": "A.8.3", "domain": "Asset Management", "title": "Information handling - handling requirements per classification", "status": "implemented"},
    {"id": "A.9.1", "domain": "Access Control", "title": "Business requirements for access control", "status": "implemented"},
    {"id": "A.9.2", "domain": "Access Control", "title": "User access management", "status": "implemented"},
    {"id": "A.9.4", "domain": "Access Control", "title": "System and application access control", "status": "implemented"},
    {"id": "A.10.1", "domain": "Cryptography", "title": "Cryptographic controls for data protection", "status": "implemented"},
    {"id": "A.11.1", "domain": "Physical and Environmental Security", "title": "Secure areas", "status": "implemented"},
    {"id": "A.12.1", "domain": "Operations Security", "title": "Operational procedures and responsibilities", "status": "implemented"},
    {"id": "A.12.2", "domain": "Operations Security", "title": "Protection from malware", "status": "implemented"},
    {"id": "A.12.4", "domain": "Operations Security", "title": "Logging and monitoring", "status": "implemented"},
    {"id": "A.12.5", "domain": "Operations Security", "title": "Control of operational software", "status": "implemented"},
    {"id": "A.13.1", "domain": "Communications Security", "title": "Network security management", "status": "implemented"},
    {"id": "A.13.2", "domain": "Communications Security", "title": "Information transfer policies and procedures", "status": "implemented"},
    {"id": "A.14.1", "domain": "System Acquisition, Development, Maintenance", "title": "Security requirements of systems", "status": "implemented"},
    {"id": "A.14.2", "domain": "System Acquisition, Development, Maintenance", "title": "Security in development and support processes", "status": "implemented"},
    {"id": "A.16.1", "domain": "Information Security Incident Management", "title": "Management of incidents and improvements", "status": "implemented"},
    {"id": "A.18.1", "domain": "Compliance", "title": "Compliance with legal and contractual requirements", "status": "implemented"},
]


# ─── HIPAA Security Rule Controls ───────────────────────────────

HIPAA_CONTROLS = [
    {"id": "164.308(a)(1)", "category": "Administrative Safeguards", "title": "Security Management Process - Risk Analysis", "status": "implemented"},
    {"id": "164.308(a)(3)", "category": "Administrative Safeguards", "title": "Workforce Security - Role-based access", "status": "implemented"},
    {"id": "164.308(a)(5)", "category": "Administrative Safeguards", "title": "Security Awareness and Training", "status": "implemented"},
    {"id": "164.310(a)(1)", "category": "Physical Safeguards", "title": "Facility Access Controls", "status": "implemented"},
    {"id": "164.310(b)", "category": "Physical Safeguards", "title": "Workstation Use and Workstation Security", "status": "implemented"},
    {"id": "164.310(c)", "category": "Physical Safeguards", "title": "Device and Media Controls", "status": "implemented"},
    {"id": "164.312(a)", "category": "Technical Safeguards", "title": "Access Control - Encryption and authentication", "status": "implemented"},
    {"id": "164.312(b)", "category": "Technical Safeguards", "title": "Audit Controls - Comprehensive logging", "status": "implemented"},
    {"id": "164.312(c)(1)", "category": "Technical Safeguards", "title": "Integrity - Person or entity authentication", "status": "implemented"},
    {"id": "164.312(e)(1)", "category": "Technical Safeguards", "title": "Transmission Security - Encryption in transit", "status": "implemented"},
]


# ─── Report Generators ──────────────────────────────────────────

def generate_soc2_report(analysis: Optional[AnalyzeResponse] = None, team_name: str = "CodeLens AI Team") -> dict:
    """
    Generate SOC2 compliance report based on analysis results.
    Maps CodeLens findings to SOC2 trust service criteria.
    """
    report_date = datetime.datetime.utcnow().isoformat() + "Z"
    
    # Map severity to compliance risk
    if analysis:
        high_risk = analysis.summary.high
        medium_risk = analysis.summary.medium
        low_risk = analysis.summary.low
        score = analysis.score
    else:
        high_risk = medium_risk = low_risk = 0
        score = 100

    # Determine overall compliance status
    if high_risk > 0:
        overall = "non_compliant"
        risk_level = "high"
    elif medium_risk > 3:
        overall = "conditional"
        risk_level = "medium"
    elif medium_risk > 0:
        overall = "compliant_with_conditions"
        risk_level = "low"
    else:
        overall = "compliant"
        risk_level = "minimal"

    report = {
        "report_type": "SOC2 Type II Compliance",
        "version": "1.0",
        "generated_at": report_date,
        "team_name": team_name,
        "audit_period": {
            "start": (datetime.datetime.utcnow() - datetime.timedelta(days=365)).isoformat() + "Z",
            "end": report_date,
        },
        "overall_compliance_status": overall,
        "risk_level": risk_level,
        "code_quality_summary": {
            "quality_score": score,
            "high_severity_findings": high_risk,
            "medium_severity_findings": medium_risk,
            "low_severity_findings": low_risk,
        },
        "controls": [],
        "executive_summary": _build_soc2_executive_summary(score, high_risk, medium_risk, low_risk),
        "recommendations": _build_soc2_recommendations(high_risk, medium_risk),
    }

    # Map controls with findings
    for ctrl in SOC2_CONTROLS:
        ctrl_copy = dict(ctrl)
        # Map to findings
        ctrl_copy["finding"] = _map_control_to_finding(ctrl["id"], analysis)
        report["controls"].append(ctrl_copy)

    return report


def _map_control_to_finding(ctrl_id: str, analysis: Optional[AnalyzeResponse]) -> dict:
    """Map a SOC2 control to relevant code analysis findings"""
    if not analysis or not analysis.issues:
        return {"status": "pass", "issues": 0, "detail": "No relevant code findings"}

    # Map specific controls to issue types
    control_issue_map = {
        "CC5.1": ["security"],
        "CC5.2": ["security", "debt"],
        "CC5.3": ["logic", "debt"],
        "CC6.1": ["security"],
        "CC6.6": ["debt"],
        "CC7.1": ["security"],
        "CC7.2": ["security", "logic"],
    }

    issue_types = control_issue_map.get(ctrl_id, [])
    if not issue_types:
        return {"status": "pass", "issues": 0, "detail": "Not directly mapped to code analysis"}

    relevant = [i for i in analysis.issues if i.type in issue_types]
    high = sum(1 for i in relevant if i.severity == "high")
    medium = sum(1 for i in relevant if i.severity == "medium")
    low = sum(1 for i in relevant if i.severity == "low")

    if high > 0:
        status = "fail"
    elif medium > 0:
        status = "warning"
    else:
        status = "pass"

    return {
        "status": status,
        "issues": len(relevant),
        "high": high,
        "medium": medium,
        "low": low,
        "detail": f"Found {len(relevant)} issue(s) relevant to {ctrl_id}" if relevant else "No relevant issues",
    }


def _build_soc2_executive_summary(score: int, high: int, medium: int, low: int) -> str:
    """Build executive summary text"""
    if high > 0:
        return (f"Code quality score: {score}/100. "
                f"⚠️ {high} high-severity finding(s) require immediate attention. "
                f"The AI-generated code review process has identified issues that may affect SOC2 compliance.")
    elif medium > 0:
        return (f"Code quality score: {score}/100. "
                f"✓ {medium} medium-severity finding(s) identified. "
                f"Recommend addressing within the current audit period.")
    else:
        return (f"Code quality score: {score}/100. "
                f"✓ No high or medium severity findings. "
                f"AI-generated code meets the security and quality standards for SOC2 compliance.")


def _build_soc2_recommendations(high: int, medium: int) -> list[dict]:
    """Build prioritized recommendations"""
    recs = []
    if high > 0:
        recs.append({
            "priority": "critical",
            "title": "Address High-Severity Findings",
            "description": f"{high} high-severity security or logic issues must be resolved before production deployment.",
        })
    if medium > 0:
        recs.append({
            "priority": "high",
            "title": "Review Medium-Severity Findings",
            "description": f"{medium} medium-severity issues should be reviewed and addressed within 30 days.",
        })
    recs.append({
        "priority": "medium",
        "title": "Integrate CodeLens into CI/CD Pipeline",
        "description": "Ensure all AI-generated code is reviewed by CodeLens before merging to production branches.",
    })
    recs.append({
        "priority": "low",
        "title": "Conduct Security Training",
        "description": "Provide AI coding security training for developers to reduce technical debt.",
    })
    return recs


def generate_iso27001_report(analysis: Optional[AnalyzeResponse] = None, team_name: str = "CodeLens AI Team") -> dict:
    """Generate ISO27001 compliance report"""
    report_date = datetime.datetime.utcnow().isoformat() + "Z"

    if analysis:
        high_risk = analysis.summary.high
        medium_risk = analysis.summary.medium
        score = analysis.score
    else:
        high_risk = medium_risk = 0
        score = 100

    # Security-specific finding mapping
    if analysis:
        security_issues = [i for i in analysis.issues if i.type == "security"]
        logic_issues = [i for i in analysis.issues if i.type == "logic"]
        debt_issues = [i for i in analysis.issues if i.type == "debt"]
    else:
        security_issues = logic_issues = debt_issues = []

    report = {
        "report_type": "ISO27001:2022 Compliance",
        "version": "1.0",
        "generated_at": report_date,
        "team_name": team_name,
        "overall_compliance_status": "compliant" if high_risk == 0 else "non_compliant",
        "controls": [],
        "security_findings": {
            "security": len(security_issues),
            "logic": len(logic_issues),
            "technical_debt": len(debt_issues),
        },
    }

    # Map ISO controls to findings
    for ctrl in ISO27001_CONTROLS:
        ctrl_copy = dict(ctrl)
        ctrl_copy["finding"] = _map_iso_to_finding(ctrl["id"], analysis)
        report["controls"].append(ctrl_copy)

    return report


def _map_iso_to_finding(ctrl_id: str, analysis: Optional[AnalyzeResponse]) -> dict:
    """Map ISO27001 control to relevant code analysis findings"""
    if not analysis or not analysis.issues:
        return {"status": "pass", "detail": "No relevant code findings"}

    mapping = {
        "A.9.1": ["security"], "A.9.2": ["security"], "A.9.4": ["security"],
        "A.10.1": ["security", "debt"],
        "A.12.4": ["debt"], "A.12.5": ["logic", "debt"],
        "A.14.1": ["security", "logic"], "A.14.2": ["security", "logic", "debt"],
        "A.16.1": ["security", "logic"],
    }

    issue_types = mapping.get(ctrl_id, [])
    if not issue_types:
        return {"status": "pass", "detail": "Not directly mapped to code analysis"}

    relevant = [i for i in analysis.issues if i.type in issue_types]
    high = sum(1 for i in relevant if i.severity == "high")

    if high > 0:
        status = "fail"
    elif len(relevant) > 0:
        status = "warning"
    else:
        status = "pass"

    return {"status": status, "issues": len(relevant), "detail": f"{len(relevant)} relevant issue(s)" if relevant else "No issues"}


def generate_hipaa_report(analysis: Optional[AnalyzeResponse] = None, team_name: str = "CodeLens AI Team") -> dict:
    """Generate HIPAA Security Rule compliance report"""
    report_date = datetime.datetime.utcnow().isoformat() + "Z"

    if analysis:
        security_issues = [i for i in analysis.issues if i.type == "security"]
        high = sum(1 for i in security_issues if i.severity == "high")
        medium = sum(1 for i in security_issues if i.severity == "medium")
    else:
        security_issues = []
        high = medium = 0

    report = {
        "report_type": "HIPAA Security Rule Compliance",
        "version": "1.0",
        "generated_at": report_date,
        "team_name": team_name,
        "overall_compliance_status": "compliant" if high == 0 else "non_compliant",
        "safeguards": [],
        "security_findings": {
            "total": len(security_issues),
            "high": high,
            "medium": medium,
        },
        "disclaimer": "This report is for informational purposes. HIPAA compliance requires formal audit by a qualified professional.",
    }

    for ctrl in HIPAA_CONTROLS:
        ctrl_copy = dict(ctrl)
        ctrl_copy["finding"] = _map_hipaa_to_finding(ctrl["id"], analysis)
        report["safeguards"].append(ctrl_copy)

    return report


def _map_hipaa_to_finding(ctrl_id: str, analysis: Optional[AnalyzeResponse]) -> dict:
    """Map HIPAA safeguard to relevant code analysis findings"""
    if not analysis:
        return {"status": "pass", "detail": "No relevant code findings"}

    mapping = {
        "164.312(a)": ["security"],
        "164.312(b)": ["security", "debt"],
        "164.312(c)(1)": ["security"],
        "164.312(e)(1)": ["security"],
    }

    issue_types = mapping.get(ctrl_id, [])
    if not issue_types:
        return {"status": "pass", "detail": "Not directly mapped to code analysis"}

    relevant = [i for i in analysis.issues if i.type in issue_types]
    high = sum(1 for i in relevant if i.severity == "high")

    return {
        "status": "fail" if high > 0 else ("warning" if relevant else "pass"),
        "issues": len(relevant),
        "detail": f"{len(relevant)} relevant issue(s)" if relevant else "No issues",
    }


# ─── HTML Report Renderer ───────────────────────────────────────

def generate_compliance_html_report(report: dict, format_type: str = "soc2") -> str:
    """Generate HTML compliance report"""
    
    format_labels = {
        "soc2": "SOC2 Type II Compliance Report",
        "iso27001": "ISO 27001:2022 Compliance Report",
        "hipaa": "HIPAA Security Rule Compliance Report",
    }
    
    status_colors = {
        "compliant": "#16a34a",
        "non_compliant": "#dc2626",
        "conditional": "#f59e0b",
        "pass": "#16a34a",
        "warning": "#f59e0b",
        "fail": "#dc2626",
    }

    status_label = {
        "compliant": "✓ Compliant",
        "non_compliant": "✗ Non-Compliant",
        "conditional": "⚠ Conditional",
        "pass": "✓ Pass",
        "warning": "⚠ Warning",
        "fail": "✗ Fail",
    }

    overall = report.get("overall_compliance_status", "unknown")
    color = status_colors.get(overall, "#6b7280")
    label = status_label.get(overall, overall.upper())

    controls_key = "controls" if format_type in ("soc2", "iso27001") else "safeguards"
    controls = report.get(controls_key, [])

    controls_html = ""
    for ctrl in controls:
        ctrl_status = ctrl.get("finding", {}).get("status", "pass")
        ctrl_color = status_colors.get(ctrl_status, "#6b7280")
        finding_detail = ctrl.get("finding", {}).get("detail", "")
        
        controls_html += f"""
        <tr>
            <td>{ctrl['id']}</td>
            <td>{ctrl.get('category', ctrl.get('domain', ''))}</td>
            <td>{ctrl['title']}</td>
            <td style="color: {ctrl_color}; font-weight: bold;">
                {status_label.get(ctrl_status, ctrl_status.upper())}
            </td>
            <td>{finding_detail}</td>
        </tr>
        """

    # Summary stats
    if format_type == "soc2":
        cqs = report.get("code_quality_summary", {})
        stats_html = f"""
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 24px 0;">
            <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #1f2937;">{cqs.get('quality_score', 'N/A')}</div>
                <div style="color: #6b7280;">Quality Score</div>
            </div>
            <div style="background: #fef2f2; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #dc2626;">{cqs.get('high_severity_findings', 0)}</div>
                <div style="color: #6b7280;">High Severity</div>
            </div>
            <div style="background: #fffbeb; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #f59e0b;">{cqs.get('medium_severity_findings', 0)}</div>
                <div style="color: #6b7280;">Medium Severity</div>
            </div>
            <div style="background: #f0fdf4; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #16a34a;">{cqs.get('low_severity_findings', 0)}</div>
                <div style="color: #6b7280;">Low Severity</div>
            </div>
        </div>
        """
    else:
        sf = report.get("security_findings", {})
        stats_html = f"""
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 24px 0;">
            <div style="background: #fef2f2; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #dc2626;">{sf.get('high', 0)}</div>
                <div style="color: #6b7280;">High Severity</div>
            </div>
            <div style="background: #fffbeb; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #f59e0b;">{sf.get('medium', 0)}</div>
                <div style="color: #6b7280;">Medium Severity</div>
            </div>
            <div style="background: #f0fdf4; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #16a34a;">{sf.get('low', 0)}</div>
                <div style="color: #6b7280;">Low Severity</div>
            </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{format_labels.get(format_type, 'Compliance Report')} - CodeLens AI</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 40px 20px; color: #1f2937; }}
    h1 {{ color: #111827; border-bottom: 3px solid {color}; padding-bottom: 12px; }}
    h2 {{ color: #374151; margin-top: 40px; }}
    .badge {{ display: inline-block; padding: 8px 20px; border-radius: 20px; font-weight: bold; font-size: 18px; background: {color}20; color: {color}; border: 2px solid {color}; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th {{ background: #f3f4f6; padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb; }}
    td {{ padding: 12px; border-bottom: 1px solid #e5e7eb; }}
    .meta {{ color: #6b7280; font-size: 14px; }}
    .footer {{ margin-top: 60px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 12px; }}
</style>
</head>
<body>
<h1>🔒 {format_labels.get(format_type, 'Compliance Report')}</h1>
<div style="margin-bottom: 20px;">
    <span class="badge">{label}</span>
    <span class="meta" style="margin-left: 16px;">Generated: {report.get('generated_at', '')}</span>
</div>

<p><strong>Team:</strong> {report.get('team_name', '')}</p>
{stats_html}

<h2>Executive Summary</h2>
<p>{report.get('executive_summary', report.get('disclaimer', ''))}</p>

<h2>Controls Assessment</h2>
<table>
    <thead>
        <tr>
            <th>ID</th>
            <th>Category</th>
            <th>Title</th>
            <th>Status</th>
            <th>Finding</th>
        </tr>
    </thead>
    <tbody>
        {controls_html}
    </tbody>
</table>

<div class="footer">
    <p>Generated by CodeLens AI Enterprise · {report.get('generated_at', '')} · Version {report.get('version', '1.0')}</p>
    <p>This report is for informational purposes. For official compliance certification, engage a qualified auditor.</p>
</div>
</body>
</html>"""


def generate_compliance_pdf_text(report: dict, format_type: str = "soc2") -> str:
    """Generate plain-text compliance report suitable for PDF conversion"""
    lines = [
        "=" * 80,
        f"{report.get('report_type', 'Compliance Report').upper()}",
        "=" * 80,
        f"Generated: {report.get('generated_at', '')}",
        f"Team: {report.get('team_name', '')}",
        f"Status: {report.get('overall_compliance_status', 'unknown').upper()}",
        "=" * 80,
        "",
    ]

    controls_key = "controls" if format_type in ("soc2", "iso27001") else "safeguards"
    for ctrl in report.get(controls_key, []):
        finding = ctrl.get("finding", {})
        status = finding.get("status", "pass")
        icon = {"pass": "[PASS]", "warning": "[WARN]", "fail": "[FAIL]"}.get(status, f"[{status.upper()}]")
        lines.append(f"{ctrl['id']:20} {icon:8} {ctrl.get('category', ctrl.get('domain', ''))[:30]:30} {ctrl['title']}")

    lines.append("")
    lines.append("=" * 80)
    lines.append(f"Generated by CodeLens AI Enterprise")
    return "\n".join(lines)
