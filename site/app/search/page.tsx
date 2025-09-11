"use client";
import dynamic from 'next/dynamic';
import { useEffect, useMemo, useState } from 'react';
import ResultsList from '../../components/ResultsList'
import DetailsPanel from '../../components/DetailsPanel'

const LeafletMap = dynamic(()=> import('../../components/Map'), { ssr: false });

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [cats, setCats] = useState<Record<string, boolean>>({
    robot_mower_seller: true,
  });
  const [show, setShow] = useState<'map'|'list'|'both'>('list');

  const activeCats = useMemo(()=> Object.keys(cats).filter(k=>cats[k]), [cats]);

  useEffect(()=>{
    const params = new URLSearchParams(window.location.search);
    const q = params.get('q');
    if (q) setQuery(q);
    const onResize = () => {
      if (window.innerWidth >= 1024) setShow('both'); else setShow('list');
    };
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  },[]);

  return (
    <div className="container">
      <head>
        <link rel="canonical" href="/search" />
      </head>
      <div className="pill" style={{position:'sticky', top:8, zIndex:10}}>
        <span>🔍</span>
        <input value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="Sök plats eller aktivitet" />
      </div>
      <div className="chips" style={{margin:'8px 0 12px'}}>
        {Object.keys(cats).map(k=> (
          <button key={k} className="chip" onClick={()=> setCats(s=>({...s,[k]:!s[k]}))} style={{background: cats[k]?'#fff':'#f5f5f5'}}>
            {k === 'robot_mower_seller' ? 'robotgräsklippare' : k}
          </button>
        ))}
      </div>
      <div className="grid">
        <div className="card" style={{minHeight:'60vh', display: show==='list' ? 'none' : 'block'}}>
          <LeafletMap query={query} cats={activeCats} height="56vh" />
        </div>
        <div style={{display: show==='map' ? 'none' : 'block'}}>
          <DetailsPanel />
          <div className="card">
            <ResultsList query={query} cats={activeCats} />
          </div>
        </div>
      </div>
      <div className="card" style={{position:'sticky', bottom:12, display: 'flex', justifyContent:'center'}}>
        <div style={{display:'flex', gap:8}}>
          <button className="btn" style={{background: show==='list'?'#0f766e':'#334155'}} onClick={()=>setShow('list')}>Lista</button>
          <button className="btn" style={{background: show==='map'?'#0f766e':'#334155'}} onClick={()=>setShow('map')}>Karta</button>
        </div>
      </div>
    </div>
  )
}
