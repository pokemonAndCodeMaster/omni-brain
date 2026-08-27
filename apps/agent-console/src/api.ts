export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(payload.detail || `请求失败：${response.status}`)
  }
  return response.json() as Promise<T>
}

export function post<T>(path: string, body: unknown = {}): Promise<T> {
  return api<T>(path, { method: 'POST', body: JSON.stringify(body) })
}
