import { Card } from "@/components/ui/Card";

export default function DashboardPage() {
  return (
    <section className="space-y-6">
      <h2 className="text-2xl font-bold">Dashboard</h2>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card title="Ventas del mes">$12,450</Card>
        <Card title="CxC Pendiente">$4,120</Card>
        <Card title="CxP Pendiente">$2,980</Card>
        <Card title="Tasa BCV">Bs 36.50</Card>
      </div>
      <div className="rounded-lg border bg-white p-5 text-sm text-slate-600">
        Placeholder MVP: aquí se conectarán los indicadores en tiempo real por módulo.
      </div>
    </section>
  );
}
