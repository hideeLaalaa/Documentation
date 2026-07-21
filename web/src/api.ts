export type DocSummary = {
  number: string
  title: string
  version: string
  category: string
  path: string
  owner: string
  approved: string
}

export type Section = { heading: string; body: string }
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
  root: string
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
    request<{ ok: boolean; count: number; documents: { number: string; ok: boolean; errors: string[] }[] }>(
      '/api/validate',
    ),
  prompt: (number: string, body: Record<string, unknown>) =>
    request<{ prompt: string }>(`/api/prompt/${number}`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}
