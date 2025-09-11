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

export async function loadPlaces(): Promise<Place[]> {
  const file = path.join(process.cwd(), '..', 'data', 'places.json')
  try {
    const buf = await fs.readFile(file, 'utf-8')
    return JSON.parse(buf)
  } catch {
    const gj = path.join(process.cwd(), '..', 'data', 'lawnmover.geojson')
    const buf = await fs.readFile(gj, 'utf-8')
    const geo = JSON.parse(buf)
    return (geo.features||[]).map((f:any, i:number)=> ({
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
}

export function slugify(s: string): string {
  return String(s || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '') || 'plats';
}
