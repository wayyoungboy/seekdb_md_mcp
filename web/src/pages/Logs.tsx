import { useState, useEffect, useRef } from 'react'

const API = import.meta.env.VITE_API_BASE || ''

export default function Logs() {
  const [logs, setLogs] = useState<string[]>([])
  const [status, setStatus] = useState<any>(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const wsRef = useRef<WebSocket | null>(null)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Load status
    fetch(`${API}/api/status`)
      .then(r => r.json())
      .then(setStatus)
      .catch(() => {})

    // Connect WebSocket
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${proto}//${location.host}/api/ws/logs`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onmessage = (e) => {
      setLogs(prev => [...prev.slice(-200), e.data])
    }

    ws.onclose = () => {
      // Retry connection after 3s
      setTimeout(() => {
        const ws2 = new WebSocket(wsUrl)
        wsRef.current = ws2
        ws2.onmessage = (e) => {
          setLogs(prev => [...prev.slice(-200), e.data])
        }
      }, 3000)
    }

    return () => ws.close()
  }, [])

  useEffect(() => {
    if (autoScroll && endRef.current) {
      endRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, autoScroll])

  const stopDaemon = async () => {
    await fetch(`${API}/api/daemon/stop`, { method: 'POST' })
    setTimeout(() => window.location.reload(), 1500)
  }

  const restartDaemon = async () => {
    await fetch(`${API}/api/daemon/restart`, { method: 'POST' })
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <h1 className="text-xl font-bold mb-6">Logs</h1>

      {/* Daemon Status */}
      {status && (
        <div className="mb-6 rounded-lg border border-[#2d2a4a] p-4" style={{ background: '#13112a' }}>
          <div className="flex items-center gap-3 mb-3">
            <span className={`inline-block w-2.5 h-2.5 rounded-full ${status.running ? 'bg-[#34d399]' : 'bg-[#f87171]'}`} />
            <span className="text-sm text-gray-300">
              {status.running ? `Running (PID ${status.pid})` : 'Stopped'}
            </span>
            {status.started_at && (
              <span className="text-gray-500 text-xs">started {status.started_at}</span>
            )}
          </div>
          <div className="flex gap-6 text-xs text-gray-400">
            <span>Web: http://{status.web_port ? `127.0.0.1:${status.web_port}` : '---'}</span>
            <span>MCP SSE: http://{status.sse_port ? `127.0.0.1:${status.sse_port}/sse` : '---'}</span>
          </div>
          <div className="flex gap-3 mt-3">
            {status.running && (
              <>
                <button onClick={stopDaemon}
                        className="px-3 py-1 bg-[#f87171]/10 text-[#f87171] border border-[#f87171]/30 rounded text-xs hover:bg-[#f87171]/20 transition-colors">
                  Stop
                </button>
                <button onClick={restartDaemon}
                        className="px-3 py-1 bg-[#a78bfa]/10 text-[#a78bfa] border border-[#a78bfa]/30 rounded text-xs hover:bg-[#a78bfa]/20 transition-colors">
                  Restart
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Log viewer */}
      <div className="rounded-lg border border-[#2d2a4a] overflow-hidden" style={{ background: '#13112a' }}>
        <div className="flex items-center justify-between px-4 py-2 border-b border-[#2d2a4a]"
             style={{ background: '#1a1830' }}>
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
          </div>
          <div className="flex items-center gap-3">
            <span className="text-gray-400 text-xs">实时日志</span>
            <label className="flex items-center gap-1 text-xs text-gray-400 cursor-pointer">
              <input type="checkbox" checked={autoScroll} onChange={e => setAutoScroll(e.target.checked)}
                     className="accent-[#a78bfa]" />
              自动滚动
            </label>
          </div>
        </div>
        <div className="p-3 h-[500px] overflow-auto text-xs font-mono space-y-0.5"
             style={{ background: '#0d0b1a' }}>
          {logs.map((line, i) => (
            <div key={i} className="text-gray-400 leading-relaxed">{line}</div>
          ))}
          <div ref={endRef} />
        </div>
      </div>
    </div>
  )
}
