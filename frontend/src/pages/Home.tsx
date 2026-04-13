import { Link } from 'react-router-dom'
import { FileUp, Brain, Briefcase, ArrowRight, Zap, Globe, Shield } from 'lucide-react'

export default function Home() {
  const features = [
    {
      icon: FileUp,
      title: 'Sube tu CV',
      description: 'Sube tu CV en PDF, Word o imagen. Soportamos todos los formatos populares.',
    },
    {
      icon: Brain,
      title: 'IA lo analiza',
      description: 'Nuestra IA extrae tu experiencia, habilidades y educación automáticamente.',
    },
    {
      icon: Briefcase,
      title: 'Encuentra empleos',
      description: 'Busca empleos relevantes en todo el mundo que coincidan con tu perfil.',
    },
  ]

  const benefits = [
    { icon: Zap, title: 'Rápido', description: 'Procesa tu CV en segundos' },
    { icon: Globe, title: 'Global', description: 'Busca empleos en todo el mundo' },
    { icon: Shield, title: 'Seguro', description: 'Tu información está protegida' },
  ]

  return (
    <div className="space-y-16">
      {/* Hero */}
      <section className="text-center py-12">
        <div className="inline-flex items-center gap-2 bg-primary-50 text-primary-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
          <Zap className="w-4 h-4" />
          Potenciado por IA
        </div>

        <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
          Deja que la IA busque
          <span className="block text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-secondary-600">
            empleo por ti
          </span>
        </h1>

        <p className="text-lg md:text-xl text-gray-600 max-w-2xl mx-auto mb-8">
          Sube tu CV y deja que JobHunter AI analice tu perfil, busque vacantes
          relevantes globalmente y te sugiera las mejores oportunidades.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/upload"
            className="btn-primary gap-2 text-lg px-8 py-3"
          >
            Comenzar ahora
            <ArrowRight className="w-5 h-5" />
          </Link>

          <a
            href="#como-funciona"
            className="btn-outline text-lg px-8 py-3"
          >
            Ver cómo funciona
          </a>
        </div>
      </section>

      {/* Features */}
      <section id="como-funciona" className="py-12">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">¿Cómo funciona?</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Tres simples pasos para comenzar tu búsqueda de empleo automatizada
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div key={feature.title} className="card text-center group hover:shadow-lg transition-shadow">
                <div className="w-14 h-14 bg-gradient-to-br from-primary-100 to-secondary-100 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                  <Icon className="w-7 h-7 text-primary-600" />
                </div>
                <div className="text-sm font-bold text-primary-600 mb-2">
                  Paso {index + 1}
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </section>

      {/* Benefits */}
      <section className="py-12">
        <div className="bg-gradient-to-r from-primary-600 to-secondary-600 rounded-2xl p-8 md:p-12 text-white">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-2">¿Por qué JobHunter AI?</h2>
            <p className="text-primary-100">La herramienta que necesitas para tu búsqueda de empleo</p>
          </div>

          <div className="grid sm:grid-cols-3 gap-6">
            {benefits.map((benefit) => {
              const Icon = benefit.icon
              return (
                <div key={benefit.title} className="bg-white/10 backdrop-blur-sm rounded-xl p-6 text-center">
                  <Icon className="w-8 h-8 mx-auto mb-3" />
                  <h3 className="font-bold mb-1">{benefit.title}</h3>
                  <p className="text-sm text-primary-100">{benefit.description}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-12 text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">¿Listo para encontrar tu próximo empleo?</h2>
        <p className="text-gray-600 mb-8 max-w-xl mx-auto">
          Comienza subiendo tu CV y deja que nuestra IA haga el trabajo pesado por ti.
        </p>
        <Link
          to="/upload"
          className="btn-primary gap-2 text-lg px-8 py-3"
        >
          Subir mi CV
          <ArrowRight className="w-5 h-5" />
        </Link>
      </section>
    </div>
  )
}
