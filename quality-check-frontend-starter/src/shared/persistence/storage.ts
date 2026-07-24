export interface PersistedEnvelope<T> {
  schemaVersion: number
  savedAt: string
  data: T
}

export function loadPersisted<T>(key: string, schemaVersion: number, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(key)
    if (!raw) return fallback

    const envelope = JSON.parse(raw) as PersistedEnvelope<T>
    if (envelope.schemaVersion !== schemaVersion) return fallback
    return envelope.data
  } catch (error) {
    console.warn(`读取本地配置失败：${key}`, error)
    return fallback
  }
}

export function savePersisted<T>(key: string, schemaVersion: number, data: T): void {
  const envelope: PersistedEnvelope<T> = {
    schemaVersion,
    savedAt: new Date().toISOString(),
    data,
  }
  window.localStorage.setItem(key, JSON.stringify(envelope))
}
