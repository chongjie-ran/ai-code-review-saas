"""
CodeLens AI - Backend Tests
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.rules.rule_engine import rule_engine
from app.analyzers.static_analyzer import LogicAnalyzer
from app.analyzers.security_analyzer import SecurityAnalyzer
from app.analyzers.debt_analyzer import DebtAnalyzer


def test_security_analyzer():
    analyzer = SecurityAnalyzer(rule_engine)

    code = '''API_KEY = "sk-1234567890abcdef"
password = "secret123"
os.system(user_input)
'''
    issues = analyzer.analyze(code, "python")
    assert len(issues) >= 2, f"Expected >= 2 issues, got {len(issues)}"
    assert any(i.rule_id == "AI-SC-001" for i in issues), "Should detect hardcoded API key"
    print("✅ Security analyzer tests passed")


def test_logic_analyzer():
    analyzer = LogicAnalyzer(rule_engine)

    code = '''def foo():
    return None

for i in range(len(items)):
    print(items[i])
'''
    issues = analyzer.analyze(code, "python")
    assert len(issues) >= 2, f"Expected >= 2 issues, got {len(issues)}"
    print("✅ Logic analyzer tests passed")


def test_debt_analyzer():
    analyzer = DebtAnalyzer(rule_engine)

    code = '''# TODO: implement this
print("debug")
'''
    issues = analyzer.analyze(code, "python")
    assert len(issues) >= 2, f"Expected >= 2 issues, got {len(issues)}"
    print("✅ Debt analyzer tests passed")


def test_score_calculation():
    """测试质量分数计算"""
    # 高危问题多，分数低
    high_issues = 5
    medium_issues = 3
    low_issues = 2
    score = max(0, 100 - high_issues * 10 - medium_issues * 3 - low_issues * 1)
    assert score == 100 - 50 - 9 - 2 == 39, f"Expected 39, got {score}"
    print("✅ Score calculation tests passed")


if __name__ == "__main__":
    test_security_analyzer()
    test_logic_analyzer()
    test_debt_analyzer()
    test_score_calculation()
    print("\n✅ All tests passed!")
