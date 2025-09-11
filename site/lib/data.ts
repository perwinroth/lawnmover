import fs from 'node:fs/promises'
import path from 'node:path'

export type Place = {
  id?: string
  name: string
  categories?: string[]
  lat?: number
  lon?: number
  website?: string
  description?: string
  open_now?: boolean
  link_ok?: boolean
}

function fromGeoJSON(geo: any): Place[] {
  return (geo.features || []).map((f: any, i: number) => ({
    id: f.properties?.id || `feature/${i}`,
    name: f.properties?.name || '(namnlös)',
    categories: f.properties?.categories || [],
    lat: f.geometry?.coordinates?.[1],
    lon: f.geometry?.coordinates?.[0],
    website: f.properties?.link,
    open_now: f.properties?.open_now,
    link_ok: f.properties?.link_ok,
  }))
}

export async function loadPlaces(): Promise<Place[]> {
  const publicDir = path.join(process.cwd(), 'public', 'data')
  const repoDataDir = path.join(process.cwd(), '..', 'data')
  const candidates = [
    { file: path.join(publicDir, 'places.json'), type: 'json' as const },
    { file: path.join(publicDir, 'lawnmover.geojson'), type: 'geojson' as const },
    { file: path.join(repoDataDir, 'places.json'), type: 'json' as const },
    { file: path.join(repoDataDir, 'lawnmover.geojson'), type: 'geojson' as const },
  ]
  for (const c of candidates) {
    try {
      const buf = await fs.readFile(c.file, 'utf-8')
      const data = JSON.parse(buf)
      if (c.type === 'geojson') return fromGeoJSON(data)
      if (Array.isArray(data)) return data as Place[]
      return (data?.places as Place[]) || []
    } catch {
      // try next candidate
    }
  }
  return []
}

export function slugify(s: string): string {
  return String(s || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '') || 'plats';
}
