"""
Advanced Reporting System for Security Findings.
Author: Asola Junior
Generates comprehensive reports in PDF, HTML, JSON, CSV formats with executive summaries.
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from collections import defaultdict

from utils import log_info, log_error


@dataclass
class SecurityFinding:
    """Represents a security finding."""
    finding_id: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # Malware, Permission, Config, etc.
    package_name: str
    title: str
    description: str
    remediation: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    device_id: str = ""
    evidence: List[str] = field(default_factory=list)


@dataclass
class ScanReport:
    """Represents a complete scan report."""
    report_id: str
    scan_date: str
    device_id: str
    device_model: str
    android_version: str
    scanner_version: str = "1.0.0"
    findings: List[SecurityFinding] = field(default_factory=list)
    scan_duration_seconds: float = 0.0
    apps_scanned: int = 0
    threats_found: int = 0
    
    def __post_init__(self):
        """Initialize threat count from findings."""
        self.threats_found = len(self.findings)


class ReportGenerator:
    """Generates security reports in multiple formats."""
    
    SEVERITY_COLORS = {
        "CRITICAL": "#dc3545",
        "HIGH": "#fd7e14",
        "MEDIUM": "#ffc107",
        "LOW": "#28a745",
    }
    
    SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory for saving reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_report(
        self,
        scan_report: ScanReport,
        formats: List[str] = None,
    ) -> Dict[str, Path]:
        """
        Generate reports in specified formats.
        
        Args:
            scan_report: Scan report object
            formats: List of formats (json, csv, html, pdf)
            
        Returns:
            Dict[str, Path]: Mapping of format to output file path
        """
        if formats is None:
            formats = ["json", "csv", "html"]
        
        outputs = {}
        
        try:
            if "json" in formats:
                outputs["json"] = self._generate_json(scan_report)
            
            if "csv" in formats:
                outputs["csv"] = self._generate_csv(scan_report)
            
            if "html" in formats:
                outputs["html"] = self._generate_html(scan_report)
            
            if "pdf" in formats:
                outputs["pdf"] = self._generate_pdf(scan_report)
            
            log_info(f"Reports generated: {', '.join(outputs.keys())}")
            return outputs
        
        except Exception as e:
            log_error(f"Report generation failed: {e}")
            raise
    
    def _generate_json(self, scan_report: ScanReport) -> Path:
        """Generate JSON report."""
        output_file = self.output_dir / f"{scan_report.report_id}_report.json"
        
        # Convert findings to dicts
        findings_data = [asdict(f) for f in scan_report.findings]
        
        report_data = {
            **asdict(scan_report),
            "findings": findings_data,
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        log_info(f"JSON report saved: {output_file}")
        return output_file
    
    def _generate_csv(self, scan_report: ScanReport) -> Path:
        """Generate CSV report."""
        output_file = self.output_dir / f"{scan_report.report_id}_findings.csv"
        
        if not scan_report.findings:
            # Create empty file with headers
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "Finding ID", "Severity", "Category", "Package",
                        "Title", "Description", "Remediation", "Timestamp"
                    ]
                )
                writer.writeheader()
            return output_file
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                "Finding ID", "Severity", "Category", "Package",
                "Title", "Description", "Remediation", "Timestamp"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for finding in scan_report.findings:
                writer.writerow({
                    "Finding ID": finding.finding_id,
                    "Severity": finding.severity,
                    "Category": finding.category,
                    "Package": finding.package_name,
                    "Title": finding.title,
                    "Description": finding.description,
                    "Remediation": finding.remediation,
                    "Timestamp": finding.timestamp,
                })
        
        log_info(f"CSV report saved: {output_file}")
        return output_file
    
    def _generate_html(self, scan_report: ScanReport) -> Path:
        """Generate HTML report."""
        output_file = self.output_dir / f"{scan_report.report_id}_report.html"
        
        # Sort findings by severity
        sorted_findings = sorted(
            scan_report.findings,
            key=lambda f: self.SEVERITY_ORDER.get(f.severity, 999)
        )
        
        # Generate severity summary
        severity_counts = defaultdict(int)
        for finding in scan_report.findings:
            severity_counts[finding.severity] += 1
        
        html_content = self._build_html(scan_report, sorted_findings, severity_counts)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        log_info(f"HTML report saved: {output_file}")
        return output_file
    
    def _build_html(
        self,
        scan_report: ScanReport,
        sorted_findings: List[SecurityFinding],
        severity_counts: Dict[str, int],
    ) -> str:
        """Build HTML report content."""
        findings_html = ""
        
        for finding in sorted_findings:
            color = self.SEVERITY_COLORS.get(finding.severity, "#6c757d")
            
            evidence_html = ""
            if finding.evidence:
                evidence_html = (
                    f"<div class='evidence'>"
                    f"<h5>Evidence:</h5><ul>"
                    + "".join(f"<li>{e}</li>" for e in finding.evidence) +
                    f"</ul></div>"
                )
            
            findings_html += f"""
            <div class='finding' style='border-left: 5px solid {color}'>
                <div class='finding-header'>
                    <span class='severity' style='background-color: {color}'>{finding.severity}</span>
                    <span class='category'>{finding.category}</span>
                    <span class='package'>{finding.package_name}</span>
                </div>
                <h4>{finding.title}</h4>
                <p class='description'>{finding.description}</p>
                <div class='remediation'>
                    <h5>Remediation:</h5>
                    <p>{finding.remediation}</p>
                </div>
                {evidence_html}
                <p class='timestamp'>Found: {finding.timestamp}</p>
            </div>
            """
        
        # Build severity summary bars
        severity_html = ""
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = severity_counts.get(severity, 0)
            color = self.SEVERITY_COLORS[severity]
            severity_html += f"""
            <div class='severity-item'>
                <span class='severity-label' style='background-color: {color}'>{severity}</span>
                <span class='severity-count'>{count}</span>
            </div>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset='UTF-8'>
            <meta name='viewport' content='width=device-width, initial-scale=1.0'>
            <title>Android Security Scanner Report</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                    color: #333;
                }}
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .header {{
                    border-bottom: 3px solid #007bff;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    margin: 0 0 10px 0;
                    color: #007bff;
                }}
                .report-meta {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 20px;
                    margin-bottom: 30px;
                    font-size: 14px;
                }}
                .meta-item {{
                    display: flex;
                    justify-content: space-between;
                }}
                .meta-label {{
                    font-weight: bold;
                    color: #666;
                }}
                .severity-summary {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 15px;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: #f9f9f9;
                    border-radius: 5px;
                }}
                .severity-item {{
                    text-align: center;
                    padding: 10px;
                    border-radius: 5px;
                    background: white;
                }}
                .severity-label {{
                    display: inline-block;
                    padding: 5px 10px;
                    color: white;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 12px;
                }}
                .severity-count {{
                    display: block;
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                    margin-top: 5px;
                }}
                .findings {{
                    margin-top: 30px;
                }}
                .findings h2 {{
                    color: #333;
                    margin-top: 0;
                }}
                .finding {{
                    margin-bottom: 20px;
                    padding: 15px;
                    background: #fafafa;
                    border-radius: 5px;
                    page-break-inside: avoid;
                }}
                .finding-header {{
                    display: flex;
                    gap: 10px;
                    margin-bottom: 10px;
                    flex-wrap: wrap;
                }}
                .finding-header span {{
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                .severity {{
                    color: white;
                }}
                .category {{
                    background: #e0e0e0;
                    color: #333;
                }}
                .package {{
                    background: #e3f2fd;
                    color: #1976d2;
                }}
                .finding h4 {{
                    margin: 10px 0 5px 0;
                    color: #d32f2f;
                }}
                .finding .description {{
                    color: #666;
                    font-size: 14px;
                    margin: 10px 0;
                }}
                .remediation {{
                    background: #e8f5e9;
                    padding: 10px;
                    border-radius: 3px;
                    margin: 10px 0;
                }}
                .remediation h5 {{
                    margin: 0 0 5px 0;
                    color: #2e7d32;
                }}
                .remediation p {{
                    margin: 0;
                    font-size: 13px;
                }}
                .evidence {{
                    background: #fff3e0;
                    padding: 10px;
                    border-radius: 3px;
                    margin: 10px 0;
                }}
                .evidence h5 {{
                    margin: 0 0 5px 0;
                    color: #e65100;
                }}
                .evidence ul {{
                    margin: 0;
                    padding-left: 20px;
                    font-size: 12px;
                }}
                .timestamp {{
                    font-size: 12px;
                    color: #999;
                    margin: 10px 0 0 0;
                }}
                .footer {{
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #999;
                    text-align: center;
                }}
                @media print {{
                    body {{
                        background: white;
                    }}
                    .container {{
                        box-shadow: none;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class='container'>
                <div class='header'>
                    <h1>🔒 Android Security Scanner Report</h1>
                    <p>Professional Security Audit Report</p>
                </div>
                
                <div class='report-meta'>
                    <div class='meta-item'>
                        <span class='meta-label'>Report ID:</span>
                        <span>{scan_report.report_id}</span>
                    </div>
                    <div class='meta-item'>
                        <span class='meta-label'>Scan Date:</span>
                        <span>{scan_report.scan_date}</span>
                    </div>
                    <div class='meta-item'>
                        <span class='meta-label'>Device:</span>
                        <span>{scan_report.device_model}</span>
                    </div>
                    <div class='meta-item'>
                        <span class='meta-label'>Android Version:</span>
                        <span>{scan_report.android_version}</span>
                    </div>
                    <div class='meta-item'>
                        <span class='meta-label'>Apps Scanned:</span>
                        <span>{scan_report.apps_scanned}</span>
                    </div>
                    <div class='meta-item'>
                        <span class='meta-label'>Scan Duration:</span>
                        <span>{scan_report.scan_duration_seconds:.1f}s</span>
                    </div>
                </div>
                
                <div class='severity-summary'>
                    {severity_html}
                </div>
                
                <div class='findings'>
                    <h2>📋 Security Findings ({scan_report.threats_found})</h2>
                    {findings_html if findings_html else '<p style="color: #666;">No threats detected. Device appears secure.</p>'}
                </div>
                
                <div class='footer'>
                    <p>Generated by Android Security Scanner v{scan_report.scanner_version} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>For questions or remediation assistance, contact your security team.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_pdf(self, scan_report: ScanReport) -> Path:
        """Generate PDF report (requires additional library)."""
        try:
            from weasyprint import HTML
            
            output_file = self.output_dir / f"{scan_report.report_id}_report.pdf"
            
            # First generate HTML
            html_file = self.output_dir / f"{scan_report.report_id}_temp.html"
            sorted_findings = sorted(
                scan_report.findings,
                key=lambda f: self.SEVERITY_ORDER.get(f.severity, 999)
            )
            severity_counts = defaultdict(int)
            for finding in scan_report.findings:
                severity_counts[finding.severity] += 1
            
            html_content = self._build_html(scan_report, sorted_findings, severity_counts)
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Convert to PDF
            HTML(str(html_file)).write_pdf(str(output_file))
            
            # Clean up temp HTML file
            html_file.unlink()
            
            log_info(f"PDF report saved: {output_file}")
            return output_file
        
        except ImportError:
            log_error("WeasyPrint not installed. Install with: pip install weasyprint")
            raise
        except Exception as e:
            log_error(f"PDF generation failed: {e}")
            raise
    
    def generate_trend_report(self, scan_reports: List[ScanReport]) -> Dict[str, Any]:
        """
        Generate trend analysis across multiple scans.
        
        Args:
            scan_reports: List of scan reports
            
        Returns:
            Dict with trend analysis data
        """
        if not scan_reports:
            return {}
        
        # Sort by scan date
        reports = sorted(scan_reports, key=lambda r: r.scan_date)
        
        trend_data = {
            "total_scans": len(reports),
            "date_range": {
                "start": reports[0].scan_date,
                "end": reports[-1].scan_date,
            },
            "threat_trend": [],
            "severity_distribution": defaultdict(int),
            "category_distribution": defaultdict(int),
            "devices_scanned": set(),
        }
        
        for report in reports:
            trend_data["threat_trend"].append({
                "date": report.scan_date,
                "threats": report.threats_found,
                "device": report.device_id,
            })
            
            for finding in report.findings:
                trend_data["severity_distribution"][finding.severity] += 1
                trend_data["category_distribution"][finding.category] += 1
            
            trend_data["devices_scanned"].add(report.device_id)
        
        trend_data["devices_scanned"] = list(trend_data["devices_scanned"])
        trend_data["unique_devices"] = len(trend_data["devices_scanned"])
        
        return trend_data


def main():
    """Test report generation."""
    generator = ReportGenerator()
    
    # Create sample report
    sample_report = ScanReport(
        report_id="sample_001",
        scan_date=datetime.now().isoformat(),
        device_id="emulator-5554",
        device_model="Android Emulator",
        android_version="13.0",
        apps_scanned=150,
        scan_duration_seconds=45.3,
    )
    
    # Add sample findings
    sample_report.findings = [
        SecurityFinding(
            finding_id="CRIT_001",
            severity="CRITICAL",
            category="Malware",
            package_name="com.malware.trojan",
            title="Trojan Horse Detected",
            description="Banking trojan attempting credential theft",
            remediation="Uninstall the app immediately and reset passwords",
            evidence=["Suspicious permission requests", "Network tracking detected"],
        ),
        SecurityFinding(
            finding_id="HIGH_001",
            severity="HIGH",
            category="Permission",
            package_name="com.example.app",
            title="Excessive Permissions",
            description="App requests unnecessary sensitive permissions",
            remediation="Review and revoke permissions via Settings > Apps",
        ),
    ]
    
    # Generate reports
    outputs = generator.generate_report(sample_report)
    print(f"\nGenerated reports:")
    for fmt, path in outputs.items():
        print(f"  • {fmt}: {path}")


if __name__ == "__main__":
    main()
