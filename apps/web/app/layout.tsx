import "@/styles/globals.css";

import { Navbar } from "@/components/layout/Navbar";
import { Sidebar } from "@/components/layout/Sidebar";
import { AuthProvider } from "@/lib/auth";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>
        <AuthProvider>
          <div className="min-h-screen">
            <Navbar />
            <div className="flex min-h-[calc(100vh-56px)]">
              <Sidebar />
              <main className="flex-1 p-6">{children}</main>
            </div>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
