import { NextResponse } from 'next/server'
import { prisma } from '../../../lib/prisma'

function toCSV(rows: any[]): string {
  const header = ['id','name','website','address','street','housenumber','postcode','city','lat','lon']
  const esc = (v: any) => {
    const s = (v == null ? '' : String(v))
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s
  }
  const lines = [header.join(',')]
  for (const r of rows) {
    lines.push([
      esc(r.id), esc(r.name), esc(r.website), esc(r.address), esc(r.street), esc(r.housenumber), esc(r.postcode), esc(r.city), esc(r.lat), esc(r.lon)
    ].join(','))
  }
  return lines.join('\n') + '\n'
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const format = (searchParams.get('format') || 'json').toLowerCase()

  // Try DB first
  try {
    const rows = await prisma.seller.findMany({ take: 20000 })
    if (format === 'csv') {
      return new NextResponse(toCSV(rows), { headers: { 'content-type': 'text/csv; charset=utf-8' } })
    }
    return NextResponse.json({ ok: true, rows })
  } catch (e) {
    // Fallback to GitHub raw
    try {
      const url = 'https://raw.githubusercontent.com/perwinroth/lawnmover/main/data/lawnmover.geojson'
      const res = await fetch(url, { cache: 'no-store' })
      if (!res.ok) throw new Error('fetch_failed')
      const geo = await res.json()
      const rows = (geo?.features || []).map((f: any) => {
        const p = f?.properties || {}
        const g = f?.geometry || {}
        const c = Array.isArray(g.coordinates) ? g.coordinates : [null, null]
        const a = p.addr || {}
        return {
          id: p.id,
          name: p.name,
          website: p.link || p.osm_url,
          address: p.address,
          street: a.street,
          housenumber: a.housenumber,
          postcode: a.postcode,
          city: a.city,
          lat: c[1],
          lon: c[0],
        }
      })
      if (format === 'csv') {
        return new NextResponse(toCSV(rows), { headers: { 'content-type': 'text/csv; charset=utf-8' } })
      }
      return NextResponse.json({ ok: true, rows })
    } catch (e2) {
      return NextResponse.json({ ok: false, error: 'not_found' }, { status: 404 })
    }
  }
}
