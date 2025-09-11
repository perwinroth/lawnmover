"use client";
import { useEffect, useMemo, useState } from 'react'

type EventItem = { name: string; date?: string; location?: string; description?: string; registrationUrl?: string }

export default function EventsPage() {
  const [events, setEvents] = useState<EventItem[]>([])
  const [month, setMonth] = useState<string>('')
  const [region, setRegion] = useState<string>('')

  useEffect(()=>{
    fetch('/api/data?kind=events').then(r=>r.json()).then((items: EventItem[])=>{
      setEvents((items||[]).sort((a,b)=> (a.date||'').localeCompare(b.date||'')))
    })
  },[])

  const filtered = useMemo(()=>{
    return events.filter(ev => {
      const okMonth = !month || (ev.date||'').slice(0,7) === month
      const okRegion = !region || (ev.location||'').toLowerCase().includes(region.toLowerCase())
      return okMonth && okRegion
    })
  }, [events, month, region])

  const jsonLd = {
    '@context':'https://schema.org', '@type':'ItemList',
    itemListElement: filtered.map(ev => ({
      '@type':'Event', name: ev.name, startDate: ev.date, description: ev.description, url: ev.registrationUrl,
      location: { '@type':'Place', name: ev.location, address: ev.location }
    }))
  }

  // Month options from events
  const months = Array.from(new Set(events.map(e => (e.date||'').slice(0,7)).filter(Boolean))).sort()

  return (
    <div className="container">
      <head>
        <title>Friluft – Evenemang</title>
        <meta name="description" content="Kalender med lopp och evenemang inom friluftsliv i Sverige." />
        <link rel="canonical" href="https://perwinroth.github.io/friluft/events" />
        <script type="application/ld+json" dangerouslySetInnerHTML={{__html: JSON.stringify(jsonLd)}} />
      </head>
      <h1>Evenemang</h1>
      <div className="card" style={{display:'flex', gap:12, alignItems:'center', flexWrap:'wrap'}}>
        <label> Månad
          <select value={month} onChange={e=>setMonth(e.target.value)} style={{marginLeft:8}}>
            <option value="">Alla</option>
            {months.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </label>
        <label> Region/Plats
          <input type="text" placeholder="t.ex. Stockholm" value={region} onChange={e=>setRegion(e.target.value)} style={{marginLeft:8}} />
        </label>
      </div>
      <div className="card">
        <ul style={{listStyle:'none', padding:0}}>
          {filtered.map((ev, i)=> (
            <li key={i} style={{border:'1px solid #eee', borderRadius:10, padding:12, marginBottom:8}}>
              <strong>{ev.name}</strong><br/>
              <small>{ev.date} – {ev.location}</small><br/>
              {ev.registrationUrl ? <a className="btn" href={ev.registrationUrl} target="_blank" rel="noopener">Anmälan</a> : null}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
