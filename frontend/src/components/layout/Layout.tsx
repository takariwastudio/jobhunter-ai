import { Link, useLocation, useNavigate } from 'react-router-dom'
import { FileUp, Home, Sparkles, LogOut, User, Search } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import type { ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, loading, logout } = useAuth()

  const navItems = [
    { path: '/', label: 'Inicio', icon: Home },
    { path: '/upload', label: 'Subir CV', icon: FileUp, requiresAuth: true },
    { path: '/jobs', label: 'Empleos', icon: Search, requiresAuth: true },
  ]

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2 group">
              <div className="bg-gradient-to-r from-primary-500 to-secondary-500 p-2 rounded-lg group-hover:scale-105 transition-transform">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent">
                JobHunter AI
              </span>
            </Link>

            <nav className="hidden md:flex items-center gap-1">
              {navItems.map((item) => {
                if (item.requiresAuth && !user) return null
                const Icon = item.icon
                const isActive = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                      isActive
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-600 hover:text-primary-600 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </Link>
                )
              })}
            </nav>

            <div className="flex items-center gap-2">
              {!loading && (
                user ? (
                  <div className="flex items-center gap-3">
                    <div className="hidden sm:flex items-center gap-2 text-sm text-gray-600">
                      {user.avatar_url ? (
                        <img src={user.avatar_url} alt="" className="w-7 h-7 rounded-full object-cover" />
                      ) : (
                        <div className="w-7 h-7 rounded-full bg-primary-100 flex items-center justify-center">
                          <User className="w-4 h-4 text-primary-600" />
                        </div>
                      )}
                      <span className="font-medium">{user.display_name || user.email || user.phone}</span>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      <span className="hidden sm:inline">Salir</span>
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Link to="/login" className="btn-outline text-sm py-1.5 px-4">
                      Iniciar sesión
                    </Link>
                    <Link to="/register" className="btn-primary text-sm py-1.5 px-4">
                      Registrarse
                    </Link>
                  </div>
                )
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-gray-500 text-sm">
            <p>© 2026 JobHunter AI - Tu asistente para encontrar empleo</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
