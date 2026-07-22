export type DocSummary = {
  number: string
  title: string
  version: string
  category: string
  path: string
  owner: string
  approved: string
}

export type Section = {
  heading: string
  body: string
  type?: string
  rows?: string[][]
  src?: string
  alt?: string
}
export type Revision = {
  version: string
  date: string
  author: string
  notes: string
}

export type DocumentDetail = {
  path: string
  number: string
  title: string
  version: string
  category: string
  owner: string
  approved: string
  purpose: string
  scope: string
  sections: number
  section_headings: string[]
  revision_history: Revision[]
  raw: {
    number: string
    title: string
    version: string
    category: string
    owner: string
    approved: string
    purpose: string
    scope: string
    sections: Section[]
    revision_history: Revision[]
  }
}

export type StatusPayload = {
  template: string | null
  template_error: string | null
  documents: DocSummary[]
  document_count: number
  pdf_backends: string[]
  categories: string[]
  all_categories?: string[]
  category_ranges?: Record<string, { from: string; to: string }>
  layout_frozen?: boolean
  section_types?: string[]
  standard_section_order?: string[]
  root: string
}

export type GovernancePayload = {
  layout_frozen: boolean
  primary_categories: string[]
  category_ranges: Record<string, { from: string; to: string }>
  standard_section_order: string[]
  section_types: string[]
  metadata_fields: string[]
}

export type ClauseItem = {
  id: string
  title: string
  path: string
  body: string
}

export type PortalDocument = {
  number: string
  title: string
  version: string
  category: string
  owner: string
  approved: string
  purpose: string
  scope: string
  sections: Section[]
  revision_history: Revision[]
  path: string
  summary: {
    headline: string
    bullets: string[]
    section_count: number
    topics: string[]
  }
}

export type ManualPayload = {
  title: string
  document_count: number
  categories: string[]
  documents: PortalDocument[]
}

export type SearchResult = {
  number: string
  title: string
  category: string
  approved: string
  version: string
  snippet: string
  matches: { field: string; excerpt: string }[]
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? JSON.stringify(body)
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return res.json() as Promise<T>
}

export const api = {
  status: () => request<StatusPayload>('/api/status'),
  list: (category?: string) =>
    request<{ documents: DocSummary[]; count: number }>(
      category ? `/api/documents?category=${encodeURIComponent(category)}` : '/api/documents',
    ),
  get: (number: string) => request<DocumentDetail>(`/api/documents/${number}`),
  create: (body: Record<string, unknown>) =>
    request<{ path: string; document: DocumentDetail }>('/api/documents', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  save: (number: string, body: Record<string, unknown>) =>
    request<DocumentDetail>(`/api/documents/${number}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),
  meta: (number: string, body: Record<string, unknown>) =>
    request<DocumentDetail>(`/api/documents/${number}/meta`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  generate: (number: string, make_pdf = false) =>
    request<{
      number: string
      docx: string | null
      pdf: string | null
      pdf_note: string | null
      download_docx: string
      download_pdf: string | null
    }>(`/api/documents/${number}/generate`, {
      method: 'POST',
      body: JSON.stringify({ make_pdf }),
    }),
  rebuild: (make_pdf = false) =>
    request<{ count: number; results: unknown[] }>('/api/rebuild', {
      method: 'POST',
      body: JSON.stringify({ make_pdf }),
    }),
  validate: () =>
    request<{
      ok: boolean
      count: number
      documents: {
        number: string
        ok: boolean
        errors: string[]
        warnings?: string[]
      }[]
    }>('/api/validate'),
  governance: () => request<GovernancePayload>('/api/governance'),
  nextNumber: (category: string) =>
    request<{ category: string; number: string }>(
      `/api/numbers/next?category=${encodeURIComponent(category)}`,
    ),
  clauses: () => request<{ count: number; clauses: ClauseItem[] }>('/api/clauses'),
  prompt: (number: string, body: Record<string, unknown>) =>
    request<{ prompt: string }>(`/api/prompt/${number}`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  manual: (category?: string) =>
    request<ManualPayload>(
      category ? `/api/manual?category=${encodeURIComponent(category)}` : '/api/manual',
    ),
  search: (q: string, category?: string) => {
    const params = new URLSearchParams()
    params.set('q', q)
    if (category) params.set('category', category)
    return request<{ query: string; count: number; results: SearchResult[] }>(
      `/api/search?${params.toString()}`,
    )
  },
  portal: (number: string) => request<PortalDocument>(`/api/portal/${number}`),
  summary: (number: string) =>
    request<{ number: string; title: string; summary: PortalDocument['summary'] }>(
      `/api/documents/${number}/summary`,
    ),
  files: (number: string) =>
    request<{
      number: string
      docx: boolean
      pdf: boolean
      download_docx: string | null
      download_pdf: string | null
    }>(`/api/files/${number}/available`),
  templateStatus: () => request<TemplateStatus>('/api/template'),
  uploadTemplate: async (file: File) => {
    const body = new FormData()
    body.append('file', file)
    const res = await fetch('/api/template/upload', { method: 'POST', body })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail))
    }
    return res.json() as Promise<TemplateStatus>
  },
  uploadLogo: async (file: File) => {
    const body = new FormData()
    body.append('file', file)
    const res = await fetch('/api/template/logo', { method: 'POST', body })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail))
    }
    return res.json() as Promise<TemplateStatus>
  },
  applyLogo: () =>
    request<TemplateStatus>('/api/template/apply-logo', { method: 'POST', body: '{}' }),
  rebuildStarterTemplate: () =>
    request<TemplateStatus>('/api/template/rebuild-starter', {
      method: 'POST',
      body: '{}',
    }),
}

export type TemplateStatus = {
  active: string | null
  active_error: string | null
  docx: string
  docx_exists: boolean
  dotx: string
  dotx_exists: boolean
  logo: string | null
  logo_exists: boolean
  logo_url: string | null
  download_docx: string
  download_dotx: string
  required_placeholders: string[]
  validation: {
    ok: boolean
    missing: string[]
    is_dotx?: boolean
    path?: string
    error?: string
  } | null
}
