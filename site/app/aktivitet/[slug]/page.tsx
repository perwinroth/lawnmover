import { redirect } from 'next/navigation'

export default function AktivitetRedirect({ params }: { params: { slug: string } }) {
  const slug = decodeURIComponent(params.slug || '').toLowerCase()
  // Send known activity to search; default to query for the slug
  if (slug === 'robotgräsklippare' || slug === 'robotgrasklippare') {
    redirect('/search?q=robotgräsklippare')
  }
  redirect('/search' + (slug ? `?q=${encodeURIComponent(slug)}` : ''))
}

