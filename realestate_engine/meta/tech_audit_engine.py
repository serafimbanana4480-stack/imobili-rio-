"""Read-only technical audit engine for the Meta Layer."""
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, UTC
from importlib import metadata
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class TechAuditFinding:
    component: str
    status: str
    severity: str
    evidence: str
    recommendation: str
    confidence: float
    source: str = "local_static_rules"


@dataclass
class TechAuditReport:
    generated_at: str
    project: str
    overall_status: str
    findings: List[TechAuditFinding] = field(default_factory=list)
    stack_versions: Dict[str, Optional[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["findings"] = [asdict(finding) for finding in self.findings]
        return data


class TechAuditEngine:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.critical_packages = [
            "fastapi",
            "sqlalchemy",
            "pydantic",
            "streamlit",
            "xgboost",
            "shap",
            "redis",
            "nodriver",
            "slowapi",
            "uvicorn",
        ]

    def run_audit(self) -> TechAuditReport:
        versions = self._collect_stack_versions()
        findings = []
        findings.extend(self._audit_stack_versions(versions))
        findings.extend(self._audit_security_posture())
        findings.extend(self._audit_architecture_posture())
        overall_status = self._overall_status(findings)
        return TechAuditReport(
            generated_at=datetime.now(UTC).isoformat(),
            project="Real Estate Opportunity Engine",
            overall_status=overall_status,
            findings=findings,
            stack_versions=versions,
        )

    def save_report(self, report: TechAuditReport, output_dir: str = "data/meta/audits") -> Path:
        target_dir = self.project_root / output_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        path = target_dir / f"tech_audit_{timestamp}.json"
        path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def render_markdown(self, report: TechAuditReport) -> str:
        lines = [
            "# Technical Audit Report",
            "",
            f"Generated at: {report.generated_at}",
            f"Overall status: {report.overall_status}",
            "",
            "## Stack versions",
        ]
        for package, version in sorted(report.stack_versions.items()):
            lines.append(f"- {package}: {version or 'not installed'}")
        lines.extend(["", "## Findings"])
        for finding in report.findings:
            lines.extend([
                f"### {finding.component}",
                f"- Status: {finding.status}",
                f"- Severity: {finding.severity}",
                f"- Evidence: {finding.evidence}",
                f"- Recommendation: {finding.recommendation}",
                f"- Confidence: {finding.confidence:.2f}",
                f"- Source: {finding.source}",
                "",
            ])
        return "\n".join(lines)

    def _collect_stack_versions(self) -> Dict[str, Optional[str]]:
        versions = {}
        for package in self.critical_packages:
            try:
                versions[package] = metadata.version(package)
            except metadata.PackageNotFoundError:
                versions[package] = None
        return versions

    def _audit_stack_versions(self, versions: Dict[str, Optional[str]]) -> List[TechAuditFinding]:
        findings = []
        for package, version in versions.items():
            if version is None:
                findings.append(TechAuditFinding(
                    component=package,
                    status="missing",
                    severity="medium",
                    evidence=f"Package {package} is not installed in the current environment.",
                    recommendation=f"Install or remove {package} from the declared production stack.",
                    confidence=0.9,
                ))
        if versions.get("fastapi"):
            findings.append(TechAuditFinding(
                component="FastAPI",
                status="good_choice",
                severity="info",
                evidence="FastAPI is present and remains suitable for typed async APIs.",
                recommendation="Keep FastAPI as the API layer and focus on auth, pagination and observability.",
                confidence=0.8,
            ))
        if versions.get("streamlit"):
            findings.append(TechAuditFinding(
                component="Streamlit",
                status="acceptable_for_internal_use",
                severity="low",
                evidence="Streamlit is optimized for internal analytical dashboards, not polished SaaS UX.",
                recommendation="Keep for local/internal operation; plan Next.js only if selling as public SaaS.",
                confidence=0.85,
            ))
        return findings

    def _audit_security_posture(self) -> List[TechAuditFinding]:
        findings = []
        env_example = self.project_root / ".env.example"
        compose_file = self.project_root / "docker-compose.yml"
        if env_example.exists() and "JWT_SECRET_KEY" not in env_example.read_text(encoding="utf-8", errors="ignore"):
            findings.append(TechAuditFinding(
                component="API security config",
                status="needs_attention",
                severity="medium",
                evidence=".env.example does not document JWT_SECRET_KEY.",
                recommendation="Document JWT_SECRET_KEY, API_AUTH_REQUIRED and API_CORS_ORIGINS.",
                confidence=0.9,
            ))
        if compose_file.exists() and "realestate_secure_2026" in compose_file.read_text(encoding="utf-8", errors="ignore"):
            findings.append(TechAuditFinding(
                component="Docker Compose secrets",
                status="insecure_default",
                severity="high",
                evidence="docker-compose.yml contains a static PostgreSQL password.",
                recommendation="Move passwords to .env variables and provide safe examples only.",
                confidence=0.95,
            ))
        return findings

    def _audit_architecture_posture(self) -> List[TechAuditFinding]:
        findings = []
        required_dirs = ["scraping", "etl", "database", "api", "valuation", "scoring", "monitoring", "quality"]
        engine_dir = self.project_root / "realestate_engine"
        missing = [name for name in required_dirs if not (engine_dir / name).exists()]
        if missing:
            findings.append(TechAuditFinding(
                component="Modular architecture",
                status="incomplete",
                severity="medium",
                evidence=f"Missing expected modules: {', '.join(missing)}.",
                recommendation="Create missing modules or update the architecture contract.",
                confidence=0.85,
            ))
        else:
            findings.append(TechAuditFinding(
                component="Modular architecture",
                status="healthy",
                severity="info",
                evidence="Core production modules are present.",
                recommendation="Continue incremental hardening instead of a risky rewrite.",
                confidence=0.85,
            ))
        return findings

    def _overall_status(self, findings: List[TechAuditFinding]) -> str:
        if any(finding.severity == "high" for finding in findings):
            return "needs_hardening"
        if any(finding.severity == "medium" for finding in findings):
            return "acceptable_with_actions"
        return "healthy"
