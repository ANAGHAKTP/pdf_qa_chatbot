import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DOCMind Enterprise — Advanced Document Intelligence",
  description: "Enterprise PDF QA, structured summaries, and RAG analytics dashboard.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
