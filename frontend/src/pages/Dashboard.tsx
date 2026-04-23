import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import {
  User,
  Mail,
  Phone,
  Briefcase,
  GraduationCap,
  Wrench,
  Languages,
  Edit2,
  Save,
  X,
  Loader2,
  Sparkles,
  ArrowRight
} from 'lucide-react'
import { cvApi } from '../services/api'
import type { ParsedProfile } from '../types'

export default function Dashboard() {
  const { cvId } = useParams<{ cvId: string }>()
  const [isEditing, setIsEditing] = useState(false)
  const [editedProfile, setEditedProfile] = useState<ParsedProfile | null>(null)

  // Fetch profile
  const { data: profile, isLoading, error } = useQuery({
    queryKey: ['profile', cvId],
    queryFn: () => cvApi.getProfile(cvId!),
    enabled: !!cvId,
  })

  // Update profile mutation
  const updateMutation = useMutation({
    mutationFn: (data: ParsedProfile) => cvApi.updateProfile(cvId!, data),
    onSuccess: () => {
      toast.success('Perfil actualizado')
      setIsEditing(false)
    },
    onError: () => {
      toast.error('Error al actualizar el perfil')
    },
  })

  const handleEdit = () => {
    if (profile) {
      setEditedProfile({ ...profile })
      setIsEditing(true)
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
    setEditedProfile(null)
  }

  const handleSave = () => {
    if (editedProfile) {
      updateMutation.mutate(editedProfile)
    }
  }

  const updateField = (field: keyof ParsedProfile, value: any) => {
    if (editedProfile) {
      setEditedProfile({ ...editedProfile, [field]: value })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-primary-600" />
          <p className="text-gray-600">Cargando tu perfil...</p>
        </div>
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="text-center py-20">
        <div className="text-red-500 mb-4">Error al cargar el perfil</div>
        <p className="text-gray-600">Por favor intenta de nuevo más tarde</p>
      </div>
    )
  }

  const displayProfile = isEditing && editedProfile ? editedProfile : profile

  const completionPercentage = calculateCompletion(profile)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Tu Perfil</h1>
          <p className="text-gray-600">Revisa y edita la información extraída de tu CV</p>
        </div>

        <div className="flex items-center gap-4">
          {/* Completion indicator */}
          <div className="flex items-center gap-2 text-sm">
            <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all"
                style={{ width: `${completionPercentage}%` }}
              />
            </div>
            <span className="text-gray-600">{completionPercentage}% completo</span>
          </div>

          {isEditing ? (
            <div className="flex gap-2">
              <button
                onClick={handleCancel}
                className="btn-outline"
                disabled={updateMutation.isPending}
              >
                <X className="w-4 h-4 mr-1" />
                Cancelar
              </button>
              <button
                onClick={handleSave}
                className="btn-primary"
                disabled={updateMutation.isPending}
              >
                {updateMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-1" />
                ) : (
                  <Save className="w-4 h-4 mr-1" />
                )}
                Guardar
              </button>
            </div>
          ) : (
            <button onClick={handleEdit} className="btn-outline">
              <Edit2 className="w-4 h-4 mr-1" />
              Editar perfil
            </button>
          )}
        </div>
      </div>

      {/* Contact Info */}
      <section className="card">
        <div className="flex items-center gap-2 mb-4">
          <User className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-bold">Información de Contacto</h2>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="label">Nombre completo</label>
            {isEditing ? (
              <input
                type="text"
                className="input"
                value={displayProfile.full_name || ''}
                onChange={(e) => updateField('full_name', e.target.value)}
              />
            ) : (
              <div className="p-2 bg-gray-50 rounded-lg flex items-center gap-2">
                <User className="w-4 h-4 text-gray-400" />
                <span>{displayProfile.full_name || 'No especificado'}</span>
              </div>
            )}
          </div>

          <div>
            <label className="label">Email</label>
            {isEditing ? (
              <input
                type="email"
                className="input"
                value={displayProfile.email || ''}
                onChange={(e) => updateField('email', e.target.value)}
              />
            ) : (
              <div className="p-2 bg-gray-50 rounded-lg flex items-center gap-2">
                <Mail className="w-4 h-4 text-gray-400" />
                <span>{displayProfile.email || 'No especificado'}</span>
              </div>
            )}
          </div>

          <div>
            <label className="label">Teléfono</label>
            {isEditing ? (
              <input
                type="tel"
                className="input"
                value={displayProfile.phone || ''}
                onChange={(e) => updateField('phone', e.target.value)}
              />
            ) : (
              <div className="p-2 bg-gray-50 rounded-lg flex items-center gap-2">
                <Phone className="w-4 h-4 text-gray-400" />
                <span>{displayProfile.phone || 'No especificado'}</span>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Summary */}
      <section className="card">
        <h2 className="text-lg font-bold mb-4">Resumen Profesional</h2>
        {isEditing ? (
          <textarea
            className="input min-h-[100px]"
            value={displayProfile.summary || ''}
            onChange={(e) => updateField('summary', e.target.value)}
            placeholder="Breve descripción de tu perfil profesional..."
          />
        ) : (
          <p className="text-gray-600">
            {displayProfile.summary || 'No se encontró resumen en el CV'}
          </p>
        )}
      </section>

      {/* Experience */}
      <section className="card">
        <div className="flex items-center gap-2 mb-4">
          <Briefcase className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-bold">Experiencia Laboral</h2>
        </div>

        <div className="space-y-4">
          {displayProfile.experience?.map((exp, index) => (
            <div key={index} className="border-l-2 border-primary-200 pl-4">
              {isEditing ? (
                <div className="space-y-2">
                  <input
                    className="input font-medium"
                    value={exp.title}
                    onChange={(e) => {
                      const newExp = [...displayProfile.experience]
                      newExp[index] = { ...exp, title: e.target.value }
                      updateField('experience', newExp)
                    }}
                    placeholder="Cargo"
                  />
                  <input
                    className="input text-sm"
                    value={exp.company}
                    onChange={(e) => {
                      const newExp = [...displayProfile.experience]
                      newExp[index] = { ...exp, company: e.target.value }
                      updateField('experience', newExp)
                    }}
                    placeholder="Empresa"
                  />
                </div>
              ) : (
                <>
                  <h3 className="font-semibold text-gray-900">{exp.title}</h3>
                  <p className="text-primary-600">{exp.company}</p>
                  <p className="text-sm text-gray-500">
                    {exp.start_date} - {exp.end_date || 'Presente'}
                  </p>
                  {exp.description && (
                    <p className="text-gray-600 text-sm mt-2">{exp.description}</p>
                  )}
                </>
              )}
            </div>
          ))}

          {(!displayProfile.experience || displayProfile.experience.length === 0) && (
            <p className="text-gray-500 italic">No se encontró experiencia laboral</p>
          )}
        </div>
      </section>

      {/* Education */}
      <section className="card">
        <div className="flex items-center gap-2 mb-4">
          <GraduationCap className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-bold">Educación</h2>
        </div>

        <div className="space-y-4">
          {displayProfile.education?.map((edu, index) => (
            <div key={index} className="border-l-2 border-secondary-200 pl-4">
              {isEditing ? (
                <div className="space-y-2">
                  <input
                    className="input font-medium"
                    value={edu.degree}
                    onChange={(e) => {
                      const newEdu = [...displayProfile.education]
                      newEdu[index] = { ...edu, degree: e.target.value }
                      updateField('education', newEdu)
                    }}
                    placeholder="Título"
                  />
                  <input
                    className="input text-sm"
                    value={edu.institution}
                    onChange={(e) => {
                      const newEdu = [...displayProfile.education]
                      newEdu[index] = { ...edu, institution: e.target.value }
                      updateField('education', newEdu)
                    }}
                    placeholder="Institución"
                  />
                </div>
              ) : (
                <>
                  <h3 className="font-semibold text-gray-900">{edu.degree}</h3>
                  <p className="text-secondary-600">{edu.institution}</p>
                  <p className="text-sm text-gray-500">
                    {edu.start_date} - {edu.end_date}
                  </p>
                </>
              )}
            </div>
          ))}

          {(!displayProfile.education || displayProfile.education.length === 0) && (
            <p className="text-gray-500 italic">No se encontró educación</p>
          )}
        </div>
      </section>

      {/* Skills */}
      <section className="card">
        <div className="flex items-center gap-2 mb-4">
          <Wrench className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-bold">Habilidades</h2>
        </div>

        <div className="flex flex-wrap gap-2">
          {displayProfile.skills?.map((skill, index) => (
            <span
              key={index}
              className={`
                px-3 py-1 rounded-full text-sm font-medium
                ${skill.category === 'technical'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-purple-100 text-purple-700'
                }
              `}
            >
              {skill.name}
              {skill.level && <span className="opacity-60 ml-1">({skill.level})</span>}
            </span>
          ))}

          {(!displayProfile.skills || displayProfile.skills.length === 0) && (
            <p className="text-gray-500 italic">No se encontraron habilidades</p>
          )}
        </div>
      </section>

      {/* Languages */}
      <section className="card">
        <div className="flex items-center gap-2 mb-4">
          <Languages className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-bold">Idiomas</h2>
        </div>

        <div className="space-y-2">
          {displayProfile.languages?.map((lang, index) => (
            <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
              <span className="font-medium">{lang.name}</span>
              <span className="text-sm text-gray-500 capitalize">{lang.level}</span>
            </div>
          ))}

          {(!displayProfile.languages || displayProfile.languages.length === 0) && (
            <p className="text-gray-500 italic">No se encontraron idiomas</p>
          )}
        </div>
      </section>

      {/* Next steps */}
      {completionPercentage >= 50 && !isEditing && (
        <div className="bg-gradient-to-r from-primary-600 to-secondary-600 rounded-xl p-6 text-white">
          <div className="flex items-start gap-4">
            <div className="bg-white/20 p-3 rounded-xl">
              <Sparkles className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold mb-2">¡Tu perfil está listo!</h3>
              <p className="text-primary-100 mb-4">
                Ahora puedes comenzar a buscar empleos que coincidan con tu experiencia y habilidades.
              </p>
              <button className="inline-flex items-center gap-2 bg-white text-primary-600 px-6 py-3 rounded-lg font-medium hover:bg-primary-50 transition-colors">
                Buscar empleos
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function calculateCompletion(profile: ParsedProfile): number {
  let score = 0
  let total = 7

  if (profile.full_name) score++
  if (profile.email) score++
  if (profile.phone) score++
  if (profile.summary) score++
  if (profile.experience?.length > 0) score++
  if (profile.education?.length > 0) score++
  if (profile.skills?.length > 0) score++

  return Math.round((score / total) * 100)
}
