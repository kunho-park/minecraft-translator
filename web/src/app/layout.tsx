import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    template: "%s | 모드팩 번역소",
    default: "모드팩 번역소 | 마인크래프트 번역 허브",
  },
  description:
    "마인크래프트 모드팩 번역, 맵 번역, 퀘스트 한글패치 등 다양한 번역을 손쉽게 다운로드하세요.",
  keywords: [
    "마인크래프트",
    "모드팩",
    "한글패치",
    "번역",
    "Minecraft",
    "Modpack",
    "Translation",
    "Korean",
    "퀘스트 번역",
    "FTB",
    "CurseForge",
    "Map",
    "맵맵"
  ],
  openGraph: {
    title: "마인크래프트 번역소 | Minecraft Translation Center",
    description: "마인크래프트 번역 공유 커뮤니티",
    url: "https://mcat.2odk.com",
    siteName: "마인크래프트 번역소",
    type: "website",
    locale: "ko_KR",
  },
  twitter: {
    card: "summary_large_image",
    title: "마인크래프트 번역소",
    description: "마인크래프트 한글패치 & 번역 공유 커뮤니티",
  },
  robots: {
    index: true,
    follow: true,
  },
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
