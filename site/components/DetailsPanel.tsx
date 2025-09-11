"use client";
import { useEffect, useState } from 'react'

type Props = {}

export default function DetailsPanel(_: Props) {
  const [item, setItem] = useState<any | null>(null)
  const [coords, setCoords] = useState<{lat:number, lon:number} | null>(null)

  useEffect(()=>{
    const handler = (e: any) => {
      const d = e.detail || {}; setItem(d.props || null); setCoords({lat:d.lat, lon:d.lon})
    }
    window.addEventListener('lawnmover:select', handler as any)
    return () => window.removeEventListener('lawnmover:select', handler as any)
  },[])

  if (!item) return (
    <div className="card" style={{marginBottom:12}}>
      <strong>Detaljer</strong>
      <div style={{color:'#64748b', fontSize:12}}>Klicka på en punkt i kartan för info.</div>
    </div>
  )

  const cats: string[] = item.categories || []
  const link = item.link || item.osm_url
  return (
    <div className="card" style={{marginBottom:12}}>
      <div style={{display:'flex', alignItems:'center', justifyContent:'space-between'}}>
        <div>
          <div style={{fontWeight:700, marginBottom:4}}>{item.name}</div>
          <div style={{color:'#64748b', fontSize:12}}>{cats.join(', ')}</div>
        </div>
        <div style={{display:'flex', gap:6}}>
          {typeof item.open_now === 'boolean' && (
            <span className="badge" style={{background:item.open_now?'#0f766e':'#b45309', color:'#fff'}}>
              {item.open_now? 'Öppet' : 'Stängt'}
            </span>
          )}
          {typeof item.link_ok === 'boolean' && (
            <span className="badge" style={{background:item.link_ok?'#0f766e':'#b00020', color:'#fff'}}>
              {item.link_ok? 'Länk OK' : 'Länk fel'}
            </span>
          )}
        </div>
      </div>
      {coords && (
        <div style={{color:'#64748b', fontSize:12, marginTop:6}}>
          Koordinater: {coords.lat.toFixed(5)}, {coords.lon.toFixed(5)}
        </div>
      )}
      <div style={{marginTop:8, display:'flex', gap:8}}>
        {link && <a className="btn" href={link} target="_blank" rel="noopener">Besök webbplats</a>}
      </div>
    </div>
  )
}
