import { notFound } from 'next/navigation'
import { loadPlaces, slugify } from '../../../lib/data'
export const dynamic = 'force-dynamic';

export default async function ListingPage({ params }: { params: { slug: string } }) {
  const places = await loadPlaces();
  const match = places.find(p => slugify(String(p.id || p.name)) === params.slug);
  if (!match) return notFound();
  const title = `${match.name} – Lawnmover`;
  const desc = match.description || `Aktivitet: ${(match.categories||[]).join(', ')}`;
  const lat = match.lat; const lon = match.lon;
  const website = match.website;
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    'name': match.name,
    'description': desc,
    'brand': 'Lawnmover',
    'offers': {
      '@type': 'Offer',
      'availability': 'https://schema.org/InStock',
      'priceCurrency': 'SEK',
      'url': website || undefined
    }
  };
  const breadcrumbs = {
    '@context':'https://schema.org', '@type':'BreadcrumbList',
    itemListElement: [
      { '@type':'ListItem', position:1, name:'Hem', item:'/search' },
      { '@type':'ListItem', position:2, name: match.name, item:`/l/${params.slug}` }
    ]
  };
  return (
    <div className="container">
      <head>
        <title>{title}</title>
        <meta name="description" content={desc} />
        <link rel="canonical" href={`/l/${params.slug}`} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{__html: JSON.stringify(jsonLd)}} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{__html: JSON.stringify(breadcrumbs)}} />
      </head>
      <p><a href="/search" aria-label="Till sök">← Till sök</a></p>
      <div className="card" style={{display:'flex', alignItems:'center', justifyContent:'space-between', gap:12}}>
        <div>
          <h1 style={{margin:'0 0 6px'}}>{match.name}</h1>
          <div style={{color:'#64748b', fontSize:14}}>
            {(match.categories||[]).join(', ')}{' '}
            {typeof match.open_now === 'boolean' && (
              <span className="badge" style={{background:match.open_now?'#0f766e':'#b45309', color:'#fff', marginLeft:6}}>
                {match.open_now?'Öppet':'Stängt'}
              </span>
            )}
            {typeof match.link_ok === 'boolean' && (
              <span className="badge" style={{background:match.link_ok?'#0f766e':'#b00020', color:'#fff', marginLeft:6}}>
                {match.link_ok?'Länk OK':'Länk fel'}
              </span>
            )}
          </div>
        </div>
        {website ? <a className="btn" href={website} target="_blank" rel="noopener">Boka / Mer info</a> : null}
      </div>
      <div className="grid">
        <div className="card">
          <p>{desc}</p>
          <p><strong>Koordinater:</strong> {lat}, {lon}</p>
        </div>
        <div className="card">
          <iframe title="Karta" width="100%" height="300" style={{border:0}} loading="lazy"
            src={`https://www.openstreetmap.org/export/embed.html?marker=${lat}%2C${lon}&layer=mapnik`} />
        </div>
      </div>
      {/* Mobile sticky CTA */}
      {website ? (
        <div className="sticky-cta" role="region" aria-label="Snabbåtgärder">
          <a className="btn" href={website} target="_blank" rel="noopener" style={{display:'block', textAlign:'center'}}>Boka / Mer info</a>
        </div>
      ) : null}
    </div>
  );
}
