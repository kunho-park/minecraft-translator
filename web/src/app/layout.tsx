import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "모드팩 번역소 | Modpack Translations",
  description: "마인크래프트 모드팩 번역을 공유하는 커뮤니티",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html suppressHydrationWarning>
      <body className="antialiased">{children}</body>
    </html>
  );
}
