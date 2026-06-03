const BASE = '/api'

export async function uploadExcel(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/batches/upload`, { method: 'POST', body: form })
  if (!res.ok) throw new Error((await res.json()).detail)
  return res.json()
}

export async function startAnalyze(batchId) {
  const res = await fetch(`${BASE}/batches/${batchId}/analyze`, { method: 'POST' })
  if (!res.ok) throw new Error((await res.json()).detail)
  return res.json()
}

export async function getBatches() {
  const res = await fetch(`${BASE}/batches`)
  return res.json()
}

export async function getBatch(batchId) {
  const res = await fetch(`${BASE}/batches/${batchId}`)
  return res.json()
}

export function downloadUrl(batchId) {
  return `${BASE}/batches/${batchId}/download`
}

export async function getDepartments() {
  const res = await fetch(`${BASE}/departments`)
  return res.json()
}

export async function createDepartment(data) {
  const res = await fetch(`${BASE}/departments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error((await res.json()).detail)
  return res.json()
}

export async function updateDepartment(id, data) {
  const res = await fetch(`${BASE}/departments/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error((await res.json()).detail)
  return res.json()
}

export async function deleteDepartment(id) {
  await fetch(`${BASE}/departments/${id}`, { method: 'DELETE' })
}

export async function getDocs() {
  const res = await fetch(`${BASE}/docs`)
  return res.json()
}

export async function uploadDoc(title, file, url) {
  const form = new FormData()
  form.append('title', title)
  if (file) form.append('file', file)
  if (url) form.append('url', url)
  const res = await fetch(`${BASE}/docs`, { method: 'POST', body: form })
  if (!res.ok) throw new Error((await res.json()).detail)
  return res.json()
}

export async function deleteDoc(id) {
  await fetch(`${BASE}/docs/${id}`, { method: 'DELETE' })
}
