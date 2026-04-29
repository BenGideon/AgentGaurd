import { ClerkProvider } from "@clerk/nextjs";
import AppHeader from "./components/AppHeader";
import "./globals.css";

export const metadata = {
  title: "AgentGuard Dashboard",
  description: "Minimal dashboard for AgentGuard approvals and audit logs",
};

export default function RootLayout({ children }) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className="min-h-screen">
          <AppHeader />
          <main className="mx-auto max-w-6xl px-5 py-8">{children}</main>
        </body>
      </html>
    </ClerkProvider>
  );
}
