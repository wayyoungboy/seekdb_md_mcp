import { useState, useEffect, useRef } from 'react'

interface SearchResult {
  content: string
  file_path: string
  file_name: string
  heading: string
  score: number
  collection: string
}

interface Collection {
  collection: string
  path: string
  total_chunks: number
}

const API = import.meta.env.VITE_API_BASE || ''

// --- Code Rain Background ---
function CodeRain() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight

    const chars = '01アイウエオカキクケコsmm{}[]<>/\\|'.split('')
    const fontSize = 12
    const columns = Math.floor(canvas.width / fontSize)
    const drops: number[] = Array(columns).fill(1).map(() => Math.random() * -100)

    function draw() {
      ctx.fillStyle = 'rgba(13, 11, 26, 0.05)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.fillStyle = '#a78bfa22'
      ctx.font = `${fontSize}px JetBrains Mono, monospace`

      for (let i = 0; i < drops.length; i++) {
        const text = chars[Math.floor(Math.random() * chars.length)]
        ctx.fillText(text, i * fontSize, drops[i] * fontSize)
        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
          drops[i] = 0
        }
        drops[i]++
      }
    }

    const interval = setInterval(draw, 50)
    return () => clearInterval(interval)
  }, [])

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />
}

// --- Config Card Component ---
function ConfigCard({ title, content, onCopy }: { title: string; content: string; onCopy: () => void }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = () => {
    onCopy()
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <div className="rounded-lg overflow-hidden border border-[#2d2a4a]">
      <div className="flex items-center gap-1.5 px-3 py-1.5 border-b border-[#2d2a4a]" style={{ background: '#1a1830' }}>
        <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
        <div className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
        <div className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
        <span className="text-gray-500 text-xs ml-2">{title}</span>
      </div>
      <div className="relative bg-[#0d0b1a] p-3">
        <pre className="text-[#e2e0f0] text-xs whitespace-pre-wrap pr-16">{content}</pre>
        <button onClick={handleCopy}
                className="absolute top-3 right-3 px-3 py-1 bg-[#a78bfa]/10 text-[#a78bfa] border border-[#a78bfa]/30 rounded text-xs hover:bg-[#a78bfa]/20 transition-colors">
          {copied ? '✓ Copied!' : '📋 Copy'}
        </button>
      </div>
    </div>
  )
}

// --- Feature Card ---
function FeatureCard({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <div className="rounded-lg border border-[#2d2a4a] p-4 hover:border-[#a78bfa]/40 transition-colors"
         style={{ background: '#13112a' }}>
      <div className="text-[#a78bfa] text-sm mb-2">{icon}</div>
      <h3 className="text-[#e2e0f0] text-sm font-medium mb-1">{title}</h3>
      <p className="text-gray-500 text-xs leading-relaxed">{description}</p>
    </div>
  )
}

// --- FAQ Item ---
function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b border-[#2d2a4a]">
      <button onClick={() => setOpen(!open)}
              className="w-full flex items-center justify-between py-3 text-left">
        <span className="text-[#a78bfa] text-xs mr-2">{open ? '−' : '+'}</span>
        <span className="text-[#e2e0f0] text-sm flex-1">{q}</span>
      </button>
      {open && <p className="text-gray-500 text-xs pb-3 pl-6 leading-relaxed">{a}</p>}
    </div>
  )
}

// --- Main Search Page ---
export default function Search() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [collections, setCollections] = useState<Collection[]>([])
  const [scope, setScope] = useState('')
  const [mode, setMode] = useState('hybrid')
  const [loading, setLoading] = useState(false)
  const [integrationOpen, setIntegrationOpen] = useState(true)
  const [integrationConfig, setIntegrationConfig] = useState<any>(null)
  const [hasSearched, setHasSearched] = useState(false)

  useEffect(() => {
    fetch(`${API}/api/collections`)
      .then(r => r.json())
      .then(setCollections)
      .catch(() => {})
    fetch(`${API}/api/integration`)
      .then(r => r.json())
      .then(setIntegrationConfig)
      .catch(() => {})
  }, [])

  const doSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setHasSearched(true)
    try {
      const params = new URLSearchParams({ query, mode })
      if (scope) params.set('scope', scope)
      const r = await fetch(`${API}/api/search?${params}`)
      const data = await r.json()
      setResults(data)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  const totalChunks = collections.reduce((s, c) => s + (c.total_chunks || 0), 0)

  return (
    <div className="min-h-screen" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      {/* ===== HERO SECTION ===== */}
      <section className="relative overflow-hidden px-6 pt-16 pb-12">
        <CodeRain />
        <div className="relative z-10 max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="text-[#a78bfa]">Local</span> Document{' '}
            <span className="text-[#a78bfa]">Search</span> &{' '}
            <span className="text-[#a78bfa]">MCP</span>
          </h1>
          <p className="text-gray-400 text-sm mb-2">
            {'> Zero Config, Auto-Indexing, Semantic Search, Infinite Evolution.'}
          </p>
          <p className="text-gray-600 text-xs mb-8">
            将本地 Markdown/TXT/RST 文档索引到 seekdb，对外提供 MCP 服务与 Web 管理界面
          </p>

          {/* Stats */}
          <div className="flex justify-center gap-8 mb-8 text-xs text-gray-500">
            <div>
              <span className="text-[#a78bfa] text-lg font-bold">{collections.length}</span>
              <span className="block">collections</span>
            </div>
            <div>
              <span className="text-[#a78bfa] text-lg font-bold">{collections.length}</span>
              <span className="block">watch dirs</span>
            </div>
            <div>
              <span className="text-[#a78bfa] text-lg font-bold">{totalChunks.toLocaleString()}</span>
              <span className="block">chunks indexed</span>
            </div>
            <div>
              <span className="text-[#a78bfa] text-lg font-bold">2</span>
              <span className="block">MCP modes</span>
            </div>
          </div>
        </div>
      </section>

      {/* ===== SKILL INSTALLATION (M0 style) ===== */}
      {integrationConfig && (
        <section className="max-w-4xl mx-auto px-6 mb-12">
          <div className="rounded-lg overflow-hidden border border-[#2d2a4a]" style={{ background: '#13112a' }}>
            <div className="flex items-center gap-1.5 px-4 py-2 border-b border-[#2d2a4a]"
                 style={{ background: '#1a1830' }}>
              <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
              <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
              <div className="w-3 h-3 rounded-full bg-[#28c840]" />
              <span className="text-gray-400 text-xs ml-2">— Copy and Add to your AI Tool</span>
            </div>
            <div className="p-6">
              <p className="text-gray-400 text-xs mb-4">
                Install SMM skill and follow the instructions to configure for your AI coding tool.
              </p>
              <div className="bg-[#0d0b1a] rounded-lg px-4 py-3 flex items-center justify-between mb-4">
                <code className="text-[#e2e0f0] text-sm">{integrationConfig.skill}</code>
                <button
                  onClick={() => navigator.clipboard.writeText(integrationConfig.skill)}
                  className="px-5 py-2 bg-[#a78bfa] text-[#0d0b1a] rounded text-sm font-bold hover:bg-[#c4b5fd] transition-colors shrink-0 ml-4"
                >
                  COPY TO START
                </button>
              </div>
              {/* MCP Configs below */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
                <ConfigCard
                  title="MCP (stdio)"
                  content={JSON.stringify({ mcpServers: { smm: integrationConfig.stdio } }, null, 2)}
                  onCopy={() => navigator.clipboard.writeText(JSON.stringify({ mcpServers: { smm: integrationConfig.stdio } }, null, 2))}
                />
                <ConfigCard
                  title="MCP (SSE)"
                  content={JSON.stringify({ mcpServers: { smm: integrationConfig.sse } }, null, 2)}
                  onCopy={() => navigator.clipboard.writeText(JSON.stringify({ mcpServers: { smm: integrationConfig.sse } }, null, 2))}
                />
              </div>
            </div>
          </div>
        </section>
      )}

      {/* ===== CONFIG INTEGRATION (additional) ===== */}
      {integrationOpen && integrationConfig && (
        <section className="max-w-4xl mx-auto px-6 mb-12">
          <div className="rounded-lg overflow-hidden border border-[#2d2a4a]" style={{ background: '#13112a' }}>
            <div className="flex items-center justify-between px-4 py-2 border-b border-[#2d2a4a]"
                 style={{ background: '#1a1830' }}>
              <span className="text-gray-400 text-xs">— Copy and Add to your AI Tool</span>
              <button onClick={() => setIntegrationOpen(false)} className="text-gray-500 hover:text-gray-300 text-xs">
                ✕
              </button>
            </div>
            <div className="p-4 space-y-3">
              <ConfigCard
                title="Claude Code Skill"
                content={integrationConfig.skill}
                onCopy={() => navigator.clipboard.writeText(integrationConfig.skill)}
              />
              <ConfigCard
                title="MCP (stdio)"
                content={JSON.stringify({ mcpServers: { smm: integrationConfig.stdio } }, null, 2)}
                onCopy={() => navigator.clipboard.writeText(JSON.stringify({ mcpServers: { smm: integrationConfig.stdio } }, null, 2))}
              />
              <ConfigCard
                title="MCP (SSE)"
                content={JSON.stringify({ mcpServers: { smm: integrationConfig.sse } }, null, 2)}
                onCopy={() => navigator.clipboard.writeText(JSON.stringify({ mcpServers: { smm: integrationConfig.sse } }, null, 2))}
              />
            </div>
          </div>
        </section>
      )}

      {/* ===== SEARCH SECTION ===== */}
      <section className="max-w-4xl mx-auto px-6 mb-16">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold mb-2">
            <span className="text-[#a78bfa]">Search</span> Your Documents
          </h2>
          <p className="text-gray-500 text-sm">{'> 语义搜索你的本地文档库_'}</p>
        </div>

        <div className="mb-4">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && doSearch()}
              placeholder="输入搜索内容..."
              className="w-full bg-[#13112a] border border-[#2d2a4a] rounded-lg px-4 py-3 text-[#e2e0f0] placeholder-gray-600 focus:outline-none focus:border-[#a78bfa] transition-colors"
              style={{ fontFamily: "'JetBrains Mono', monospace" }}
            />
            <button
              onClick={doSearch}
              disabled={loading || !query.trim()}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#a78bfa] hover:text-[#c4b5fd] disabled:opacity-30"
            >
              🔍
            </button>
          </div>
          <div className="flex gap-4 mt-3 text-xs text-gray-400">
            <div className="flex gap-2">
              {['hybrid', 'vector', 'fulltext'].map(m => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`px-2 py-0.5 rounded ${mode === m ? 'text-[#a78bfa] bg-[#a78bfa]/10' : 'hover:text-gray-300'}`}
                >
                  {m}
                </button>
              ))}
            </div>
            <div>
              scope:{' '}
              <select
                value={scope}
                onChange={e => setScope(e.target.value)}
                className="bg-transparent text-gray-400 focus:outline-none"
              >
                <option value="">全部</option>
                {collections.map(c => (
                  <option key={c.collection} value={c.collection} className="bg-[#13112a]">{c.collection}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Results */}
        {loading && <div className="text-center text-gray-500 py-4">搜索中...</div>}

        {hasSearched && !loading && results.length > 0 && (
          <div className="rounded-lg overflow-hidden border border-[#2d2a4a]" style={{ background: '#13112a' }}>
            <div className="flex items-center gap-1.5 px-4 py-2 border-b border-[#2d2a4a]"
                 style={{ background: '#1a1830' }}>
              <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
              <span className="text-gray-400 text-xs ml-2">搜索结果 ({results.length})</span>
            </div>
            <div className="divide-y divide-[#2d2a4a]">
              {results.map((r, i) => (
                <div key={i} className="p-4 hover:bg-[#1a1830]/50 transition-colors">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-gray-600 text-xs w-5">{String(i + 1).padStart(2, '0')}</span>
                    <span className="text-[#a78bfa] text-xs">{r.collection}</span>
                    <span className="text-gray-300 text-xs">{r.file_name}</span>
                    {r.heading && <span className="text-green-400/70 text-xs">{r.heading}</span>}
                    <span className="ml-auto text-[#a78bfa]/70 text-xs">{r.score.toFixed(2)}</span>
                  </div>
                  <p className="text-gray-400 text-xs pl-7 leading-relaxed line-clamp-3">{r.content}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {hasSearched && !loading && results.length === 0 && (
          <div className="text-center text-gray-500 py-8">没有找到结果</div>
        )}
      </section>

      {/* ===== FEATURES SECTION ===== */}
      <section className="max-w-4xl mx-auto px-6 mb-16">
        <h2 className="text-xl font-bold mb-6 text-center">
          <span className="text-[#a78bfa]">Capabilities</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FeatureCard
            icon="⚡"
            title="Semantic Search"
            description="基于向量嵌入的语义搜索，理解查询意图而非简单关键词匹配。支持 hybrid/vector/fulltext 三种模式。"
          />
          <FeatureCard
            icon="🔄"
            title="Real-time Sync"
            description="自动监听目录变更，新增/修改/删除文件时自动更新索引。0.5s 防抖避免重复触发。"
          />
          <FeatureCard
            icon="🧩"
            title="MCP Integration"
            description="通过 stdio 和 SSE 两种传输方式提供 MCP 服务，Claude Code、Cursor 等 AI 工具可直接调用。"
          />
          <FeatureCard
            icon="📄"
            title="Smart Chunking"
            description="按语义结构分块：Markdown 按标题、TXT 按段落、RST 按章节。自动处理超长文本。"
          />
          <FeatureCard
            icon="🔀"
            title="Multi-Collection"
            description="每个监听目录独立 collection，搜索时可指定范围或跨库合并排序。自动命名冲突解决。"
          />
          <FeatureCard
            icon="🌐"
            title="Web Dashboard"
            description="全功能 Web 管理界面：搜索、文档管理、配置编辑、实时日志监控。深色主题，等宽字体。"
          />
        </div>
      </section>

      {/* ===== ARCHITECTURE SECTION ===== */}
      <section className="max-w-4xl mx-auto px-6 mb-16">
        <h2 className="text-xl font-bold mb-2 text-center">
          <span className="text-[#a78bfa]">Architecture</span>
        </h2>
        <p className="text-gray-500 text-xs text-center mb-6">CLI + Daemon 架构，组件独立、职责清晰</p>

        <div className="rounded-lg overflow-hidden border border-[#2d2a4a]" style={{ background: '#13112a' }}>
          <div className="flex items-center gap-1.5 px-3 py-1.5 border-b border-[#2d2a4a]" style={{ background: '#1a1830' }}>
            <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
            <span className="text-gray-500 text-xs ml-2">smm architecture</span>
          </div>
          <div className="p-6 space-y-4 text-xs">
            <div className="flex items-center gap-3">
              <span className="px-3 py-1.5 rounded bg-[#a78bfa]/20 text-[#a78bfa] border border-[#a78bfa]/30 shrink-0">CLI</span>
              <span className="text-gray-400">smm init / import / search / mcp / status / stop</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="px-3 py-1.5 rounded bg-[#a78bfa]/20 text-[#a78bfa] border border-[#a78bfa]/30 shrink-0">Daemon</span>
              <span className="text-gray-400">FastAPI Web UI + File Watcher + SSE MCP Endpoint</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="px-3 py-1.5 rounded bg-[#a78bfa]/20 text-[#a78bfa] border border-[#a78bfa]/30 shrink-0">seekdb</span>
              <span className="text-gray-400">Embedded or Server mode — HNSW vector index + fulltext index</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="px-3 py-1.5 rounded bg-[#a78bfa]/20 text-[#a78bfa] border border-[#a78bfa]/30 shrink-0">MCP</span>
              <span className="text-gray-400">search / import / get_document / list_collections / reindex / status</span>
            </div>
          </div>
        </div>
      </section>

      {/* ===== WORKFLOW SECTION ===== */}
      <section className="max-w-4xl mx-auto px-6 mb-16">
        <h2 className="text-xl font-bold mb-2 text-center">
          <span className="text-[#a78bfa]">How It Works</span>
        </h2>
        <p className="text-gray-500 text-xs text-center mb-6">文档索引流程</p>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
          {[
            { step: '01', title: '发现', desc: '扫描目录 .md/.txt/.rst' },
            { step: '02', title: '解析', desc: '识别文件格式与编码' },
            { step: '03', title: '分块', desc: '按语义结构智能分块' },
            { step: '04', title: 'Embedding', desc: '本地/云端模型生成向量' },
            { step: '05', title: '存储', desc: '存入 seekdb + HNSW 索引' },
          ].map(item => (
            <div key={item.step} className="text-center rounded-lg border border-[#2d2a4a] p-4"
                 style={{ background: '#13112a' }}>
              <div className="text-[#a78bfa] font-bold text-lg mb-1">{item.step}</div>
              <div className="text-[#e2e0f0] text-sm mb-1">{item.title}</div>
              <div className="text-gray-500">{item.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ===== FAQ SECTION ===== */}
      <section className="max-w-4xl mx-auto px-6 mb-16">
        <h2 className="text-xl font-bold mb-6 text-center">
          <span className="text-[#a78bfa]">FAQ</span>
        </h2>
        <div className="rounded-lg border border-[#2d2a4a] overflow-hidden" style={{ background: '#13112a' }}>
          {[
            { q: 'SMM 是什么？', a: 'SMM (seekdb Markdown MCP) 是一个命令行工具，将本地 Markdown/TXT/RST 文档索引到 seekdb 数据库，对外提供 MCP 服务供 AI 工具调用，同时提供 Web 管理界面。' },
            { q: '如何快速开始？', a: '运行 smm init 初始化配置，然后 smm import /path/to/docs 导入文档，最后 smm serve --daemon 启动 Web 服务。' },
            { q: '支持哪些 AI 工具集成？', a: '支持所有兼容 MCP 协议的工具，包括 Claude Code、Cursor 等。通过 stdio 或 SSE 两种传输模式接入。' },
            { q: '文件变更会自动同步吗？', a: '会。smm serve 启动后会自动监听 watch_dirs 中的目录，文件新增、修改、删除都会自动更新索引。' },
            { q: '可以切换 Embedding 模型吗？', a: '可以。在 Settings 页面或 config.yaml 中切换 provider（default/openai/jina/ollama 等），切换后需要重新索引。' },
            { q: '多个目录会有命名冲突吗？', a: '不会。同名目录会自动添加父目录名前缀来区分，如 notes 和 work_notes。' },
          ].map((item, i) => (
            <FAQItem key={i} q={item.q} a={item.a} />
          ))}
        </div>
      </section>

      {/* ===== CTA SECTION ===== */}
      <section className="max-w-4xl mx-auto px-6 mb-16 text-center">
        <div className="rounded-lg overflow-hidden border border-[#2d2a4a] p-8" style={{ background: '#13112a' }}>
          <div className="flex items-center gap-1.5 justify-center mb-4">
            <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
            <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
            <div className="w-3 h-3 rounded-full bg-[#28c840]" />
          </div>
          <h2 className="text-xl font-bold mb-2">
            Ready For <span className="text-[#a78bfa]">Deployment</span>?
          </h2>
          <p className="text-gray-500 text-xs mb-4">
            安装 SMM skill 并配置 MCP 服务，让你的 AI 工具拥有本地文档搜索能力
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <div className="bg-[#0d0b1a] rounded px-4 py-2 text-sm flex items-center justify-between max-w-sm">
              <code className="text-[#e2e0f0] text-xs">{integrationConfig?.skill}</code>
              <button onClick={() => integrationConfig && navigator.clipboard.writeText(integrationConfig.skill)}
                      className="text-[#a78bfa] hover:text-[#c4b5fd] text-xs ml-3 shrink-0">
                📋
              </button>
            </div>
            <div className="bg-[#0d0b1a] rounded px-4 py-2 text-sm flex items-center justify-between max-w-sm">
              <code className="text-[#e2e0f0] text-xs">{integrationConfig?.stdio.command} {integrationConfig?.stdio.args?.join(' ')}</code>
              <button onClick={() => integrationConfig && navigator.clipboard.writeText(JSON.stringify({ mcpServers: { smm: integrationConfig.stdio } }, null, 2))}
                      className="text-[#a78bfa] hover:text-[#c4b5fd] text-xs ml-3 shrink-0">
                📋
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer className="border-t border-[#2d2a4a] py-4 text-center text-gray-600 text-xs">
        Powered by seekdb | SMM v0.1.0
      </footer>
    </div>
  )
}
