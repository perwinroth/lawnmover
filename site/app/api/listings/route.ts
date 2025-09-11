import { NextResponse } from 'next/server'
import { loadPlaces } from '../../../lib/data'

// For MVP, expose read-only listings backed by ETL places.
export async function GET() {
  const places = await loadPlaces();
  return NextResponse.json({ items: places.slice(0, 500) })
}

export async function POST() {
  // Placeholder for provider-created listings (would require auth & DB)
  return new NextResponse('Not Implemented', { status: 501 })
}

