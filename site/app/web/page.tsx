// Redirect /web to the static HTML under public/web/index.html so it works on Vercel
import { redirect } from 'next/navigation'

export default function WebRedirectPage() {
  redirect('/web/index.html')
}

