import { useState } from 'react';

const LANGUAGES = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'java', label: 'Java' },
  { value: 'go', label: 'Go' },
];

const SAMPLE_CODE = `# AI生成的Python代码 - 包含多个问题
import os

API_KEY = "sk-1234567890abcdef"  # 硬编码密钥

def get_user(user_id):
    data = cache.get(user_id, None)
    if data is None:
        return None
    return data

def process_items(items):
    for i in range(len(items)):  # AI典型模式
        print(items[i])
        if items[i] < 0:  # 未检查越界
            return items[-1]

# TODO: 添加错误处理
def execute_query(sql):
    query = "SELECT * FROM users WHERE id = %s" % sql
    os.system(query)
`;

function App() {
  const [code, setCode] = useState(SAMPLE_CODE);
  const [language, setLanguage] = useState('python');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult(data);
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

  const typeLabel = (t) => {
    if (t === 'logic') return '🔴 逻辑错误';
    if (t === 'security') return '🔒 安全漏洞';
    return '📉 技术债务';
  };

  return (
    <div style={{ minHeight: '100vh', padding: '2rem' }}>
      {/* Header */}
      <header style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          <span style={{ color: '#3b82f6' }}>Code</span>
          <span style={{ color: '#8b5cf6' }}>Lens</span>
          <span style={{ color: '#fff' }}> AI</span>
        </h1>
        <p style={{ color: '#94a3b8' }}>让AI代码从风险到可信</p>
      </header>

      {/* Main */}
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Controls */}
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            style={{
              padding: '0.5rem 1rem',
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
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? '分析中...' : '开始分析'}
          </button>
        </div>

        {/* Editor + Results */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          {/* Code Input */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: '#94a3b8', fontSize: '0.875rem' }}>
              代码输入
            </label>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              style={{
                width: '100%',
                height: '500px',
                padding: '1rem',
                borderRadius: '0.5rem',
                border: '1px solid #334155',
                background: '#1e293b',
                color: '#e2e8f0',
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                resize: 'vertical',
              }}
              placeholder="粘贴AI生成的代码..."
            />
          </div>

          {/* Results */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: '#94a3b8', fontSize: '0.875rem' }}>
              审查结果
            </label>
            <div
              style={{
                height: '500px',
                borderRadius: '0.5rem',
                border: '1px solid #334155',
                background: '#1e293b',
                overflow: 'auto',
                padding: '1rem',
              }}
            >
              {error && (
                <div style={{ color: '#ef4444', fontFamily: 'monospace', fontSize: '0.875rem' }}>
                  错误: {error}
                </div>
              )}
              {!result && !error && (
                <div style={{ color: '#64748b', textAlign: 'center', marginTop: '2rem' }}>
                  点击"开始分析"查看结果
                </div>
              )}
              {result && (
                <>
                  {/* Score */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem',
                      marginBottom: '1rem',
                      padding: '1rem',
                      borderRadius: '0.5rem',
                      background: '#0f172a',
                    }}
                  >
                    <div
                      style={{
                        width: '64px',
                        height: '64px',
                        borderRadius: '50%',
                        border: `4px solid ${scoreColor(result.score)}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '1.25rem',
                        fontWeight: 700,
                        color: scoreColor(result.score),
                      }}
                    >
                      {result.score}
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>
                        质量分数
                      </div>
                      <div style={{ color: '#94a3b8', fontSize: '0.875rem' }}>
                        {result.lines_of_code} 行代码
                      </div>
                    </div>
                    <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.75rem' }}>
                      <span style={{ color: '#ef4444', fontSize: '0.875rem' }}>
                        🔴 {result.summary.high}
                      </span>
                      <span style={{ color: '#eab308', fontSize: '0.875rem' }}>
                        🟡 {result.summary.medium}
                      </span>
                      <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>
                        ⚪ {result.summary.low}
                      </span>
                    </div>
                  </div>

                  {/* Issues */}
                  {result.issues.length === 0 ? (
                    <div style={{ color: '#22c55e', textAlign: 'center', marginTop: '2rem' }}>
                      ✅ 未发现问题！代码质量良好
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {result.issues.map((issue, i) => (
                        <div
                          key={i}
                          style={{
                            padding: '0.75rem',
                            borderRadius: '0.5rem',
                            background: '#0f172a',
                            borderLeft: `3px solid ${severityColor(issue.severity)}`,
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                            <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                              {typeLabel(issue.type)}
                            </span>
                            <span style={{ color: '#64748b', fontSize: '0.75rem' }}>
                              L{issue.line} · {issue.rule_id}
                            </span>
                          </div>
                          <div style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                            {issue.message}
                          </div>
                          {issue.fix && (
                            <div
                              style={{
                                fontSize: '0.75rem',
                                color: '#22c55e',
                                fontFamily: 'monospace',
                                padding: '0.25rem 0.5rem',
                                background: '#14532d',
                                borderRadius: '0.25rem',
                                display: 'inline-block',
                              }}
                            >
                              → {issue.fix}
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
