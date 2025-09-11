import { NextResponse } from 'next/server'
import { sql } from '../../../../lib/db'

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const secret = process.env.SEED_SECRET || ''
  if (!secret || searchParams.get('secret') !== secret) {
    return NextResponse.json({ ok: false, error: 'forbidden' }, { status: 403 })
  }
  // Create table if not exists
  await sql`
    CREATE TABLE IF NOT EXISTS sellers (
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
  `
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
      await sql`
        INSERT INTO sellers (id, name, website, address, city, postcode, street, housenumber, lat, lon)
        VALUES (${id}, ${name}, ${website}, ${address}, ${addr.city||null}, ${addr.postcode||null}, ${addr.street||null}, ${addr.housenumber||null}, ${lat}, ${lon})
        ON CONFLICT (id) DO UPDATE SET
          name = EXCLUDED.name,
          website = EXCLUDED.website,
          address = EXCLUDED.address,
          city = EXCLUDED.city,
          postcode = EXCLUDED.postcode,
          street = EXCLUDED.street,
          housenumber = EXCLUDED.housenumber,
          lat = EXCLUDED.lat,
          lon = EXCLUDED.lon
      `
      inserted++
    } catch (e) {
      // skip bad rows
    }
  }
  return NextResponse.json({ ok: true, inserted })
}

