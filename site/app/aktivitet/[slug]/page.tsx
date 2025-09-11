import Link from 'next/link'
import { loadPlaces, slugify } from '../../../lib/data'

export default async function ActivityPage({ params }: { params: { slug: string } }) {
  const places = await loadPlaces();
  const list = places.filter(p => (p.categories||[]).some((c:string)=> c.replace(/\s+/g,'_').toLowerCase()===params.slug));
  return (
    <div className="container">
      <h1>Aktivitet: {params.slug}</h1>
      <div className="card">
        <ul>
          {list.map(p => (
            <li key={p.id}><Link href={`/l/${slugify(String(p.id||p.name))}`}>{p.name}</Link></li>
          ))}
        </ul>
      </div>
    </div>
  )
}

