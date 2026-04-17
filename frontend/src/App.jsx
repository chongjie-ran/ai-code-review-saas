import { useState, useRef } from 'react';
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import javascript from 'highlight.js/lib/languages/javascript';
import typescript from 'highlight.js/lib/languages/typescript';
import java from 'highlight.js/lib/languages/java';
import go from 'highlight.js/lib/languages/go';
import 'highlight.js/styles/github-dark.css';

hljs.registerLanguage('python', python);
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('typescript', typescript);
hljs.registerLanguage('java', java);
hljs.registerLanguage('go', go);

const LANGUAGES = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'java', label: 'Java' },
  { value: 'go', label: 'Go' },
];

const LANGUAGE_MAP = {
  python: 'python',
  javascript: 'javascript',
  typescript: 'typescript',
  java: 'java',
  go: 'go',
};

const SAMPLE_CODE = `# AI生成的Python代码 - 包含多个问题
import os

API_KEY = "sk-1234567890abcdef"  # 硬编码密钥

def get_user(user_id):
    data = cache.get(user_id, None)
    if data is None:
        return None
    return data

def process_items(items):
    for i in range(len(items)):
        print(items[i])
        if items[i] < 0:
            return items[-1]

# TODO: 添加错误处理
def execute_query(sql):
    query = "SELECT * FROM users WHERE id = %s" % sql
    os.system(query)
`;

function CopyButton({ text, label = '复制' }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // fallback
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  return (
    <button
      onClick={handleCopy}
      style={{
        padding: '0.2rem 0.6rem',
        borderRadius: '0.375rem',
        border: '1px solid #334155',
        background: copied ? '#14532d' : '#1e293b',
        color: copied ? '#22c55e' : '#94a3b8',
        fontSize: '0.75rem',
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
    >
      {copied ? '✓ 已复制' : label}
    </button>
  );
}

function CodePreview({ code, language }) {
  const ref = useRef(null);

  const highlighted = (() => {
    try {
      const lang = LANGUAGE_MAP[language] || 'plaintext';
      return hljs.highlight(code || '', { language: lang }).value;
    } catch {
      return code || '';
    }
  })();

  const lines = (code || '').split('\n');

  return (
    <div
      style={{
        fontFamily: "'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace",
        fontSize: '0.8rem',
        lineHeight: 1.6,
        overflow: 'auto',
        maxHeight: '500px',
      }}
    >
      <table style={{ borderCollapse: 'collapse', width: '100%' }}>
        <tbody>
          {lines.map((line, i) => (
            <tr key={i}>
              <td
                style={{
                  color: '#4b5563',
                  padding: '0 0.75rem 0 0',
                  textAlign: 'right',
                  userSelect: 'none',
                  minWidth: '2.5rem',
                  borderRight: '1px solid #1e293b',
                }}
              >
                {i + 1}
              </td>
              <td
                style={{
                  padding: '0 1rem',
                  whiteSpace: 'pre',
                }}
              >
                {/* line-specific highlight */}
                {(() => {
                  try {
                    const lang = LANGUAGE_MAP[language] || 'plaintext';
                        return hljs.highlight(line || ' ', { language: lang }).value;
                  } catch {
                    return line;
                  }
                })()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function App() {
  const [code, setCode] = useState(SAMPLE_CODE);
  const [language, setLanguage] = useState('python');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('input'); // 'input' | 'preview'
  const [copiedFixes, setCopiedFixes] = useState({});

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch('/api/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code,
          language,
          options: {
            check_security: true,
            check_logic: true,
            check_debt: true,
          },
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setResult(data);
      setActiveTab('preview');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const scoreColor = (score) => {
    if (score >= 80) return '#22c55e';
    if (score >= 60) return '#eab308';
    return '#ef4444';
  };

  const severityColor = (s) => {
    if (s === 'high') return '#ef4444';
    if (s === 'medium') return '#eab308';
    return '#6b7280';
  };

  const severityBg = (s) => {
    if (s === 'high') return 'rgba(239,68,68,0.1)';
    if (s === 'medium') return 'rgba(234,179,8,0.1)';
    return 'rgba(107,114,128,0.1)';
  };

  const typeLabel = (t) => {
    if (t === 'logic') return '🔴 逻辑错误';
    if (t === 'security') return '🔒 安全漏洞';
    return '📉 技术债务';
  };

  const handleCopyFix = (index, fix) => {
    navigator.clipboard.writeText(fix).then(() => {
      setCopiedFixes((prev) => ({ ...prev, [index]: true }));
      setTimeout(() => {
        setCopiedFixes((prev) => ({ ...prev, [index]: false }));
      }, 1500);
    });
  };

  return (
    <div style={{ minHeight: '100vh', padding: '1.5rem', background: '#0f172a' }}>
      {/* Header */}
      <header style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '0.25rem' }}>
          <span style={{ color: '#3b82f6' }}>Code</span>
          <span style={{ color: '#8b5cf6' }}>Lens</span>
          <span style={{ color: '#e2e8f0' }}> AI</span>
        </h1>
        <p style={{ color: '#64748b', fontSize: '0.875rem' }}>AI代码审查 · 代码质量可视化</p>
      </header>

      <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
        {/* Controls bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            marginBottom: '1rem',
            flexWrap: 'wrap',
          }}
        >
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: '0.5rem',
              border: '1px solid #334155',
              background: '#1e293b',
              color: '#e2e8f0',
              fontSize: '0.875rem',
            }}
          >
            {LANGUAGES.map((l) => (
              <option key={l.value} value={l.value}>{l.label}</option>
            ))}
          </select>

          <button
            onClick={handleAnalyze}
            disabled={loading || !code.trim()}
            style={{
              padding: '0.5rem 1.5rem',
              borderRadius: '0.5rem',
              border: 'none',
              background: loading ? '#334155' : '#3b82f6',
              color: '#fff',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: loading || !code.trim() ? 'not-allowed' : 'pointer',
              opacity: loading || !code.trim() ? 0.6 : 1,
            }}
          >
            {loading ? '⏳ 分析中...' : '🔍 开始分析'}
          </button>

          <button
            onClick={() => setCode('')}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '0.5rem',
              border: '1px solid #334155',
              background: 'transparent',
              color: '#94a3b8',
              fontSize: '0.875rem',
              cursor: 'pointer',
            }}
          >
            清空
          </button>

          <button
            onClick={() => setCode(SAMPLE_CODE)}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '0.5rem',
              border: '1px solid #334155',
              background: 'transparent',
              color: '#94a3b8',
              fontSize: '0.875rem',
              cursor: 'pointer',
            }}
          >
            加载示例
          </button>

          <div style={{ marginLeft: 'auto', color: '#64748b', fontSize: '0.75rem' }}>
            {code.split('\n').length} 行 · {new TextEncoder().encode(code).length} 字节
          </div>
        </div>

        {/* Main split */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '1rem',
            alignItems: 'start',
          }}
        >
          {/* LEFT: Code Input */}
          <div>
            <div
              style={{
                display: 'flex',
                borderBottom: '1px solid #1e293b',
                marginBottom: '0',
              }}
            >
              {['input', 'preview'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  style={{
                    padding: '0.5rem 1rem',
                    border: 'none',
                    borderBottom: activeTab === tab ? '2px solid #3b82f6' : '2px solid transparent',
                    background: 'transparent',
                    color: activeTab === tab ? '#e2e8f0' : '#64748b',
                    fontSize: '0.875rem',
                    cursor: 'pointer',
                  }}
                >
                  {tab === 'input' ? '📝 代码输入' : '🎨 语法高亮'}
                </button>
              ))}
            </div>

            {activeTab === 'input' ? (
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                style={{
                  width: '100%',
                  height: '480px',
                  padding: '1rem',
                  borderRadius: '0 0 0.5rem 0.5rem',
                  border: '1px solid #334155',
                  borderTop: 'none',
                  background: '#1e293b',
                  color: '#e2e8f0',
                  fontFamily: "'Fira Code', 'Cascadia Code', monospace",
                  fontSize: '0.8rem',
                  lineHeight: 1.6,
                  resize: 'vertical',
                  outline: 'none',
                }}
                placeholder="粘贴AI生成的代码..."
                spellCheck={false}
              />
            ) : (
              <div
                style={{
                  height: '480px',
                  overflow: 'auto',
                  borderRadius: '0 0 0.5rem 0.5rem',
                  border: '1px solid #334155',
                  borderTop: 'none',
                  background: '#1e293b',
                  padding: '0.5rem 0',
                }}
              >
                <CodePreview code={code} language={language} />
              </div>
            )}
          </div>

          {/* RIGHT: Results */}
          <div>
            <div
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '0.5rem 0.5rem 0 0',
                background: '#1e293b',
                border: '1px solid #334155',
                borderBottom: 'none',
                color: '#94a3b8',
                fontSize: '0.875rem',
              }}
            >
              📊 审查结果
            </div>

            <div
              style={{
                height: '510px',
                borderRadius: '0 0 0.5rem 0.5rem',
                border: '1px solid #334155',
                background: '#1e293b',
                overflow: 'auto',
                padding: '1rem',
              }}
            >
              {error && (
                <div
                  style={{
                    color: '#ef4444',
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                    padding: '1rem',
                    background: 'rgba(239,68,68,0.1)',
                    borderRadius: '0.5rem',
                  }}
                >
                  ❌ 错误: {error}
                </div>
              )}

              {!result && !error && (
                <div
                  style={{
                    color: '#4b5563',
                    textAlign: 'center',
                    marginTop: '4rem',
                    fontSize: '0.875rem',
                  }}
                >
                  点击「开始分析」查看结果
                </div>
              )}

              {result && (
                <>
                  {/* Score card */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem',
                      marginBottom: '1rem',
                      padding: '1rem',
                      borderRadius: '0.5rem',
                      background: '#0f172a',
                      border: '1px solid #1e293b',
                    }}
                  >
                    <div
                      style={{
                        width: '64px',
                        height: '64px',
                        borderRadius: '50%',
                        border: `4px solid ${scoreColor(result.score)}`,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                      }}
                    >
                      <span style={{ fontSize: '1.25rem', fontWeight: 800, color: scoreColor(result.score) }}>
                        {result.score}
                      </span>
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, marginBottom: '0.25rem', fontSize: '0.9rem' }}>
                        {result.score >= 80 ? '✅ 优秀' : result.score >= 60 ? '⚠️ 需改进' : '❌ 质量差'}
                      </div>
                      <div style={{ color: '#64748b', fontSize: '0.8rem' }}>
                        {result.lines_of_code} 行 · {result.language}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ color: '#ef4444', fontWeight: 700, fontSize: '1.1rem' }}>{result.summary.high}</div>
                        <div style={{ color: '#64748b', fontSize: '0.7rem' }}>高</div>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ color: '#eab308', fontWeight: 700, fontSize: '1.1rem' }}>{result.summary.medium}</div>
                        <div style={{ color: '#64748b', fontSize: '0.7rem' }}>中</div>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ color: '#6b7280', fontWeight: 700, fontSize: '1.1rem' }}>{result.summary.low}</div>
                        <div style={{ color: '#64748b', fontSize: '0.7rem' }}>低</div>
                      </div>
                    </div>
                  </div>

                  {/* Issues */}
                  {result.issues.length === 0 ? (
                    <div
                      style={{
                        color: '#22c55e',
                        textAlign: 'center',
                        marginTop: '2rem',
                        fontSize: '0.9rem',
                      }}
                    >
                      ✅ 未发现问题！代码质量良好
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {result.issues.map((issue, i) => (
                        <div
                          key={i}
                          style={{
                            padding: '0.875rem',
                            borderRadius: '0.5rem',
                            background: severityBg(issue.severity),
                            border: `1px solid ${severityColor(issue.severity)}22`,
                            borderLeft: `3px solid ${severityColor(issue.severity)}`,
                          }}
                        >
                          <div
                            style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'flex-start',
                              marginBottom: '0.375rem',
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <span
                                style={{
                                  fontSize: '0.7rem',
                                  fontWeight: 600,
                                  padding: '0.1rem 0.4rem',
                                  borderRadius: '0.25rem',
                                  background: severityColor(issue.severity),
                                  color: '#fff',
                                  textTransform: 'uppercase',
                                }}
                              >
                                {issue.severity}
                              </span>
                              <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                                {typeLabel(issue.type)}
                              </span>
                            </div>
                            <span style={{ color: '#4b5563', fontSize: '0.75rem', flexShrink: 0 }}>
                              L{issue.line} · {issue.rule_id}
                            </span>
                          </div>

                          <div
                            style={{
                              color: '#cbd5e1',
                              fontSize: '0.85rem',
                              marginBottom: '0.5rem',
                              lineHeight: 1.5,
                            }}
                          >
                            {issue.message}
                          </div>

                          {issue.fix && (
                            <div
                              style={{
                                display: 'flex',
                                alignItems: 'flex-start',
                                gap: '0.5rem',
                              }}
                            >
                              <div
                                style={{
                                  flex: 1,
                                  fontSize: '0.78rem',
                                  color: '#22c55e',
                                  fontFamily: "'Fira Code', monospace",
                                  padding: '0.375rem 0.5rem',
                                  background: 'rgba(34,197,94,0.08)',
                                  borderRadius: '0.375rem',
                                  border: '1px solid rgba(34,197,94,0.2)',
                                  lineHeight: 1.5,
                                }}
                              >
                                → {issue.fix}
                              </div>
                              <button
                                onClick={() => handleCopyFix(i, issue.fix)}
                                style={{
                                  padding: '0.2rem 0.5rem',
                                  borderRadius: '0.375rem',
                                  border: '1px solid #334155',
                                  background: copiedFixes[i] ? '#14532d' : '#1e293b',
                                  color: copiedFixes[i] ? '#22c55e' : '#94a3b8',
                                  fontSize: '0.7rem',
                                  cursor: 'pointer',
                                  flexShrink: 0,
                                  transition: 'all 0.15s',
                                }}
                              >
                                {copiedFixes[i] ? '✓ 已复制' : '📋 复制'}
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
