import { NextResponse } from 'next/server'
import fs from 'node:fs/promises'
import path from 'node:path'

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const kind = searchParams.get('kind') || 'geojson'
  const base = path.join(process.cwd(), '..', 'data')
  const file = kind === 'places' ? 'places.json' : kind === 'events' ? 'events.json' : 'lawnmover.geojson'
  // 1) Try local filesystem (works in dev; not in Vercel runtime)
  try {
    const buf = await fs.readFile(path.join(base, file), 'utf-8')
    return new NextResponse(buf, { headers: { 'content-type': 'application/json; charset=utf-8' } })
  } catch {}
  // 2) Fallback to GitHub raw (decouples data from deployment)
  try {
    const url = `https://raw.githubusercontent.com/perwinroth/lawnmover/main/data/${file}`
    const res = await fetch(url, { next: { revalidate: 300 } })
    if (!res.ok) throw new Error('fetch_failed')
    const text = await res.text()
    return new NextResponse(text, { headers: { 'content-type': 'application/json; charset=utf-8' } })
  } catch (e) {
    return NextResponse.json({ error: 'not_found' }, { status: 404 })
  }
}
