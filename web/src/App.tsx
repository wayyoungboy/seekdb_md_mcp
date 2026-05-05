import { Outlet, NavLink, useLocation } from 'react-router-dom'

const navItems = [
  { path: '/', label: 'Search' },
  { path: '/documents', label: 'Documents' },
  { path: '/settings', label: 'Settings' },
  { path: '/logs', label: 'Logs' },
]

export default function App() {
  return (
    <div className="min-h-screen flex flex-col" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      {/* Navigation */}
      <nav className="border-b border-[#2d2a4a] px-6 py-3 flex items-center justify-between"
           style={{ background: '#13112a' }}>
        <div className="flex items-center gap-6">
          <span className="text-[#a78bfa] font-bold text-lg">smm</span>
          <div className="flex gap-4">
            {navItems.map(item => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `px-3 py-1 rounded transition-colors ${
                    isActive
                      ? 'text-[#a78bfa] bg-[#a78bfa]/10'
                      : 'text-gray-400 hover:text-gray-200'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        </div>
        <span className="text-gray-500 text-sm">seekdb Markdown MCP</span>
      </nav>

      {/* Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
