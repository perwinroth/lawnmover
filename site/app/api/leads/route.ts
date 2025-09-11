import { NextResponse } from 'next/server'
import fs from 'node:fs/promises'
import path from 'node:path'

export async function POST(req: Request) {
  const body = await req.json().catch(()=>({}));
  // In production, send email and store in DB. For now, append to data/leads.json if possible.
  try {
    const file = path.join(process.cwd(), '..', 'data', 'leads.json')
    let list: any[] = []
    try { list = JSON.parse(await fs.readFile(file, 'utf-8')) } catch {}
    list.push({ ...body, createdAt: new Date().toISOString() })
    await fs.writeFile(file, JSON.stringify(list, null, 2), 'utf-8')
  } catch (e) {
    console.log('Lead (not persisted):', body)
  }
  return NextResponse.json({ ok: true })
}
