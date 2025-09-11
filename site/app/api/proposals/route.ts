import { NextResponse } from 'next/server'
import fs from 'node:fs/promises'
import path from 'node:path'

export async function POST(req: Request) {
  const body = await req.json().catch(()=>({}))
  const title = String(body.title||'').trim()
  const website = String(body.website||'').trim()
  const priceFrom = body.price_from ? parseInt(body.price_from, 10) : null
  const categories = String(body.categories||'').trim()
  const description = String(body.description||'').trim()

  if (!title || !website) {
    return NextResponse.json({ ok:false, error:'missing_fields' }, { status: 400 })
  }

  // Persist to JSON file (no DB in Vercel build)
  try {
    const dir = path.join(process.cwd(), '..', 'data')
    const file = path.join(dir, 'proposals.json')
    try { await fs.mkdir(dir, { recursive: true }) } catch {}
    let list: any[] = []
    try { list = JSON.parse(await fs.readFile(file, 'utf-8')) } catch {}
    const rec = { id: Date.now().toString(36), createdAt: new Date().toISOString(), title, website, priceFrom, categories, description }
    list.push(rec)
    await fs.writeFile(file, JSON.stringify(list, null, 2), 'utf-8')
    return NextResponse.json({ ok:true, id: rec.id, mode:'file' })
  } catch (e2) {
    return NextResponse.json({ ok:false, error:'persist_failed' }, { status: 500 })
  }
}
