"use client";
import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'

type Props = { query?: string; cats?: string[] }

export default function ResultsList({ query = '', cats = [] }: Props) {
  const [items, setItems] = useState<any[]>([])
  useEffect(()=>{
    fetch('/api/data?kind=geojson').then(r=>r.json()).then(geo=>{
      setItems((geo.features||[]).map((f:any)=> ({
        id: f.properties?.id,
        name: f.properties?.name,
        link: f.properties?.link || f.properties?.osm_url,
        cats: f.properties?.categories || [],
        bookable: !!f.properties?.bookable,
        open_now: f.properties?.open_now,
        link_ok: f.properties?.link_ok,
        lat: f.geometry?.coordinates?.[1],
        lon: f.geometry?.coordinates?.[0]
      })))
    })
  },[])

  const filtered = useMemo(()=>{
    const q = query.trim().toLowerCase()
    return items.filter(it =>
      (!cats.length || it.cats.some((c:string)=> cats.includes(c))) &&
      (!q || String(it.name||'').toLowerCase().includes(q))
    ).slice(0, 50)
  }, [items, query, cats.join(',')])

  return (
    <div>
      <div style={{color:'#64748b', margin:'8px 0'}}>{filtered.length} träffar</div>
      <ul style={{listStyle:'none', padding:0, margin:0}}>
        {filtered.map(it => (
          <li key={it.id} className="card" style={{marginBottom:8}}>
            <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', gap:8}}>
              <div style={{fontWeight:600, display:'flex', alignItems:'center', gap:8}}>
                {iconFor(it.cats?.[0])}
                <Link href={`/l/${slugify(it.id)}`}>{it.name}</Link>
              </div>
              {it.bookable ? <span className="badge" style={{background:'#0f766e', color:'#fff'}}>Boka</span> : null}
            </div>
            <div style={{color:'#64748b', fontSize:12, margin:'6px 0'}}>
              {(it.cats||[]).map((c:string)=> (
                <span key={c} className="badge" style={{marginRight:6, background:'#eef2ff', color:'#3730a3', display:'inline-flex', alignItems:'center', gap:6}}>
                  {iconFor(c, 12)} {c}
                </span>
              ))}
            </div>
            <div style={{display:'flex', gap:10, alignItems:'center', flexWrap:'wrap'}}>
              {it.link ? <a className="btn" href={it.link} target="_blank" rel="noopener">{it.bookable ? 'Boka' : 'Länk'}</a> : null}
              <Link className="btn" href={`/l/${slugify(it.id)}`} style={{background:'#1f2937'}}>Detaljer</Link>
              <button className="btn" style={{background:'#334155'}} onClick={()=>focusOnMap(it.lat, it.lon)}>Visa på karta</button>
              {typeof it.open_now === 'boolean' && (
                <span className="badge" style={{background:it.open_now?'#0f766e':'#b45309', color:'#fff'}}>{it.open_now?'Öppet':'Stängt'}</span>
              )}
              {typeof it.link_ok === 'boolean' && (
                <span className="badge" style={{background:it.link_ok?'#0f766e':'#b00020', color:'#fff'}}>{it.link_ok?'Länk OK':'Länk fel'}</span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

function slugify(s: string) {
  return String(s || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '') || 'plats';
}

function iconFor(cat?: string, size = 16) {
  if (!cat) return null;
  const map: Record<string, string> = {
    hiking: '/icons/hiking.svg',
    canoe_kayak: '/icons/canoe_kayak.svg',
    camp_site: '/icons/camp_site.svg',
    shelter: '/icons/shelter.svg',
    viewpoint: '/icons/viewpoint.svg',
    picnic_site: '/icons/picnic_site.svg',
    slipway: '/icons/slipway.svg',
    boat_rental: '/icons/boat_rental.svg',
    national_park: '/icons/hiking.svg',
    nature_reserve: '/icons/hiking.svg',
  };
  const src = map[cat] || map.hiking;
  return <img src={src} alt="" width={size} height={size} style={{display:'inline-block'}} />
}

function focusOnMap(lat?: number, lon?: number) {
  if (lat == null || lon == null) return;
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('friluft:focus', { detail: { lat, lon, zoom: 13 } }))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}
