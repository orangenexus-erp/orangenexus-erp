"use client";

import { useAuth } from "@/hooks/useAuth";

export function Navbar() {
  const { isAuthenticated, logout } = useAuth();

  return (
    <header className="h-14 border-b bg-white px-6 flex items-center justify-between">
      <h1 className="font-semibold text-brand">OrangeNexus ERP</h1>
      {isAuthenticated ? (
        <button
          onClick={logout}
          className="rounded-md bg-slate-800 px-3 py-1.5 text-sm text-white hover:bg-slate-900"
        >
          Cerrar sesión
        </button>
      ) : null}
    </header>
  );
}
