import { NextResponse } from 'next/server'
import fs from 'node:fs/promises'
import path from 'node:path'

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const kind = searchParams.get('kind') || 'geojson'
  const base = path.join(process.cwd(), '..', 'data')
  const file = kind === 'places' ? 'places.json' : kind === 'events' ? 'events.json' : 'friluft.geojson'
  try {
    const buf = await fs.readFile(path.join(base, file), 'utf-8')
    return new NextResponse(buf, { headers: { 'content-type': 'application/json; charset=utf-8' } })
  } catch (e) {
    return NextResponse.json({ error: 'not_found' }, { status: 404 })
  }
}

