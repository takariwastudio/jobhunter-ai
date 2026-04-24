import { useState, useCallback } from 'react'
import { Search, MapPin, Bookmark, BookmarkCheck, ExternalLink, Briefcase, Globe, Wifi } from 'lucide-react'
import { jobApi } from '../services/api'
import type { JobSearchResult, SavedJob, JobSearchParams } from '../types'

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

type Tab = 'search' | 'saved'

function JobCard({
  job,
  onSave,
  onUnsave,
  saving,
}: {
  job: JobSearchResult | SavedJob
  onSave?: (job: JobSearchResult) => void
  onUnsave?: (externalId: string) => void
  saving?: boolean
}) {
  const isSearchResult = (job as JobSearchResult).is_saved !== undefined
  const isSaved = isSearchResult ? (job as JobSearchResult).is_saved : true
  const externalId = job.external_id

  function handleToggle() {
    if (isSaved) {
      onUnsave?.(externalId)
    } else if (isSearchResult) {
      onSave?.(job as JobSearchResult)
    }
  }

  const sourceUrl = job.source_url

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
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

  const doSearch = useCallback(async (p = 1) => {
    if (!query.trim()) return
    setLoading(true)
    setPage(p)
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

          {/* Results */}
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

          {!loading && results.length > 0 && (
            <>
              <div className="grid gap-4 sm:grid-cols-2">
                {results.map((job) => (
                  <JobCard
                    key={`${job.source}-${job.external_id}`}
                    job={job}
                    onSave={handleSave}
                    onUnsave={handleUnsave}
                    saving={savingId === job.external_id}
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
