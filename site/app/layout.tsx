export const metadata = {
  title: 'Lawnmover – Återförsäljare av robotgräsklippare',
  description: 'Sök och hitta butiker i Sverige som säljer robotgräsklippare.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="sv">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet" />
        <style>{`
          :root { --accent: #0f766e; --bg:#ffffff; --text:#0f172a; --muted:#64748b; --border:#e5e7eb; }
          html, body { margin:0; padding:0; font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; background:var(--bg); color:var(--text); }
          a { color: var(--accent); text-decoration: none; }
          header { position:sticky; top:0; z-index:100; background:rgba(255,255,255,0.96); backdrop-filter:saturate(180%) blur(8px); border-bottom:1px solid var(--border); }
          .nav { max-width: 1200px; margin:0 auto; display:flex; align-items:center; gap:16px; padding:10px 16px; }
          .brand { font-weight:700; letter-spacing:0.2px; }
          .nav a { color:#0f172a; }
          .spacer { flex:1; }
          .container { max-width: 1200px; margin: 0 auto; padding: 16px; }
          .grid { display:grid; grid-template-columns: 1.6fr 1fr; gap: 16px; align-items:start; }
          @media (max-width: 1024px) { .grid { grid-template-columns: 1fr; } }
          .card { border: 1px solid var(--border); border-radius: 12px; padding: 14px; background:#fff; box-shadow: 0 1px 2px rgba(0,0,0,0.03); }
          .pill { border:1px solid var(--border); border-radius:999px; padding:10px 14px; display:flex; gap:10px; align-items:center; box-shadow:0 4px 16px rgba(0,0,0,0.06); background:#fff; }
          input[type=text] { border:0; outline:0; width:100%; font-size:14px; }
          .btn { display:inline-block; padding:10px 14px; border-radius:10px; background:var(--accent); color:#fff; }
          .btn:hover { filter:brightness(0.95); }
          .badge { display:inline-block; font-size:12px; padding:2px 8px; border-radius:999px; background:#eef2ff; color:#3730a3; }
          .chips { display:flex; gap:8px; flex-wrap:wrap; }
          .chip { border:1px solid var(--border); border-radius:999px; padding:6px 10px; background:#fff; cursor:pointer; }
          /* Mobile sticky CTA */
          .sticky-cta { position:fixed; left:0; right:0; bottom:0; background:rgba(255,255,255,0.96); border-top:1px solid var(--border); padding:10px 16px; display:none; }
          @media (max-width: 768px) { .sticky-cta { display:block; } }
        `}</style>
      </head>
      <body>
        <header>
          <nav className="nav">
            <a className="brand" href="/">Lawnmover</a>
            <a href="/search">Sök</a>
            
            <div className="spacer" />
            <a href="/dashboard" className="btn">För leverantörer</a>
          </nav>
        </header>
        {children}
        {/* Placeholder for global mobile actions if needed */}
      </body>
    </html>
  );
}
