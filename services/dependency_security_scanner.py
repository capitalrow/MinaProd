#!/usr/bin/env python3
"""
🔒 Production Feature: Dependency Security Scanner

Implements automated dependency vulnerability scanning, container security,
and security audit pipeline for production deployment safety.

Key Features:
- Python package vulnerability scanning
- Container image security analysis
- Automated security audit reporting
- CVE database integration
- Security policy enforcement
"""

import logging
import json
import subprocess
import sys
import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SecurityVulnerability:
    """Security vulnerability record."""
    package_name: str
    current_version: str
    vulnerability_id: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    affected_versions: str
    fixed_in: Optional[str] = None
    cvss_score: Optional[float] = None
    published_date: Optional[str] = None
    references: List[str] = None
    
    def __post_init__(self):
        if self.references is None:
            self.references = []

@dataclass
class SecurityScanResult:
    """Complete security scan results."""
    scan_timestamp: datetime
    scan_type: str
    total_packages: int
    vulnerabilities_found: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    vulnerabilities: List[SecurityVulnerability]
    scan_duration: float
    
class DependencySecurityScanner:
    """
    🛡️ Production-grade dependency security scanner.
    
    Scans Python dependencies for known vulnerabilities using multiple
    security databases and provides comprehensive reporting.
    """
    
    def __init__(self):
        self.scan_results = []
        self.security_policies = {
            'block_critical': True,
            'block_high': True,
            'warn_medium': True,
            'max_critical': 0,
            'max_high': 2,
            'max_medium': 10
        }
        
        logger.info("🔒 Dependency Security Scanner initialized")
    
    def scan_python_dependencies(self, requirements_file: str = "pyproject.toml") -> SecurityScanResult:
        """Scan Python dependencies for vulnerabilities."""
        start_time = datetime.now()
        
        try:
            # Get installed packages
            packages = self._get_installed_packages()
            vulnerabilities = []
            
            # Check each package against vulnerability databases
            for package_name, version in packages.items():
                package_vulns = self._check_package_vulnerabilities(package_name, version)
                vulnerabilities.extend(package_vulns)
            
            # Count by severity
            severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
            for vuln in vulnerabilities:
                severity_counts[vuln.severity] = severity_counts.get(vuln.severity, 0) + 1
            
            scan_duration = (datetime.now() - start_time).total_seconds()
            
            result = SecurityScanResult(
                scan_timestamp=start_time,
                scan_type="python_dependencies",
                total_packages=len(packages),
                vulnerabilities_found=len(vulnerabilities),
                critical_count=severity_counts['CRITICAL'],
                high_count=severity_counts['HIGH'],
                medium_count=severity_counts['MEDIUM'],
                low_count=severity_counts['LOW'],
                vulnerabilities=vulnerabilities,
                scan_duration=scan_duration
            )
            
            self.scan_results.append(result)
            self._log_scan_results(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Dependency scan failed: {e}")
            raise
    
    def _get_installed_packages(self) -> Dict[str, str]:
        """Get all installed Python packages and versions."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                check=True
            )
            
            packages = json.loads(result.stdout)
            return {pkg['name'].lower(): pkg['version'] for pkg in packages}
            
        except Exception as e:
            logger.error(f"Failed to get installed packages: {e}")
            return {}
    
    def _check_package_vulnerabilities(self, package_name: str, version: str) -> List[SecurityVulnerability]:
        """Check a specific package for vulnerabilities using PyUp.io Safety API."""
        vulnerabilities = []
        
        try:
            # Use safety command line tool if available
            result = subprocess.run(
                ['safety', 'check', '--json', '--package', f"{package_name}=={version}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout:
                safety_data = json.loads(result.stdout)
                for vuln_data in safety_data:
                    vuln = SecurityVulnerability(
                        package_name=package_name,
                        current_version=version,
                        vulnerability_id=vuln_data.get('id', 'UNKNOWN'),
                        severity=self._map_severity(vuln_data.get('v', '')),
                        description=vuln_data.get('advisory', ''),
                        affected_versions=vuln_data.get('v', ''),
                        fixed_in=self._extract_fixed_version(vuln_data.get('v', '')),
                        references=[vuln_data.get('cve', '')] if vuln_data.get('cve') else []
                    )
                    vulnerabilities.append(vuln)
            
        except subprocess.CalledProcessError:
            # Safety not available, try alternative method
            vulnerabilities.extend(self._check_osv_database(package_name, version))
        except Exception as e:
            logger.warning(f"Could not check {package_name}: {e}")
        
        return vulnerabilities
    
    def _check_osv_database(self, package_name: str, version: str) -> List[SecurityVulnerability]:
        """Check package against OSV (Open Source Vulnerabilities) database."""
        vulnerabilities = []
        
        try:
            # Query OSV API
            osv_url = "https://api.osv.dev/v1/query"
            query_data = {
                "package": {
                    "name": package_name,
                    "ecosystem": "PyPI"
                },
                "version": version
            }
            
            response = requests.post(osv_url, json=query_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                for vuln_data in data.get('vulns', []):
                    vuln = SecurityVulnerability(
                        package_name=package_name,
                        current_version=version,
                        vulnerability_id=vuln_data.get('id', 'UNKNOWN'),
                        severity=self._extract_severity_from_osv(vuln_data),
                        description=vuln_data.get('summary', ''),
                        affected_versions=self._extract_affected_versions(vuln_data),
                        published_date=vuln_data.get('published', ''),
                        references=vuln_data.get('references', [])
                    )
                    vulnerabilities.append(vuln)
        
        except Exception as e:
            logger.warning(f"OSV check failed for {package_name}: {e}")
        
        return vulnerabilities
    
    def _map_severity(self, version_spec: str) -> str:
        """Map version specification to severity level."""
        # This is a simplified mapping - in production, you'd use CVSS scores
        if 'critical' in version_spec.lower():
            return 'CRITICAL'
        elif 'high' in version_spec.lower():
            return 'HIGH'
        elif 'medium' in version_spec.lower():
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _extract_severity_from_osv(self, vuln_data: Dict) -> str:
        """Extract severity from OSV vulnerability data."""
        severity_data = vuln_data.get('severity', [])
        if severity_data:
            score = severity_data[0].get('score')
            if isinstance(score, (int, float)):
                if score >= 9.0:
                    return 'CRITICAL'
                elif score >= 7.0:
                    return 'HIGH'
                elif score >= 4.0:
                    return 'MEDIUM'
                else:
                    return 'LOW'
        return 'MEDIUM'  # Default
    
    def _extract_affected_versions(self, vuln_data: Dict) -> str:
        """Extract affected version ranges from OSV data."""
        affected = vuln_data.get('affected', [])
        if affected:
            ranges = affected[0].get('ranges', [])
            if ranges:
                events = ranges[0].get('events', [])
                version_ranges = []
                for event in events:
                    if 'introduced' in event:
                        version_ranges.append(f">={event['introduced']}")
                    elif 'fixed' in event:
                        version_ranges.append(f"<{event['fixed']}")
                return ','.join(version_ranges)
        return 'unknown'
    
    def _extract_fixed_version(self, version_spec: str) -> Optional[str]:
        """Extract fixed version from version specification."""
        # Simple extraction - in production, parse version specs properly
        if '>=' in version_spec:
            parts = version_spec.split('>=')
            if len(parts) > 1:
                return parts[1].strip()
        return None
    
    def scan_container_security(self, image_name: str = "mina:latest") -> Dict[str, Any]:
        """Scan container image for security vulnerabilities."""
        try:
            # Try to use trivy if available
            result = subprocess.run(
                ['trivy', 'image', '--format', 'json', image_name],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout:
                scan_data = json.loads(result.stdout)
                
                return {
                    'scan_type': 'container_security',
                    'image': image_name,
                    'timestamp': datetime.now().isoformat(),
                    'vulnerabilities': self._process_trivy_results(scan_data),
                    'status': 'completed'
                }
            else:
                logger.warning("Trivy not available, using basic Docker security checks")
                return self._basic_container_checks(image_name)
                
        except Exception as e:
            logger.error(f"Container security scan failed: {e}")
            return {
                'scan_type': 'container_security',
                'image': image_name,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'status': 'failed'
            }
    
    def _process_trivy_results(self, scan_data: Dict) -> List[Dict]:
        """Process Trivy scan results into standardized format."""
        vulnerabilities = []
        
        for result in scan_data.get('Results', []):
            for vuln in result.get('Vulnerabilities', []):
                vulnerabilities.append({
                    'vulnerability_id': vuln.get('VulnerabilityID'),
                    'package_name': vuln.get('PkgName'),
                    'installed_version': vuln.get('InstalledVersion'),
                    'fixed_version': vuln.get('FixedVersion'),
                    'severity': vuln.get('Severity'),
                    'title': vuln.get('Title'),
                    'description': vuln.get('Description'),
                    'references': vuln.get('References', [])
                })
        
        return vulnerabilities
    
    def _basic_container_checks(self, image_name: str) -> Dict[str, Any]:
        """Basic container security checks when advanced tools unavailable."""
        checks = {
            'scan_type': 'basic_container_security',
            'image': image_name,
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        try:
            # Check if running as root
            result = subprocess.run(
                ['docker', 'run', '--rm', image_name, 'whoami'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            checks['checks']['runs_as_root'] = result.stdout.strip() == 'root'
            
            # Check for common security tools
            for tool in ['apt', 'yum', 'wget', 'curl']:
                tool_result = subprocess.run(
                    ['docker', 'run', '--rm', image_name, 'which', tool],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                checks['checks'][f'has_{tool}'] = tool_result.returncode == 0
            
        except Exception as e:
            checks['error'] = str(e)
        
        return checks
    
    def enforce_security_policy(self, scan_result: SecurityScanResult) -> Tuple[bool, List[str]]:
        """Enforce security policy and return pass/fail with reasons."""
        violations = []
        
        # Check critical vulnerabilities
        if self.security_policies['block_critical'] and scan_result.critical_count > 0:
            violations.append(f"CRITICAL: {scan_result.critical_count} critical vulnerabilities found")
        
        # Check high vulnerabilities
        if self.security_policies['block_high'] and scan_result.high_count > self.security_policies['max_high']:
            violations.append(f"HIGH: {scan_result.high_count} high vulnerabilities exceed limit of {self.security_policies['max_high']}")
        
        # Check medium vulnerabilities
        if scan_result.medium_count > self.security_policies['max_medium']:
            violations.append(f"MEDIUM: {scan_result.medium_count} medium vulnerabilities exceed limit of {self.security_policies['max_medium']}")
        
        policy_passed = len(violations) == 0
        
        if not policy_passed:
            logger.error(f"Security policy violations: {violations}")
        else:
            logger.info("All security policies passed")
        
        return policy_passed, violations
    
    def generate_security_report(self, output_file: str = "security_report.json"):
        """Generate comprehensive security report."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'scan_summary': {
                'total_scans': len(self.scan_results),
                'latest_scan': asdict(self.scan_results[-1]) if self.scan_results else None
            },
            'security_policies': self.security_policies,
            'scan_history': [asdict(result) for result in self.scan_results],
            'recommendations': self._generate_recommendations()
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Security report generated: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to generate security report: {e}")
            return None
    
    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on scan results."""
        recommendations = []
        
        if not self.scan_results:
            return ["No scan results available"]
        
        latest_scan = self.scan_results[-1]
        
        if latest_scan.critical_count > 0:
            recommendations.append("URGENT: Update packages with critical vulnerabilities immediately")
        
        if latest_scan.high_count > 0:
            recommendations.append("HIGH PRIORITY: Review and update packages with high severity vulnerabilities")
        
        if latest_scan.medium_count > 10:
            recommendations.append("Schedule maintenance window to address medium severity vulnerabilities")
        
        # Package-specific recommendations
        for vuln in latest_scan.vulnerabilities:
            if vuln.fixed_in:
                recommendations.append(f"Update {vuln.package_name} from {vuln.current_version} to {vuln.fixed_in}")
        
        return recommendations
    
    def _log_scan_results(self, result: SecurityScanResult):
        """Log scan results for monitoring."""
        logger.info(f"Security scan completed: {result.vulnerabilities_found} vulnerabilities found")
        logger.info(f"Severity breakdown - Critical: {result.critical_count}, High: {result.high_count}, Medium: {result.medium_count}, Low: {result.low_count}")
    
    def install_security_tools(self) -> bool:
        """Install required security scanning tools."""
        tools_to_install = []
        
        # Check for safety
        try:
            subprocess.run(['safety', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            tools_to_install.append('safety')
        
        if tools_to_install:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install'] + tools_to_install, check=True)
                logger.info(f"Installed security tools: {tools_to_install}")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install security tools: {e}")
                return False
        
        logger.info("All security tools already installed")
        return True

def run_security_scan() -> SecurityScanResult:
    """Run complete security scan and return results."""
    scanner = DependencySecurityScanner()
    
    # Install tools if needed
    scanner.install_security_tools()
    
    # Run dependency scan
    result = scanner.scan_python_dependencies()
    
    # Check security policy
    policy_passed, violations = scanner.enforce_security_policy(result)
    
    if not policy_passed:
        logger.error("Security scan failed policy checks")
        for violation in violations:
            logger.error(f"Policy violation: {violation}")
    
    # Generate report
    scanner.generate_security_report()
    
    return result

if __name__ == "__main__":
    # CLI interface for running security scans
    run_security_scan()