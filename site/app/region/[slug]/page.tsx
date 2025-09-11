// Placeholder region page: in a real app, map places to municipalities/regions via reverse geocoding.
export default function RegionPage({ params }: { params: { slug: string } }) {
  return (
    <div className="container">
      <h1>Region: {params.slug}</h1>
      <p>Kommer snart: platser, guider och evenemang i denna region.</p>
    </div>
  );
}

