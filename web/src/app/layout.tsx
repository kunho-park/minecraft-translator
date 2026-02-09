import type { Metadata } from "next";
import "./globals.css";

const baseUrl = "https://mcat.2odk.com";

export const metadata: Metadata = {
  metadataBase: new URL(baseUrl),
  title: {
    template: "%s | 마인크래프트 번역소",
    default: "마인크래프트 번역소 | 모드팩·맵 한글패치 무료 다운로드",
  },
  description:
    "마인크래프트 모드팩 한글패치, 맵 번역, 퀘스트 한글화를 무료로 다운로드하세요. ATM, FTB, Create 등 인기 모드팩과 다양한 맵의 최신 한국어 번역을 제공하는 커뮤니티입니다.",
  keywords: [
    "마인크래프트 한글패치",
    "마인크래프트 모드팩 번역",
    "마인크래프트 맵 번역",
    "마인크래프트 맵 한글패치",
    "모드팩 한글화",
    "Minecraft Korean translation",
    "Minecraft modpack translation",
    "Minecraft map translation",
    "마인크래프트 번역 다운로드",
    "마인크래프트 퀘스트 번역",
    "FTB 한글패치",
    "ATM 한글패치",
    "Create 한글패치",
    "CurseForge 번역",
    "마인크래프트",
    "모드팩",
    "맵",
    "한글패치",
    "번역",
    "Minecraft",
    "Modpack",
    "Map",
    "Translation",
    "Korean",
    "리소스팩",
    "퀘스트 한글화",
  ],
  openGraph: {
    title: "마인크래프트 번역소 | 모드팩·맵 한글패치 무료 다운로드",
    description:
      "마인크래프트 모드팩, 맵 한글패치를 무료로 다운로드하세요. 인기 모드팩과 맵의 최신 번역을 제공합니다.",
    url: baseUrl,
    siteName: "마인크래프트 번역소",
    type: "website",
    locale: "ko_KR",
    alternateLocale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "마인크래프트 번역소 | 모드팩·맵 한글패치",
    description:
      "마인크래프트 모드팩, 맵 한글패치를 무료로 다운로드하세요. 인기 모드팩과 맵의 최신 번역을 제공합니다.",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  alternates: {
    canonical: baseUrl,
    languages: {
      "ko": baseUrl,
      "en": `${baseUrl}/en`,
    },
  },
  verification: {},
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html suppressHydrationWarning>
      <head>
        <link rel="canonical" href={baseUrl} />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
