import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { Loader2, Sparkles, ArrowRight, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const schema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(6, 'Mínimo 6 caracteres'),
})

type Form = z.infer<typeof schema>

const OAUTH_PROVIDERS = [
  { id: 'google', label: 'Google' },
  { id: 'github', label: 'GitHub' },
]

export default function Login() {
  const { refresh } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)

  const oauthError = searchParams.get('error')

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
  })

  async function onSubmit(data: Form) {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Credenciales incorrectas')
      }
      await refresh()
      navigate('/upload')
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : 'Error al iniciar sesión')
    } finally {
      setLoading(false)
    }
  }

  function handleOAuth(provider: string) {
    globalThis.location.href = `${API_URL}/auth/oauth/${provider}`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="bg-gradient-to-r from-primary-500 to-secondary-500 p-2.5 rounded-xl">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent">
              JobHunter AI
            </span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Inicia sesión</h1>
          <p className="text-gray-500 mt-1">
            ¿No tienes cuenta?{' '}
            <Link to="/register" className="text-primary-600 hover:underline font-medium">Regístrate</Link>
          </p>
        </div>

        {oauthError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            Error al autenticar: {oauthError.replace(/_/g, ' ')}
          </div>
        )}

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-5">
          <div className="space-y-2">
            {OAUTH_PROVIDERS.map((p) => (
              <button
                key={p.id}
                onClick={() => handleOAuth(p.id)}
                className="w-full flex items-center justify-center gap-3 py-2.5 px-4 border border-gray-300 hover:border-gray-400 rounded-lg font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors text-sm"
              >
                Continuar con {p.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-gray-200" />
            <span className="text-xs text-gray-400 font-medium">O con email</span>
            <div className="flex-1 h-px bg-gray-200" />
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label htmlFor="email" className="label">Email</label>
              <input id="email" type="email" className="input" placeholder="tu@email.com" {...register('email')} />
              {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
            </div>
            <div>
              <label htmlFor="password" className="label">Contraseña</label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  className="input pr-10"
                  placeholder="••••••••"
                  {...register('password')}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
            </div>
            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : (
                <span className="flex items-center justify-center gap-2">
                  Iniciar sesión <ArrowRight className="w-4 h-4" />
                </span>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
