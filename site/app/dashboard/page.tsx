"use client";
import { useState } from 'react'

export default function DashboardPage() {
  const [form, setForm] = useState({ title:'', website:'', price_from:'', categories:'', description:'' })
  const submit = async (e: any) => {
    e.preventDefault();
    await fetch('/api/proposals', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ type:'listing-proposal', ...form }) })
    alert('Tack! Vi hör av oss. (Detta är en MVP-demo)')
    setForm({ title:'', website:'', price_from:'', categories:'', description:'' })
  }
  return (
    <div className="container">
      <h1>Leverantör – Skapa listning (demo)</h1>
      <form className="card" onSubmit={submit}>
        <label>Titel<br/><input type="text" value={form.title} onChange={e=>setForm({...form, title:e.target.value})} required /></label>
        <br/>
        <label>Webbplats/Booking-URL<br/><input type="url" value={form.website} onChange={e=>setForm({...form, website:e.target.value})} required /></label>
        <br/>
        <label>Pris från (SEK)<br/><input type="number" value={form.price_from} onChange={e=>setForm({...form, price_from:e.target.value})} /></label>
        <br/>
        <label>Kategorier (kommaseparerade)<br/><input type="text" value={form.categories} onChange={e=>setForm({...form, categories:e.target.value})} /></label>
        <br/>
        <label>Beskrivning<br/><textarea value={form.description} onChange={e=>setForm({...form, description:e.target.value})} /></label>
        <br/>
        <button className="pill" type="submit">Skicka</button>
      </form>
      <p>Kommande: inloggning, bilduppladdning, iCal-import, tillgänglighet och direktbokning.</p>
    </div>
  )
}
