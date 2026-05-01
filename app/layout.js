import { ClerkProvider } from "@clerk/nextjs";
import AppHeader from "./components/AppHeader";
import "./globals.css";

export const metadata = {
  title: "AgentGuard Dashboard",
  description: "Minimal dashboard for AgentGuard approvals and audit logs",
};

export default function RootLayout({ children }) {
  const content = (
    <html lang="en">
      <body className="min-h-screen">
        <AppHeader />
        <main className="mx-auto max-w-6xl px-5 py-8">{children}</main>
      </body>
    </html>
  );

  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    return content;
  }

  return (
    <ClerkProvider>
      {content}
    </ClerkProvider>
  );
}
