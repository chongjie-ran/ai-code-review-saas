"""
CodeLens AI - Security Vulnerability Analyzer
检测AI生成代码的安全漏洞
"""
import re
from ..rules.rule_engine import RuleEngine, Rule
from ..models.schemas import Issue


class SecurityAnalyzer:
    """安全漏洞分析器"""

    def __init__(self, rule_engine: RuleEngine):
        self.rule_engine = rule_engine

    def analyze(self, code: str, language: str) -> list[Issue]:
        """分析代码中的安全漏洞"""
        issues = []
        rules = self.rule_engine.get_rules_by_type("security")
        rules = [r for r in rules if language in r.languages]

        lines = code.split("\n")
        for line_no, line in enumerate(lines, start=1):
            for rule in rules:
                if self._matches_rule(line, rule):
                    issues.append(
                        Issue(
                            type="security",
                            severity=rule.severity,
                            line=line_no,
                            message=rule.message,
                            rule_id=rule.id,
                            fix=rule.fix,
                        )
                    )
                    break

        return issues

    def _matches_rule(self, line: str, rule: Rule) -> bool:
        """检查单行是否匹配规则"""
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            return False
        return bool(re.search(rule.pattern, line, re.IGNORECASE))
