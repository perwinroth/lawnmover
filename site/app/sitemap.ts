import { MetadataRoute } from 'next'
import { loadPlaces, slugify } from '../lib/data'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = 'https://perwinroth.github.io/friluft'
  const urls: MetadataRoute.Sitemap = [
    { url: `${base}/web/`, lastModified: new Date() },
    { url: `${base}/web/list.html`, lastModified: new Date() },
  ]
  try {
    const places = await loadPlaces()
    places.slice(0, 500).forEach(p=> {
      urls.push({ url: `${base}/l/${slugify(String(p.id || p.name))}`, lastModified: new Date() })
    })
  } catch {}
  return urls
}

