import { useState, useCallback, useEffect, useMemo } from 'react'
import { Search, MapPin, Bookmark, BookmarkCheck, ExternalLink, Briefcase, Globe, Wifi, Sparkles, ChevronDown, ChevronUp } from 'lucide-react'
import { jobApi, cvApi, matchApi } from '../services/api'
import type { JobSearchResult, SavedJob, JobSearchParams, MatchScore } from '../types'

const COUNTRIES = [
  { code: 'es', label: 'España' },
  { code: 'mx', label: 'México' },
  { code: 'ar', label: 'Argentina' },
  { code: 'co', label: 'Colombia' },
  { code: 'br', label: 'Brasil' },
  { code: 'us', label: 'Estados Unidos' },
  { code: 'gb', label: 'Reino Unido' },
]

const SOURCE_LABELS: Record<string, string> = {
  adzuna: 'Adzuna',
  jsearch: 'JSearch',
}

const SOURCE_COLORS: Record<string, string> = {
  adzuna: 'bg-blue-100 text-blue-700',
  jsearch: 'bg-purple-100 text-purple-700',
}

function scoreColor(score: number): string {
  if (score >= 75) return 'bg-emerald-100 text-emerald-700 border-emerald-200'
  if (score >= 50) return 'bg-amber-100 text-amber-700 border-amber-200'
  if (score >= 25) return 'bg-orange-100 text-orange-700 border-orange-200'
  return 'bg-red-100 text-red-700 border-red-200'
}

function scoreLabel(score: number): string {
  if (score >= 75) return 'Muy compatible'
  if (score >= 50) return 'Compatible'
  if (score >= 25) return 'Parcial'
  return 'Baja'
}

type Tab = 'search' | 'saved'

function MatchBadge({ score }: { score: number }) {
  return (
    <div className={`shrink-0 flex flex-col items-center justify-center w-14 h-14 rounded-xl border text-center ${scoreColor(score)}`}>
      <span className="text-xl font-bold leading-none">{score}</span>
      <span className="text-[10px] leading-tight mt-0.5 font-medium">{scoreLabel(score)}</span>
    </div>
  )
}

function SkillPills({ skills, variant }: { skills: string[]; variant: 'match' | 'miss' }) {
  if (!skills.length) return null
  const colors = variant === 'match'
    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
    : 'bg-red-50 text-red-600 border-red-200'
  return (
    <div className="flex flex-wrap gap-1">
      {skills.map((s) => (
        <span key={s} className={`text-xs px-2 py-0.5 rounded-full border ${colors}`}>{s}</span>
      ))}
    </div>
  )
}

function JobCard({
  job,
  onSave,
  onUnsave,
  saving,
  matchScore,
}: {
  job: JobSearchResult | SavedJob
  onSave?: (job: JobSearchResult) => void
  onUnsave?: (externalId: string) => void
  saving?: boolean
  matchScore?: MatchScore
}) {
  const [expanded, setExpanded] = useState(false)
  const isSearchResult = (job as JobSearchResult).is_saved !== undefined
  const isSaved = isSearchResult ? (job as JobSearchResult).is_saved : true
  const externalId = job.external_id
  const sourceUrl = job.source_url

  function handleToggle() {
    if (isSaved) {
      onUnsave?.(externalId)
    } else if (isSearchResult) {
      onSave?.(job as JobSearchResult)
    }
  }

  const hasSkillInfo = matchScore && (matchScore.matching_skills.length > 0 || matchScore.missing_skills.length > 0)

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow flex flex-col gap-3">
      <div className="flex items-start gap-3">
        {matchScore && <MatchBadge score={matchScore.score} />}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 text-base leading-snug truncate">{job.title}</h3>
          <p className="text-sm text-gray-600 mt-0.5">{job.company}</p>
        </div>
        <button
          onClick={handleToggle}
          disabled={saving}
          className={`shrink-0 p-1.5 rounded-lg transition-colors ${
            isSaved
              ? 'text-primary-600 bg-primary-50 hover:bg-red-50 hover:text-red-500'
              : 'text-gray-400 hover:text-primary-600 hover:bg-primary-50'
          }`}
          title={isSaved ? 'Quitar de guardados' : 'Guardar empleo'}
        >
          {isSaved ? <BookmarkCheck className="w-5 h-5" /> : <Bookmark className="w-5 h-5" />}
        </button>
      </div>

      <div className="flex flex-wrap gap-2 text-xs">
        {job.location && (
          <span className="flex items-center gap-1 text-gray-500">
            <MapPin className="w-3.5 h-3.5" />
            {job.location}
          </span>
        )}
        {job.remote && (
          <span className="flex items-center gap-1 text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full font-medium">
            <Wifi className="w-3 h-3" />
            Remoto
          </span>
        )}
        {job.job_type && (
          <span className="flex items-center gap-1 text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
            <Briefcase className="w-3 h-3" />
            {job.job_type}
          </span>
        )}
        {job.salary_range && (
          <span className="text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full font-medium">
            {job.salary_range}
          </span>
        )}
        <span className={`px-2 py-0.5 rounded-full font-medium ${SOURCE_COLORS[job.source] ?? 'bg-gray-100 text-gray-600'}`}>
          {SOURCE_LABELS[job.source] ?? job.source}
        </span>
      </div>

      <p className="text-sm text-gray-600 line-clamp-3 leading-relaxed">
        {job.description}
      </p>

      {matchScore && (
        <div className="border-t border-gray-100 pt-2 space-y-2">
          <p className="text-xs text-gray-500 leading-relaxed italic">"{matchScore.reasoning}"</p>
          {hasSkillInfo && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
            >
              {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              {expanded ? 'Ocultar habilidades' : 'Ver habilidades'}
            </button>
          )}
          {expanded && hasSkillInfo && (
            <div className="space-y-1.5">
              {matchScore.matching_skills.length > 0 && (
                <div>
                  <p className="text-[10px] uppercase tracking-wide text-emerald-600 font-semibold mb-1">Tienes</p>
                  <SkillPills skills={matchScore.matching_skills} variant="match" />
                </div>
              )}
              {matchScore.missing_skills.length > 0 && (
                <div>
                  <p className="text-[10px] uppercase tracking-wide text-red-500 font-semibold mb-1">Te faltan</p>
                  <SkillPills skills={matchScore.missing_skills} variant="miss" />
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {sourceUrl && (
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-primary-600 hover:text-primary-700 mt-auto"
        >
          Ver oferta
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      )}
    </div>
  )
}

export default function JobSearch() {
  const [tab, setTab] = useState<Tab>('search')
  const [query, setQuery] = useState('')
  const [location, setLocation] = useState('')
  const [country, setCountry] = useState('es')
  const [remote, setRemote] = useState<boolean | undefined>(undefined)
  const [source, setSource] = useState<'all' | 'adzuna' | 'jsearch'>('all')
  const [page, setPage] = useState(1)

  const [results, setResults] = useState<JobSearchResult[]>([])
  const [savedJobs, setSavedJobs] = useState<SavedJob[]>([])
  const [loading, setLoading] = useState(false)
  const [savingId, setSavingId] = useState<string | null>(null)
  const [searched, setSearched] = useState(false)
  const [savedLoaded, setSavedLoaded] = useState(false)

  // Matching state
  const [activeCvId, setActiveCvId] = useState<string | null>(null)
  const [matching, setMatching] = useState(false)
  const [matchScores, setMatchScores] = useState<Record<string, MatchScore>>({})
  const [profileName, setProfileName] = useState<string | null>(null)

  useEffect(() => {
    cvApi.list().then((cvs) => {
      const parsed = cvs.find((cv) => cv.status === 'completed')
      if (parsed) setActiveCvId(parsed.id)
    }).catch(() => {})
  }, [])

  const sortedResults = useMemo(() => {
    if (!Object.keys(matchScores).length) return results
    return [...results].sort((a, b) => {
      const scoreA = matchScores[a.external_id]?.score ?? -1
      const scoreB = matchScores[b.external_id]?.score ?? -1
      return scoreB - scoreA
    })
  }, [results, matchScores])

  const doSearch = useCallback(async (p = 1) => {
    if (!query.trim()) return
    setLoading(true)
    setPage(p)
    setMatchScores({})
    setProfileName(null)
    try {
      const params: JobSearchParams = {
        q: query.trim(),
        location: location || undefined,
        country,
        remote: remote ?? undefined,
        page: p,
        limit: 10,
        source,
      }
      const data = await jobApi.search(params)
      setResults(data)
      setSearched(true)
    } finally {
      setLoading(false)
    }
  }, [query, location, country, remote, source])

  async function handleMatch() {
    if (!activeCvId || !results.length) return
    setMatching(true)
    try {
      const jobs = results.map((j) => ({
        external_id: j.external_id,
        title: j.title,
        company: j.company,
        description: j.description,
      }))
      const response = await matchApi.matchJobs(activeCvId, jobs)
      const map: Record<string, MatchScore> = {}
      for (const r of response.results) {
        map[r.external_id] = r
      }
      setMatchScores(map)
      setProfileName(response.profile_name)
    } finally {
      setMatching(false)
    }
  }

  async function loadSaved() {
    if (savedLoaded) return
    setLoading(true)
    try {
      const data = await jobApi.getSaved()
      setSavedJobs(data)
      setSavedLoaded(true)
    } finally {
      setLoading(false)
    }
  }

  function handleTabChange(t: Tab) {
    setTab(t)
    if (t === 'saved') loadSaved()
  }

  async function handleSave(job: JobSearchResult) {
    setSavingId(job.external_id)
    try {
      const saved = await jobApi.save({
        external_id: job.external_id,
        source: job.source,
        title: job.title,
        company: job.company,
        description: job.description,
        location: job.location,
        salary_range: job.salary_range,
        job_type: job.job_type,
        remote: job.remote,
        source_url: job.source_url,
        posted_date: job.posted_date,
      })
      setResults((prev) => prev.map((r) => r.external_id === job.external_id ? { ...r, is_saved: true } : r))
      setSavedJobs((prev) => [saved, ...prev])
    } finally {
      setSavingId(null)
    }
  }

  async function handleUnsave(externalId: string) {
    setSavingId(externalId)
    try {
      await jobApi.unsave(externalId)
      setResults((prev) => prev.map((r) => r.external_id === externalId ? { ...r, is_saved: false } : r))
      setSavedJobs((prev) => prev.filter((j) => j.external_id !== externalId))
    } finally {
      setSavingId(null)
    }
  }

  const hasMatchScores = Object.keys(matchScores).length > 0

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Buscar Empleos</h1>
        <p className="text-gray-500 mt-1 text-sm">Resultados de Adzuna y JSearch (LinkedIn, Indeed, Glassdoor)</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {(['search', 'saved'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => handleTabChange(t)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t === 'search' ? 'Buscar' : `Guardados${savedJobs.length ? ` (${savedJobs.length})` : ''}`}
          </button>
        ))}
      </div>

      {tab === 'search' && (
        <div className="space-y-4">
          {/* Search form */}
          <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && doSearch(1)}
                  placeholder="Título, tecnología, empresa…"
                  className="w-full pl-9 pr-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <div className="relative w-48">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Ciudad (opcional)"
                  className="w-full pl-9 pr-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-1.5">
                <Globe className="w-4 h-4 text-gray-400" />
                <select
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="text-sm border border-gray-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                >
                  {COUNTRIES.map((c) => (
                    <option key={c.code} value={c.code}>{c.label}</option>
                  ))}
                </select>
              </div>

              <select
                value={source}
                onChange={(e) => setSource(e.target.value as typeof source)}
                className="text-sm border border-gray-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
              >
                <option value="all">Todas las fuentes</option>
                <option value="adzuna">Solo Adzuna</option>
                <option value="jsearch">Solo JSearch</option>
              </select>

              <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={remote === true}
                  onChange={(e) => setRemote(e.target.checked ? true : undefined)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                Solo remotos
              </label>

              <button
                onClick={() => doSearch(1)}
                disabled={loading || !query.trim()}
                className="ml-auto btn-primary py-2 px-5 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Buscando…' : 'Buscar'}
              </button>
            </div>
          </div>

          {/* AI Match banner */}
          {!loading && results.length > 0 && activeCvId && !hasMatchScores && (
            <div className="flex items-center justify-between gap-4 bg-gradient-to-r from-violet-50 to-indigo-50 border border-violet-200 rounded-xl px-4 py-3">
              <div>
                <p className="text-sm font-semibold text-gray-900">¿Cuánto encajan con tu perfil?</p>
                <p className="text-xs text-gray-500 mt-0.5">Claude analizará la compatibilidad de cada oferta con tu CV</p>
              </div>
              <button
                onClick={handleMatch}
                disabled={matching}
                className="shrink-0 inline-flex items-center gap-2 bg-violet-600 hover:bg-violet-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <Sparkles className="w-4 h-4" />
                {matching ? 'Analizando…' : 'Analizar compatibilidad'}
              </button>
            </div>
          )}

          {/* Match scores summary bar */}
          {hasMatchScores && (
            <div className="flex items-center justify-between text-sm text-gray-500 px-1">
              <span>
                Ordenado por compatibilidad
                {profileName && <> con <span className="font-medium text-gray-900">{profileName}</span></>}
              </span>
              <button
                onClick={() => { setMatchScores({}); setProfileName(null) }}
                className="text-xs text-gray-400 hover:text-gray-600 underline underline-offset-2"
              >
                Limpiar
              </button>
            </div>
          )}

          {/* Matching loading skeleton overlay */}
          {matching && (
            <div className="grid gap-4 sm:grid-cols-2">
              {results.map((_, i) => (
                <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse space-y-3">
                  <div className="flex gap-3">
                    <div className="w-14 h-14 bg-gray-200 rounded-xl shrink-0" />
                    <div className="flex-1 space-y-2 pt-1">
                      <div className="h-4 bg-gray-200 rounded w-3/4" />
                      <div className="h-3 bg-gray-200 rounded w-1/2" />
                    </div>
                  </div>
                  <div className="h-3 bg-gray-200 rounded w-full" />
                  <div className="h-3 bg-gray-200 rounded w-5/6" />
                </div>
              ))}
            </div>
          )}

          {/* Regular search loading */}
          {loading && (
            <div className="grid gap-4 sm:grid-cols-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse space-y-3">
                  <div className="h-4 bg-gray-200 rounded w-3/4" />
                  <div className="h-3 bg-gray-200 rounded w-1/2" />
                  <div className="h-3 bg-gray-200 rounded w-full" />
                  <div className="h-3 bg-gray-200 rounded w-5/6" />
                </div>
              ))}
            </div>
          )}

          {!loading && searched && results.length === 0 && (
            <div className="text-center py-16 text-gray-500">
              <Search className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="font-medium">Sin resultados</p>
              <p className="text-sm mt-1">Prueba con otros términos o cambia el país</p>
            </div>
          )}

          {!loading && !matching && results.length > 0 && (
            <>
              <div className="grid gap-4 sm:grid-cols-2">
                {sortedResults.map((job) => (
                  <JobCard
                    key={`${job.source}-${job.external_id}`}
                    job={job}
                    onSave={handleSave}
                    onUnsave={handleUnsave}
                    saving={savingId === job.external_id}
                    matchScore={matchScores[job.external_id]}
                  />
                ))}
              </div>

              <div className="flex justify-center gap-2 pt-2">
                <button
                  onClick={() => doSearch(page - 1)}
                  disabled={page === 1 || loading}
                  className="btn-outline py-1.5 px-4 text-sm disabled:opacity-40"
                >
                  Anterior
                </button>
                <span className="px-3 py-1.5 text-sm text-gray-600">Página {page}</span>
                <button
                  onClick={() => doSearch(page + 1)}
                  disabled={results.length < 10 || loading}
                  className="btn-outline py-1.5 px-4 text-sm disabled:opacity-40"
                >
                  Siguiente
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {tab === 'saved' && (
        <div className="space-y-4">
          {loading && (
            <div className="grid gap-4 sm:grid-cols-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse space-y-3">
                  <div className="h-4 bg-gray-200 rounded w-3/4" />
                  <div className="h-3 bg-gray-200 rounded w-1/2" />
                  <div className="h-3 bg-gray-200 rounded w-full" />
                </div>
              ))}
            </div>
          )}

          {!loading && savedJobs.length === 0 && (
            <div className="text-center py-16 text-gray-500">
              <Bookmark className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="font-medium">No tienes empleos guardados</p>
              <p className="text-sm mt-1">Guarda ofertas desde la búsqueda para revisarlas después</p>
            </div>
          )}

          {!loading && savedJobs.length > 0 && (
            <div className="grid gap-4 sm:grid-cols-2">
              {savedJobs.map((job) => (
                <JobCard
                  key={job.id}
                  job={job}
                  onUnsave={handleUnsave}
                  saving={savingId === job.external_id}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
