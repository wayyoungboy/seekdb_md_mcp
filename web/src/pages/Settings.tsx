import { useState, useEffect } from 'react'

const API = import.meta.env.VITE_API_BASE || ''

export default function Settings() {
  const [config, setConfig] = useState<any>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    fetch(`${API}/api/config`)
      .then(r => r.json())
      .then(setConfig)
      .catch(() => {})
  }, [])

  const update = (path: string[], value: any) => {
    setConfig(prev => {
      const copy = JSON.parse(JSON.stringify(prev))
      let obj = copy
      for (let i = 0; i < path.length - 1; i++) obj = obj[path[i]]
      obj[path[path.length - 1]] = value
      return copy
    })
    setSaved(false)
  }

  const save = async () => {
    await fetch(`${API}/api/config`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config }),
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  if (!config) return <div className="text-center text-gray-500 py-12">Loading...</div>

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <h1 className="text-xl font-bold mb-6">Settings</h1>

      {/* Database */}
      <div className="mb-6 rounded-lg border border-[#2d2a4a] p-4" style={{ background: '#13112a' }}>
        <h2 className="text-[#a78bfa] text-sm font-medium mb-3">Database</h2>
        <div className="flex gap-4 mb-3">
          {['embedded', 'server'].map(m => (
            <label key={m} className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
              <input type="radio" name="db_mode" checked={config.database.mode === m}
                     onChange={() => update(['database', 'mode'], m)} />
              {m}
            </label>
          ))}
        </div>
        {config.database.mode === 'embedded' && (
          <div className="text-gray-400 text-xs">
            Path: {config.database.embedded.path}
          </div>
        )}
        {config.database.mode === 'server' && (
          <div className="grid grid-cols-2 gap-2">
            {(['host', 'port', 'user', 'password', 'database'] as const).map(key => (
              <div key={key}>
                <label className="text-gray-500 text-xs">{key}</label>
                <input
                  type={key === 'password' ? 'password' : 'text'}
                  value={config.database.server[key]}
                  onChange={e => update(['database', 'server', key], e.target.value)}
                  className="w-full bg-[#0d0b1a] border border-[#2d2a4a] rounded px-2 py-1 text-xs text-[#e2e0f0] focus:outline-none focus:border-[#a78bfa]"
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Embedding */}
      <div className="mb-6 rounded-lg border border-[#2d2a4a] p-4" style={{ background: '#13112a' }}>
        <h2 className="text-[#a78bfa] text-sm font-medium mb-3">Embedding</h2>
        <div className="text-sm text-gray-300">
          Provider:{' '}
          <select
            value={config.embedding.provider}
            onChange={e => update(['embedding', 'provider'], e.target.value)}
            className="bg-[#0d0b1a] border border-[#2d2a4a] rounded px-2 py-1 text-xs text-[#e2e0f0] focus:outline-none"
          >
            {['default', 'openai', 'jina', 'ollama', 'huggingface', 'qwen', 'cohere'].map(p => (
              <option key={p} value={p} className="bg-[#13112a]">{p}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Chunking */}
      <div className="mb-6 rounded-lg border border-[#2d2a4a] p-4" style={{ background: '#13112a' }}>
        <h2 className="text-[#a78bfa] text-sm font-medium mb-3">Chunking</h2>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-gray-500 text-xs">Strategy</label>
            <select
              value={config.chunking.strategy}
              onChange={e => update(['chunking', 'strategy'], e.target.value)}
              className="w-full bg-[#0d0b1a] border border-[#2d2a4a] rounded px-2 py-1 text-xs text-[#e2e0f0] focus:outline-none"
            >
              <option value="semantic" className="bg-[#13112a]">semantic</option>
              <option value="fixed" className="bg-[#13112a]">fixed</option>
            </select>
          </div>
          <div>
            <label className="text-gray-500 text-xs">Max chunk size</label>
            <input
              type="number"
              value={config.chunking.max_chunk_size}
              onChange={e => update(['chunking', 'max_chunk_size'], parseInt(e.target.value))}
              className="w-full bg-[#0d0b1a] border border-[#2d2a4a] rounded px-2 py-1 text-xs text-[#e2e0f0] focus:outline-none"
            />
          </div>
          <div>
            <label className="text-gray-500 text-xs">Overlap</label>
            <input
              type="number"
              value={config.chunking.overlap}
              onChange={e => update(['chunking', 'overlap'], parseInt(e.target.value))}
              className="w-full bg-[#0d0b1a] border border-[#2d2a4a] rounded px-2 py-1 text-xs text-[#e2e0f0] focus:outline-none"
            />
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="mb-6 rounded-lg border border-[#2d2a4a] p-4" style={{ background: '#13112a' }}>
        <h2 className="text-[#a78bfa] text-sm font-medium mb-3">Search</h2>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-gray-500 text-xs">Mode</label>
            <select
              value={config.search.mode}
              onChange={e => update(['search', 'mode'], e.target.value)}
              className="w-full bg-[#0d0b1a] border border-[#2d2a4a] rounded px-2 py-1 text-xs text-[#e2e0f0] focus:outline-none"
            >
              {['hybrid', 'vector', 'fulltext'].map(m => (
                <option key={m} value={m} className="bg-[#13112a]">{m}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-gray-500 text-xs">N results</label>
            <input
              type="number"
              value={config.search.n_results}
              onChange={e => update(['search', 'n_results'], parseInt(e.target.value))}
              className="w-full bg-[#0d0b1a] border border-[#2d2a4a] rounded px-2 py-1 text-xs text-[#e2e0f0] focus:outline-none"
            />
          </div>
        </div>
      </div>

      {/* Save */}
      <div className="flex items-center gap-3">
        <button onClick={save}
                className="px-6 py-2 bg-[#a78bfa] text-[#0d0b1a] rounded text-sm font-medium hover:bg-[#c4b5fd] transition-colors">
          Save
        </button>
        {saved && <span className="text-[#34d399] text-sm">✓ Saved</span>}
      </div>
    </div>
  )
}
