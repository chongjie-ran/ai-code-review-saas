"""
CodeLens AI - Technical Debt Analyzer
检测AI生成代码的技术债务
"""
import re
from ..rules.rule_engine import RuleEngine, Rule
from ..models.schemas import Issue


class DebtAnalyzer:
    """技术债务分析器"""

    def __init__(self, rule_engine: RuleEngine):
        self.rule_engine = rule_engine

    def analyze(self, code: str, language: str) -> list[Issue]:
        """分析代码中的技术债务"""
        issues = []
        rules = self.rule_engine.get_rules_by_type("debt")
        rules = [r for r in rules if language in r.languages]

        lines = code.split("\n")
        for line_no, line in enumerate(lines, start=1):
            for rule in rules:
                if self._matches_rule(line, rule):
                    issues.append(
                        Issue(
                            type="debt",
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
        # 技术债务规则可以匹配注释
        if stripped.startswith("#") or stripped.startswith("//"):
            if rule.id in ("AI-DB-001",):  # TODO/FIXME注释规则
                return bool(re.search(rule.pattern, line, re.IGNORECASE))
        return bool(re.search(rule.pattern, line, re.IGNORECASE))
