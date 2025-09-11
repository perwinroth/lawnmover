import { NextResponse } from 'next/server'
import { prisma } from '../../../../lib/prisma'

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const secret = process.env.SEED_SECRET || ''
  if (!secret || searchParams.get('secret') !== secret) {
    return NextResponse.json({ ok: false, error: 'forbidden' }, { status: 403 })
  }
  // Ensure table exists (raw SQL for first-time setup)
  try {
    await prisma.$executeRawUnsafe(`
      CREATE TABLE IF NOT EXISTS "Seller" (
        id text PRIMARY KEY,
        name text NOT NULL,
        website text,
        address text,
        city text,
        postcode text,
        street text,
        housenumber text,
        lat double precision,
        lon double precision
      )
    `)
  } catch (_) {}
  // Fetch data from GitHub raw
  const url = 'https://raw.githubusercontent.com/perwinroth/lawnmover/main/data/lawnmover.geojson'
  const res = await fetch(url, { cache: 'no-store' })
  if (!res.ok) return NextResponse.json({ ok:false, error: 'fetch_failed' }, { status: 502 })
  const geo = await res.json()
  const features = Array.isArray(geo?.features) ? geo.features : []
  let inserted = 0
  for (const f of features) {
    const p = f?.properties || {}
    const g = f?.geometry || {}
    const coords = Array.isArray(g.coordinates) ? g.coordinates : [null, null]
    const id = String(p.id || '')
    if (!id) continue
    const name = String(p.name || '')
    const website = p.link || p.osm_url || null
    const address = p.address || null
    const addr = p.addr || {}
    const lat = coords[1] != null ? Number(coords[1]) : null
    const lon = coords[0] != null ? Number(coords[0]) : null
    try {
      await prisma.seller.upsert({
        where: { id },
        update: { name, website, address, city: addr.city||null, postcode: addr.postcode||null, street: addr.street||null, housenumber: addr.housenumber||null, lat, lon },
        create: { id, name, website: website||null, address, city: addr.city||null, postcode: addr.postcode||null, street: addr.street||null, housenumber: addr.housenumber||null, lat, lon },
      })
      inserted++
    } catch (e) { /* skip */ }
  }
  return NextResponse.json({ ok: true, inserted })
}
