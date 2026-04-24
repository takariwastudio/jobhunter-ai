import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { Loader2, Sparkles, ArrowRight, Eye, EyeOff, CheckCircle } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const schema = z.object({
  full_name: z.string().min(2, 'Ingresa tu nombre completo'),
  email: z.string().email('Email inválido'),
  password: z.string().min(8, 'Mínimo 8 caracteres'),
  confirm_password: z.string(),
}).refine((d) => d.password === d.confirm_password, {
  message: 'Las contraseñas no coinciden',
  path: ['confirm_password'],
})

type Form = z.infer<typeof schema>

const OAUTH_PROVIDERS = [
  { id: 'google', label: 'Google' },
  { id: 'github', label: 'GitHub' },
]

export default function Register() {
  const { refresh } = useAuth()
  const navigate = useNavigate()
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [emailSent, setEmailSent] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
  })

  async function onSubmit(data: Form) {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: data.email,
          password: data.password,
          full_name: data.full_name,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Error al registrarse')
      }
      const user = await res.json()
      if (user.id) {
        // Session created (no email confirmation required)
        await refresh()
        navigate('/upload')
      } else {
        // Email confirmation required
        setEmailSent(true)
      }
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : 'Error al registrarse')
    } finally {
      setLoading(false)
    }
  }

  function handleOAuth(provider: string) {
    window.location.href = `${API_URL}/auth/oauth/${provider}`
  }

  if (emailSent) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Revisa tu email</h2>
          <p className="text-gray-600 mb-6">
            Te enviamos un enlace de confirmación. Una vez confirmado, podrás iniciar sesión.
          </p>
          <Link to="/login" className="btn-primary inline-flex items-center gap-2">
            Ir al login <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    )
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
          <h1 className="text-2xl font-bold text-gray-900">Crea tu cuenta</h1>
          <p className="text-gray-500 mt-1">
            ¿Ya tienes cuenta? <Link to="/login" className="text-primary-600 hover:underline font-medium">Inicia sesión</Link>
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-5">
          {/* OAuth */}
          <div className="space-y-2">
            {OAUTH_PROVIDERS.map((p) => (
              <button
                key={p.id}
                onClick={() => handleOAuth(p.id)}
                className="w-full flex items-center justify-center gap-3 py-2.5 px-4 border border-gray-300 hover:border-gray-400 rounded-lg font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors text-sm"
              >
                Registrarse con {p.label}
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
              <label className="label">Nombre completo</label>
              <input type="text" className="input" placeholder="Ana García" {...register('full_name')} />
              {errors.full_name && <p className="text-red-500 text-xs mt-1">{errors.full_name.message}</p>}
            </div>

            <div>
              <label className="label">Email</label>
              <input type="email" className="input" placeholder="tu@email.com" {...register('email')} />
              {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="label">Contraseña</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="input pr-10"
                  placeholder="Mínimo 8 caracteres"
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

            <div>
              <label className="label">Confirmar contraseña</label>
              <input
                type={showPassword ? 'text' : 'password'}
                className="input"
                placeholder="Repite la contraseña"
                {...register('confirm_password')}
              />
              {errors.confirm_password && <p className="text-red-500 text-xs mt-1">{errors.confirm_password.message}</p>}
            </div>

            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : (
                <span className="flex items-center justify-center gap-2">
                  Crear cuenta <ArrowRight className="w-4 h-4" />
                </span>
              )}
            </button>
          </form>

          <p className="text-xs text-gray-400 text-center">
            Al registrarte aceptas nuestros Términos de uso y Política de privacidad.
          </p>
        </div>
      </div>
    </div>
  )
}
