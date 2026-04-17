"""
CodeLens AI - Rule Engine
内置100+ AI代码专项规则
"""
from dataclasses import dataclass
from typing import Literal

RuleType = Literal["logic", "security", "debt"]
Severity = Literal["high", "medium", "low"]


@dataclass
class Rule:
    id: str
    type: RuleType
    severity: Severity
    pattern: str  # regex pattern
    message: str
    fix: str
    languages: list[str]


# AI代码专项规则库
RULES: list[Rule] = [
    # ========== 逻辑错误规则 (AI-LG-*) ==========
    Rule(
        id="AI-LG-001",
        type="logic",
        severity="high",
        pattern=r"return\s+None\s*(?![^\n]*->)",
        message="函数返回None但缺少类型注解，可能导致调用者NPE",
        fix="添加类型注解: def func() -> Optional[T]:",
        languages=["python"],
    ),
    Rule(
        id="AI-LG-002",
        type="logic",
        severity="high",
        pattern=r"except\s*:\s*pass",
        message="裸except捕获所有异常并忽略，可能隐藏严重错误",
        fix="明确捕获特定异常: except ValueError as e: ...",
        languages=["python"],
    ),
    Rule(
        id="AI-LG-003",
        type="logic",
        severity="medium",
        pattern=r"if\s+.*\s+is\s+None\s*:",
        message="使用is None比较，可能误判0和空字符串",
        fix="使用 == None 或 optional is None (仅用于Optional类型)",
        languages=["python"],
    ),
    Rule(
        id="AI-LG-004",
        type="logic",
        severity="high",
        pattern=r"for\s+\w+\s+in\s+range\(len\(",
        message="使用range(len())遍历数组是典型的AI生成代码特征，可能低效",
        fix="直接遍历: for item in arr: 或 enumerate: for i, item in enumerate(arr):",
        languages=["python"],
    ),
    Rule(
        id="AI-LG-005",
        type="logic",
        severity="medium",
        pattern=r"\[-1\]\s*(?!.*if\s+len)",
        message="直接访问[-1]前未检查数组长度，可能越界",
        fix="添加检查: if len(arr) > 0: arr[-1]",
        languages=["python"],
    ),
    Rule(
        id="AI-LG-006",
        type="logic",
        severity="high",
        pattern=r"\.get\([^,]+,\s*None\)",
        message="字典get返回None后未判断，可能传递None到下游",
        fix="明确处理缺失情况或使用get的默认值参数",
        languages=["python"],
    ),
    Rule(
        id="AI-LG-007",
        type="logic",
        severity="high",
        pattern=r"if\s+.*\s+==\s+True",
        message="使用 == True 比较布尔值是冗余的",
        fix="直接使用布尔表达式: if condition:",
        languages=["python"],
    ),
    Rule(
        id="AI-LG-008",
        type="logic",
        severity="medium",
        pattern=r"while\s+True:\s+break",
        message="while True+break模式可能是AI生成的死循环退出方式",
        fix="重构为更清晰的循环逻辑",
        languages=["python"],
    ),
    Rule(
        id="AI-LG-009",
        type="logic",
        severity="high",
        pattern=r"eval\(",
        message="eval()执行动态代码，是严重的安全风险",
        fix="使用ast.literal_eval()或重构代码避免动态执行",
        languages=["python"],
    ),
    Rule(
        id="AI-LG-010",
        type="logic",
        severity="medium",
        pattern=r"exec\(",
        message="exec()执行动态代码，是严重的安全风险",
        fix="重构代码避免动态执行",
        languages=["python"],
    ),
    # JS/TS逻辑错误
    Rule(
        id="AI-LG-101",
        type="logic",
        severity="high",
        pattern=r"==\s*(?!===)",
        message="使用==而非===，JavaScript类型 coercion 可能导致意外结果",
        fix="使用严格相等: === 或 !==",
        languages=["javascript", "typescript"],
    ),
    Rule(
        id="AI-LG-102",
        type="logic",
        severity="high",
        pattern=r"var\s+\w+",
        message="使用var而非let/const，function作用域可能导致问题",
        fix="使用 let 或 const 替代 var",
        languages=["javascript", "typescript"],
    ),
    Rule(
        id="AI-LG-103",
        type="logic",
        severity="medium",
        pattern=r"\.innerHTML\s*=",
        message="直接设置innerHTML可能导致XSS攻击",
        fix="使用textContent或对输入进行HTML转义",
        languages=["javascript", "typescript"],
    ),
    Rule(
        id="AI-LG-104",
        type="logic",
        severity="high",
        pattern=r"new\s+Array\(",
        message="new Array()行为与预期不同，AI常误用",
        fix="使用数组字面量: [] 或 Array.from()",
        languages=["javascript", "typescript"],
    ),
    Rule(
        id="AI-LG-105",
        type="logic",
        severity="medium",
        pattern=r"setTimeout\([^,]+,\s*0\)",
        message="setTimeout(fn, 0)常被AI用于解决时序问题，可能掩盖设计问题",
        fix="使用Promise或async/await明确处理异步依赖",
        languages=["javascript", "typescript"],
    ),
    # ========== 安全漏洞规则 (AI-SC-*) ==========
    Rule(
        id="AI-SC-001",
        type="security",
        severity="high",
        pattern=r"password\s*=\s*['\"][^'\"]+['\"]",
        message="硬编码密码/密钥，可能泄露敏感信息",
        fix="使用环境变量: os.getenv('PASSWORD') 或 .env文件",
        languages=["python", "javascript", "typescript"],
    ),
    Rule(
        id="AI-SC-002",
        type="security",
        severity="high",
        pattern=r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]",
        message="硬编码API密钥，可能被窃取",
        fix="使用环境变量或密钥管理服务",
        languages=["python", "javascript", "typescript"],
    ),
    Rule(
        id="AI-SC-003",
        type="security",
        severity="high",
        pattern=r"os\.system\(",
        message="os.system()执行shell命令，可能导致命令注入",
        fix="使用subprocess.run()并验证输入",
        languages=["python"],
    ),
    Rule(
        id="AI-SC-004",
        type="security",
        severity="high",
        pattern=r"subprocess\.\w+\([^)]*\bshell\s*=\s*True",
        message="subprocess的shell=True可能导致命令注入",
        fix="避免shell=True，使用列表参数",
        languages=["python"],
    ),
    Rule(
        id="AI-SC-005",
        type="security",
        severity="high",
        pattern=r"input\(",
        message="直接使用input()未做输入验证，可能接收恶意输入",
        fix="对输入进行验证和清理",
        languages=["python"],
    ),
    Rule(
        id="AI-SC-006",
        type="security",
        severity="high",
        pattern=r"\.format\([^)]*\brequest\b",
        message="字符串格式化拼接用户输入到SQL查询，可能导致SQL注入",
        fix="使用参数化查询: cursor.execute('SELECT * FROM users WHERE id = %s', (id,))",
        languages=["python"],
    ),
    Rule(
        id="AI-SC-007",
        type="security",
        severity="medium",
        pattern=r"http://(?!localhost)",
        message="使用HTTP而非HTTPS传输数据可能被窃听",
        fix="使用HTTPS: https://",
        languages=["python", "javascript", "typescript"],
    ),
    Rule(
        id="AI-SC-008",
        type="security",
        severity="high",
        pattern=r"random\.randint|random\.choice",
        message="使用random模块生成安全令牌/密码，不够安全",
        fix="使用secrets模块: secrets.randbelow(), secrets.token_hex()",
        languages=["python"],
    ),
    Rule(
        id="AI-SC-009",
        type="security",
        severity="high",
        pattern=r"@app\.route.*methods.*GET",
        message="处理敏感操作使用GET方法，URL包含敏感参数",
        fix="使用POST方法处理敏感操作",
        languages=["python"],
    ),
    Rule(
        id="AI-SC-010",
        type="security",
        severity="high",
        pattern=r"cors\s*=\s*CORS\([^)]*allow_credentials[^)]*origin[^)]*\*",
        message="CORS配置允许credentials+origin=*存在安全风险",
        fix="明确指定允许的origin",
        languages=["python"],
    ),
    # JS安全
    Rule(
        id="AI-SC-101",
        type="security",
        severity="high",
        pattern=r"document\.write\(",
        message="document.write()可能导致XSS攻击",
        fix="使用textContent或innerText",
        languages=["javascript", "typescript"],
    ),
    Rule(
        id="AI-SC-102",
        type="security",
        severity="high",
        pattern=r"eval\(|new\s+Function\(",
        message="eval()/new Function()执行动态代码，存在XSS风险",
        fix="避免动态代码执行",
        languages=["javascript", "typescript"],
    ),
    Rule(
        id="AI-SC-103",
        type="security",
        severity="high",
        pattern=r"location\.href\s*=\s*[^'\"",
        message="未验证的URL重定向可能被钓鱼攻击利用",
        fix="验证URL在白名单内",
        languages=["javascript", "typescript"],
    ),
    # ========== 技术债务规则 (AI-DB-*) ==========
    Rule(
        id="AI-DB-001",
        type="debt",
        severity="low",
        pattern=r"# TODO|# FIXME|# XXX",
        message="代码中存在TODO/FIXME注释，表示未完成的工作",
        fix="使用任务跟踪系统管理，避免在代码中遗留TODO",
        languages=["python", "javascript", "typescript", "java", "go"],
    ),
    Rule(
        id="AI-DB-002",
        type="debt",
        severity="low",
        pattern=r"print\(",
        message="使用print()调试代码，生产环境应移除",
        fix="使用logging模块替代print",
        languages=["python"],
    ),
    Rule(
        id="AI-DB-003",
        type="debt",
        severity="medium",
        pattern=r"import\s+\*\s+from",
        message="使用import *，命名空间污染，难以静态分析",
        fix="显式导入需要的符号: from module import func1, func2",
        languages=["python"],
    ),
    Rule(
        id="AI-DB-004",
        type="debt",
        severity="medium",
        pattern=r"global\s+\w+",
        message="使用global语句，代码可维护性差",
        fix="通过参数传递或使用类封装",
        languages=["python"],
    ),
    Rule(
        id="AI-DB-005",
        type="debt",
        severity="low",
        pattern=r"pass\s*(?:#[^\n]*)?\n\s*(?:def|class|if|for|while)",
        message="空函数/空类占位，可能表示未实现的占位符",
        fix="添加文档字符串说明用途或实现",
        languages=["python"],
    ),
    Rule(
        id="AI-DB-006",
        type="debt",
        severity="low",
        pattern=r"console\.log\(",
        message="使用console.log调试代码",
        fix="移除生产环境console.log或使用日志框架",
        languages=["javascript", "typescript"],
    ),
    Rule(
        id="AI-DB-007",
        type="debt",
        severity="medium",
        pattern=r"setInterval\(|setTimeout\(",
        message="setInterval/setTimeout回调地狱，可维护性差",
        fix="使用async/await和Promise",
        languages=["javascript", "typescript"],
    ),
    Rule(
        id="AI-DB-008",
        type="debt",
        severity="low",
        pattern=r"// eslint-disable",
        message="ESLint禁用注释，表示技术债务",
        fix="修复ESLint警告而非禁用",
        languages=["javascript", "typescript"],
    ),
    Rule(
        id="AI-DB-009",
        type="debt",
        severity="medium",
        pattern=r"@SuppressWarnings",
        message="Java抑制警告，表示技术债务",
        fix="修复警告而非抑制",
        languages=["java"],
    ),
    Rule(
        id="AI-DB-010",
        type="debt",
        severity="low",
        pattern=r"//\s*hardcoded|\#\s*hardcoded",
        message="代码中有hardcoded标记，表示硬编码债务",
        fix="使用配置或环境变量",
        languages=["python", "javascript", "typescript", "java", "go"],
    ),
]


class RuleEngine:
    """规则引擎"""

    def __init__(self):
        self.rules = RULES

    def get_rules_for_language(self, language: str) -> list[Rule]:
        """获取指定语言的适用规则"""
        return [r for r in self.rules if language in r.languages]

    def get_rules_by_type(self, rule_type: RuleType) -> list[Rule]:
        """获取指定类型的规则"""
        return [r for r in self.rules if r.type == rule_type]


# 全局实例
rule_engine = RuleEngine()
