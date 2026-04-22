"use client";

import Link from "next/link";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard?module=accounting", label: "Contabilidad" },
  { href: "/dashboard?module=sales", label: "Ventas" },
  { href: "/dashboard?module=treasury", label: "Tesorería" },
  { href: "/dashboard?module=purchases", label: "Compras" },
];

export function Sidebar() {
  return (
    <aside className="w-60 border-r bg-white p-4">
      <nav className="space-y-2">
        {links.map((link) => (
          <Link key={link.href} href={link.href} className="block rounded px-3 py-2 text-sm hover:bg-slate-100">
            {link.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
