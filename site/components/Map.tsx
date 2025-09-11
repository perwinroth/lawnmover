"use client";
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect, useRef } from 'react';

type Props = { query?: string; cats?: string[]; height?: string };

export default function Map({ query = '', cats = [], height = '60vh' }: Props) {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletRef = useRef<L.Map | null>(null);
  const clusterRef = useRef<any>(null);

  useEffect(()=>{
    if (!mapRef.current || leafletRef.current) return;
    const map = L.map(mapRef.current).setView([62.0, 15.0], 5);
    leafletRef.current = map;
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
    const ensureCluster = async () => {
      // @ts-ignore
      if (!(L as any).markerClusterGroup) {
        await loadCss('https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css');
        await loadCss('https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css');
        await loadScript('https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js');
      }
      // @ts-ignore
      const cluster = (L as any).markerClusterGroup ? (L as any).markerClusterGroup({
        disableClusteringAtZoom:14, showCoverageOnHover:false, spiderfyOnMaxZoom:true, maxClusterRadius:50
      }) : L.layerGroup();
      clusterRef.current = cluster;
      map.addLayer(cluster);
    };
    ensureCluster();
    // Listen to focus events
    const handler = (e: any) => {
      const d = e.detail || {}; const { lat, lon, zoom } = d;
      if (typeof lat === 'number' && typeof lon === 'number') {
        map.setView([lat, lon], zoom || Math.max(map.getZoom(), 12));
      }
    };
    window.addEventListener('friluft:focus', handler);
    return () => {
      window.removeEventListener('friluft:focus', handler);
    };
  },[]);

  useEffect(()=>{
    const map = leafletRef.current; const cluster = clusterRef.current; if (!map || !cluster) return;
    // Clear
    // @ts-ignore
    if (cluster.clearLayers) cluster.clearLayers();
    fetch('/api/data?kind=geojson')
      .then(r=>r.json())
      .then(geo=>{
        (geo.features||[]).forEach((f:any)=>{
          const [lon, lat] = f.geometry.coordinates;
          const p = f.properties||{};
          const name = p.name || '(namnlös)';
          const link = p.link || p.osm_url;
          const categories = p.categories || [];
          // filter
          const qok = !query || String(name).toLowerCase().includes(query.toLowerCase());
          const cok = !cats.length || categories.some((c:string)=> cats.includes(c));
          if (!qok || !cok) return;
          const marker = L.marker([lat, lon]);
          marker.bindPopup(`<strong>${name}</strong><br/><a href="${link}" target="_blank" rel="noopener">Länk</a>`);
          marker.on('click', () => {
            if (typeof window !== 'undefined') {
              window.dispatchEvent(new CustomEvent('friluft:select', { detail: { props: p, lat, lon } }))
            }
          });
          // @ts-ignore
          if (cluster.addLayer) cluster.addLayer(marker); else marker.addTo(cluster);
        });
      })
  },[query, cats.join(',')]);

  return <div ref={mapRef} style={{height, width: '100%', borderRadius: 12, overflow: 'hidden'}} />
}

function loadScript(src: string) {
  return new Promise<void>((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src; s.async = true; s.onload = () => resolve(); s.onerror = () => reject();
    document.head.appendChild(s);
  });
}

function loadCss(href: string) {
  return new Promise<void>((resolve) => {
    const l = document.createElement('link');
    l.rel = 'stylesheet'; l.href = href; l.onload = () => resolve();
    document.head.appendChild(l);
  });
}
