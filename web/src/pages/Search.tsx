import { useState, useEffect } from 'react'

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

export default function Search() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [collections, setCollections] = useState<Collection[]>([])
  const [scope, setScope] = useState('')
  const [mode, setMode] = useState('hybrid')
  const [loading, setLoading] = useState(false)
  const [integrationOpen, setIntegrationOpen] = useState(true)
  const [integrationConfig, setIntegrationConfig] = useState<any>(null)

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

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      {/* Integration Guide */}
      {integrationOpen && integrationConfig && (
        <div className="mb-8 rounded-lg overflow-hidden border border-[#2d2a4a]" style={{ background: '#13112a' }}>
          <div className="flex items-center justify-between px-4 py-2 border-b border-[#2d2a4a]"
               style={{ background: '#1a1830' }}>
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
              <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
              <div className="w-3 h-3 rounded-full bg-[#28c840]" />
            </div>
            <span className="text-gray-400 text-xs">— Copy and Add to your AI Tool</span>
            <button onClick={() => setIntegrationOpen(false)} className="text-gray-500 hover:text-gray-300 text-xs">
              ✕
            </button>
          </div>
          <div className="p-4 space-y-3">
            {/* Claude Code skill */}
            <div className="flex items-center justify-between bg-[#0d0b1a] rounded px-3 py-2 text-sm">
              <code className="text-[#e2e0f0]">{integrationConfig.skill}</code>
              <button onClick={() => copyToClipboard(integrationConfig.skill)}
                      className="text-[#a78bfa] hover:text-[#c4b5fd] text-xs shrink-0 ml-2">
                 Copy
              </button>
            </div>

            {/* stdio MCP */}
            <div className="flex items-start justify-between bg-[#0d0b1a] rounded px-3 py-2 text-sm">
              <pre className="text-[#e2e0f0] whitespace-pre-wrap text-xs">
{JSON.stringify({ mcpServers: { smm: integrationConfig.stdio } }, null, 2)}
              </pre>
              <button onClick={() => copyToClipboard(JSON.stringify({ mcpServers: { smm: integrationConfig.stdio } }, null, 2))}
                      className="text-[#a78bfa] hover:text-[#c4b5fd] text-xs shrink-0 ml-2 mt-1">
                📋 Copy
              </button>
            </div>

            {/* SSE MCP */}
            <div className="flex items-start justify-between bg-[#0d0b1a] rounded px-3 py-2 text-sm">
              <pre className="text-[#e2e0f0] whitespace-pre-wrap text-xs">
{JSON.stringify({ mcpServers: { smm: integrationConfig.sse } }, null, 2)}
              </pre>
              <button onClick={() => copyToClipboard(JSON.stringify({ mcpServers: { smm: integrationConfig.sse } }, null, 2))}
                      className="text-[#a78bfa] hover:text-[#c4b5fd] text-xs shrink-0 ml-2 mt-1">
                📋 Copy
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Title */}
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold mb-2">
          <span className="text-[#a78bfa]">Search</span> Your Documents
        </h1>
        <p className="text-gray-500 text-sm">{'> 语义搜索你的本地文档库_'}</p>
      </div>

      {/* Search Box */}
      <div className="mb-6">
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

        {/* Options */}
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
            scope: {' '}
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

      {!loading && results.length > 0 && (
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

      {!loading && results.length === 0 && query && (
        <div className="text-center text-gray-500 py-8">没有找到结果</div>
      )}

      {/* Stats bar */}
      <div className="mt-8 flex justify-center gap-6 text-xs text-gray-500 border-t border-[#2d2a4a] pt-4">
        <span>{collections.length} collections</span>
        <span>{collections.reduce((s, c) => s + (c.total_chunks || 0), 0).toLocaleString()} chunks</span>
      </div>
    </div>
  )
}
