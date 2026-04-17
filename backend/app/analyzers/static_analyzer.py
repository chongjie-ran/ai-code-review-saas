"""
CodeLens AI - Logic Error Analyzer
检测AI生成代码的逻辑错误
"""
import re
from typing import Optional
from ..rules.rule_engine import RuleEngine, Rule
from ..models.schemas import Issue


class LogicAnalyzer:
    """逻辑错误分析器"""

    def __init__(self, rule_engine: RuleEngine):
        self.rule_engine = rule_engine

    def analyze(self, code: str, language: str) -> list[Issue]:
        """分析代码中的逻辑错误"""
        issues = []
        rules = self.rule_engine.get_rules_by_type("logic")
        rules = [r for r in rules if language in r.languages]

        lines = code.split("\n")
        for line_no, line in enumerate(lines, start=1):
            for rule in rules:
                if self._matches_rule(line, rule):
                    issues.append(
                        Issue(
                            type="logic",
                            severity=rule.severity,
                            line=line_no,
                            message=rule.message,
                            rule_id=rule.id,
                            fix=rule.fix,
                        )
                    )
                    break  # 一行只报一个同类问题

        return issues

    def _matches_rule(self, line: str, rule: Rule) -> bool:
        """检查单行是否匹配规则"""
        # 跳过注释
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            return False
        return bool(re.search(rule.pattern, line, re.IGNORECASE))
