import { useState, useEffect } from 'react'

interface Collection {
  collection: string
  path: string
  total_chunks: number
}

interface FileInfo {
  file_path: string
  file_name: string
  chunks: number
  indexed_at: string
}

const API = import.meta.env.VITE_API_BASE || ''

export default function Documents() {
  const [collections, setCollections] = useState<Collection[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [files, setFiles] = useState<FileInfo[]>([])
  const [importPath, setImportPath] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  const loadCollections = () => {
    fetch(`${API}/api/collections`)
      .then(r => r.json())
      .then(setCollections)
      .catch(() => {})
  }

  useEffect(loadCollections, [])

  useEffect(() => {
    if (!selected) { setFiles([]); return }
    fetch(`${API}/api/collections/${selected}`)
      .then(r => r.json())
      .then(d => setFiles(d.files || []))
      .catch(() => setFiles([]))
  }, [selected])

  const reindex = async (name: string) => {
    setRefreshing(true)
    await fetch(`${API}/api/collections/${name}/reindex`, { method: 'POST' })
    loadCollections()
    setRefreshing(false)
  }

  const deleteCollection = async (name: string) => {
    if (!confirm(`Delete collection "${name}"?`)) return
    await fetch(`${API}/api/collections/${name}`, { method: 'DELETE' })
    setSelected(null)
    loadCollections()
  }

  const importDirectory = async () => {
    if (!importPath.trim()) return
    await fetch(`${API}/api/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: importPath }),
    })
    setImportPath('')
    loadCollections()
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <h1 className="text-xl font-bold mb-6">Documents</h1>

      {/* Import */}
      <div className="mb-6 flex gap-2">
        <input
          value={importPath}
          onChange={e => setImportPath(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && importDirectory()}
          placeholder="/path/to/documents"
          className="flex-1 bg-[#13112a] border border-[#2d2a4a] rounded px-3 py-2 text-sm text-[#e2e0f0] placeholder-gray-600 focus:outline-none focus:border-[#a78bfa]"
        />
        <button onClick={importDirectory}
                className="px-4 py-2 bg-[#a78bfa] text-[#0d0b1a] rounded text-sm font-medium hover:bg-[#c4b5fd] transition-colors">
          + 导入目录
        </button>
      </div>

      {/* Collections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {collections.map(c => (
          <div
            key={c.collection}
            onClick={() => setSelected(selected === c.collection ? null : c.collection)}
            className={`rounded-lg border p-4 cursor-pointer transition-colors ${
              selected === c.collection
                ? 'border-[#a78bfa] bg-[#a78bfa]/5'
                : 'border-[#2d2a4a] bg-[#13112a] hover:border-[#a78bfa]/50'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[#a78bfa] font-medium">{c.collection}</span>
              <div className="flex gap-2">
                <button onClick={e => { e.stopPropagation(); reindex(c.collection) }}
                        className="text-gray-400 hover:text-[#a78bfa] text-xs" title="Reindex">
                  ↻
                </button>
                <button onClick={e => { e.stopPropagation(); deleteCollection(c.collection) }}
                        className="text-gray-400 hover:text-red-400 text-xs" title="Delete">
                  ✕
                </button>
              </div>
            </div>
            <p className="text-gray-500 text-xs truncate">{c.path}</p>
            <p className="text-gray-400 text-xs mt-1">{c.total_chunks || 0} chunks</p>
          </div>
        ))}
      </div>

      {/* Files in selected collection */}
      {selected && (
        <div className="mt-6 rounded-lg border border-[#2d2a4a] overflow-hidden" style={{ background: '#13112a' }}>
          <div className="px-4 py-2 border-b border-[#2d2a4a]" style={{ background: '#1a1830' }}>
            <span className="text-gray-400 text-sm">{selected} — {files.length} files</span>
          </div>
          <div className="divide-y divide-[#2d2a4a] max-h-96 overflow-auto">
            {files.map(f => (
              <div key={f.file_path} className="px-4 py-3 flex items-center justify-between hover:bg-[#1a1830]/50">
                <div>
                  <p className="text-[#e2e0f0] text-sm">{f.file_name}</p>
                  <p className="text-gray-500 text-xs truncate">{f.file_path}</p>
                </div>
                <div className="text-right text-xs text-gray-400">
                  <p>{f.chunks} chunks</p>
                  <p>{f.indexed_at}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {collections.length === 0 && (
        <div className="text-center text-gray-500 py-12">
          No collections yet. Import documents to get started.
        </div>
      )}
    </div>
  )
}
