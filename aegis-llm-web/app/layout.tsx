import type { Metadata } from "next";
import { Providers } from "@/lib/providers";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: { default: "Aegis-LLM", template: "%s · Aegis-LLM" },
  description: "Safe-by-design, multi-agent LLM red-teaming platform — operator console",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
