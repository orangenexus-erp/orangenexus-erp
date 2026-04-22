import Link from "next/link";

export default function HomePage() {
  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-bold">Bienvenido a OrangeNexus ERP</h2>
      <p className="text-slate-600">Plataforma SaaS multi-tenant para operaciones administrativas en Venezuela.</p>
      <Link href="/dashboard" className="inline-block rounded bg-brand px-4 py-2 text-white">
        Ir al Dashboard
      </Link>
    </section>
  );
}
