import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="container">
      <head>
        <link rel="canonical" href="https://perwinroth.github.io/friluft/web/" />
      </head>
      <h1>Friluft</h1>
      <p>Upptäck och boka friluftsupplevelser i Sverige.</p>
      <div className="card" style={{marginTop:12}}>
        <div className="pill">
          <span>🔍</span>
          <input type="text" placeholder="Sök plats eller aktivitet" onKeyDown={(e)=>{
            const input = e.currentTarget as HTMLInputElement;
            if (e.key==='Enter') {
              window.location.href = '/search?q=' + encodeURIComponent(input.value);
            }
          }} />
        </div>
        <div style={{marginTop:10, display:'flex', gap:8, flexWrap:'wrap'}}>
          {['vandring','paddling','camping','utsikt','vindskydd'].map(tag=> (
            <Link key={tag} className="pill" href={`/aktivitet/${tag}`}>{tag}</Link>
          ))}
        </div>
      </div>
      <p style={{marginTop:16, display:'flex', gap:12}}>
        <Link className="btn" href="/search">Sök platser</Link>
        <Link className="btn" href="/events" style={{background:'#334155'}}>Evenemang</Link>
      </p>
    </div>
  )
}
