import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { prisma } from "@/lib/prisma";
import { Search, ArrowRight, Package, Download, Users, Sparkles, TrendingUp, Zap, Map as MapIcon, Globe } from "lucide-react";
import ModpackCard from "@/components/ui/ModpackCard";
import MapCard from "@/components/ui/MapCard";
import type { Metadata } from "next";

// Force dynamic rendering (no static generation)
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "마인크래프트 번역소 | 모드팩·맵 한글패치 무료 다운로드",
  description:
    "마인크래프트 모드팩 한글패치, 맵 번역, 퀘스트 한글화를 무료로 다운로드하세요. ATM, FTB, Create 등 인기 모드팩과 맵의 최신 한국어 번역을 제공합니다.",
  keywords: [
    "마인크래프트 한글패치",
    "마인크래프트 모드팩 번역",
    "마인크래프트 맵 번역",
    "마인크래프트 한국어",
    "모드팩 한글화",
    "맵 한글패치",
    "퀘스트 번역",
    "Minecraft Korean translation",
    "Minecraft modpack translation",
    "Minecraft map translation",
    "마인크래프트 번역 다운로드",
    "FTB 한글패치",
    "ATM 한글패치",
    "CurseForge 번역",
  ],
  alternates: {
    canonical: "https://mcat.2odk.com",
    languages: {
      "ko": "https://mcat.2odk.com",
      "en": "https://mcat.2odk.com/en",
    },
  },
};

interface HomePageProps {
  params: Promise<{ locale: string }>;
}

export default async function HomePage({ params }: HomePageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  // Get latest translated modpacks (approved only)
  // Sorted by the creation time of the translation pack, not the modpack cache time
  const latestTranslations = await prisma.translationPack.findMany({
    where: { status: "approved" },
    orderBy: { createdAt: "desc" },
    distinct: ["modpackId"],
    take: 6,
    include: {
      modpack: {
        include: {
          _count: {
            select: { translationPacks: true },
          },
          translationPacks: {
            where: { status: "approved" },
            select: {
              targetLang: true,
              downloadCount: true,
            },
          },
        },
      },
    },
  });

  const latestModpacks = latestTranslations.map((t) => t.modpack);

  // Get popular modpacks (by total translation downloads)
  const popularModpacks = await prisma.modpack.findMany({
    where: {
      translationPacks: {
        some: {
          status: "approved",
        },
      },
    },
    include: {
      _count: {
        select: { translationPacks: true },
      },
      translationPacks: {
        where: { status: "approved" },
        select: {
          targetLang: true,
          downloadCount: true,
        },
      },
    },
    take: 100,
  });

  // Sort by total downloads
  const sortedPopular = popularModpacks
    .map((mp: any) => ({
      ...mp,
      totalTranslationDownloads: mp.translationPacks.reduce(
        (sum: number, tp: any) => sum + (tp.downloadCount || 0),
        0
      ),
    }))
    .sort((a: any, b: any) => b.totalTranslationDownloads - a.totalTranslationDownloads)
    .slice(0, 6);

  // Get latest translated maps (approved only)
  const latestMapTranslations = await prisma.mapTranslation.findMany({
    where: { status: "approved" },
    orderBy: { createdAt: "desc" },
    distinct: ["mapId"],
    take: 6,
    include: {
      map: {
        include: {
          _count: {
            select: { translations: true },
          },
          translations: {
            where: { status: "approved" },
            select: {
              targetLang: true,
              downloadCount: true,
            },
          },
        },
      },
    },
  });

  const latestMaps = latestMapTranslations.map((t) => t.map);

  // Get popular maps (by total translation downloads)
  const popularMapsRaw = await prisma.map.findMany({
    where: {
      translations: {
        some: { status: "approved" },
      },
    },
    include: {
      _count: {
        select: { translations: true },
      },
      translations: {
        where: { status: "approved" },
        select: {
          targetLang: true,
          downloadCount: true,
        },
      },
    },
    take: 100,
  });

  const sortedPopularMaps = popularMapsRaw
    .map((m: any) => ({
      ...m,
      totalTranslationDownloads: m.translations.reduce(
        (sum: number, t: any) => sum + (t.downloadCount || 0),
        0
      ),
    }))
    .sort((a: any, b: any) => b.totalTranslationDownloads - a.totalTranslationDownloads)
    .slice(0, 6);

  // Get stats
  const [modpackCount, translationCount, modpackDownloads, mapCount, mapTranslationCount, mapDownloads] = await Promise.all([
    prisma.modpack.count({
      where: {
        translationPacks: {
          some: { status: "approved" },
        },
      },
    }),
    prisma.translationPack.count({
      where: { status: "approved" },
    }),
    prisma.translationPack.aggregate({
      where: { status: "approved" },
      _sum: { downloadCount: true },
    }),
    prisma.map.count({
      where: {
        translations: {
          some: { status: "approved" },
        },
      },
    }),
    prisma.mapTranslation.count({
      where: { status: "approved" },
    }),
    prisma.mapTranslation.aggregate({
      where: { status: "approved" },
      _sum: { downloadCount: true },
    }),
  ]);

  const stats = {
    modpacks: modpackCount,
    maps: mapCount,
    translations: translationCount + mapTranslationCount,
    downloads: (modpackDownloads._sum.downloadCount || 0) + (mapDownloads._sum.downloadCount || 0),
  };

  // JSON-LD structured data for the homepage
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "마인크래프트 번역소",
    "alternateName": ["Minecraft Translation Center", "MCAT"],
    "url": "https://mcat.2odk.com",
    "description": "마인크래프트 모드팩, 맵 한글패치 및 번역을 무료로 다운로드할 수 있는 커뮤니티",
    "inLanguage": ["ko", "en"],
    "potentialAction": {
      "@type": "SearchAction",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://mcat.2odk.com/modpacks?q={search_term_string}"
      },
      "query-input": "required name=search_term_string"
    }
  };

  const orgJsonLd = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "마인크래프트 번역소",
    "url": "https://mcat.2odk.com",
    "logo": "https://mcat.2odk.com/favicon.ico",
    "description": "마인크래프트 번역 공유 커뮤니티"
  };

  return (
    <div className="animate-fade-in">
      {/* JSON-LD Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(orgJsonLd) }}
      />

      {/* Hero Section */}
      <section className="relative py-28 px-4 overflow-hidden">
        {/* Background effects */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-gradient-radial from-[var(--accent-primary)]/8 to-transparent blur-3xl" />
          <div className="absolute bottom-0 left-0 w-[600px] h-[400px] bg-gradient-radial from-[var(--accent-secondary)]/5 to-transparent blur-3xl" />
        </div>

        <div className="max-w-4xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/20 mb-8">
            <Zap className="w-4 h-4 text-[var(--accent-primary)]" />
            <span className="text-sm font-medium text-[var(--accent-primary)]">{t("home.hero.badge")}</span>
          </div>

          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-[var(--text-primary)] mb-6 leading-[1.1] tracking-tight">
            {t("home.hero.title")}
          </h1>
          <p className="text-lg md:text-xl text-[var(--text-secondary)] mb-12 max-w-2xl mx-auto leading-relaxed">
            {t("home.hero.subtitle")}
          </p>

          {/* Search Bar */}
          <form action="/modpacks" method="GET" className="max-w-xl mx-auto">
            <div className="relative group">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-muted)] group-focus-within:text-[var(--accent-primary)] transition-colors pointer-events-none" />
              <input
                type="text"
                name="q"
                placeholder={t("home.hero.searchPlaceholder")}
                className="w-full py-4 text-lg rounded-2xl bg-[var(--bg-card)] border-2 border-[var(--border-primary)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:border-[var(--accent-primary)] focus:shadow-lg focus:shadow-[var(--accent-primary)]/10 transition-all"
                style={{ paddingLeft: "3.25rem", paddingRight: "5rem" }}
              />
              <button
                type="submit"
                className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-[var(--accent-primary)] text-white rounded-xl font-semibold hover:bg-[var(--accent-secondary)] transition-all"
              >
                {t("common.search")}
              </button>
            </div>
          </form>

          {/* Quick navigation */}
          <div className="flex items-center justify-center gap-4 mt-8">
            <Link
              href="/modpacks"
              className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-[var(--text-secondary)] hover:text-[var(--accent-primary)] bg-[var(--bg-card)] border border-[var(--border-primary)] hover:border-[var(--accent-primary)]/30 rounded-xl transition-all"
            >
              <Package className="w-4 h-4" />
              {t("home.hero.browseModpacks")}
            </Link>
            <Link
              href="/maps"
              className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-[var(--text-secondary)] hover:text-[var(--accent-primary)] bg-[var(--bg-card)] border border-[var(--border-primary)] hover:border-[var(--accent-primary)]/30 rounded-xl transition-all"
            >
              <MapIcon className="w-4 h-4" />
              {t("home.hero.browseMaps")}
            </Link>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 px-4 border-y border-[var(--border-primary)] bg-[var(--bg-secondary)]/50">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="group p-6 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-primary)] hover:border-[var(--accent-primary)]/30 transition-all">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] shadow-lg shadow-[var(--accent-primary)]/20">
                  <Package className="w-6 h-6 text-white" />
                </div>
                <div>
                  <div className="text-3xl font-bold text-[var(--text-primary)] stat-number">
                    {stats.modpacks}
                  </div>
                  <div className="text-sm text-[var(--text-muted)] font-medium">
                    {t("nav.modpacks")}
                  </div>
                </div>
              </div>
            </div>

            <div className="group p-6 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-primary)] hover:border-[var(--status-warning)]/30 transition-all">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 shadow-lg shadow-amber-500/20">
                  <MapIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <div className="text-3xl font-bold text-[var(--text-primary)] stat-number">
                    {stats.maps}
                  </div>
                  <div className="text-sm text-[var(--text-muted)] font-medium">
                    {t("nav.maps")}
                  </div>
                </div>
              </div>
            </div>

            <div className="group p-6 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-primary)] hover:border-[var(--status-info)]/30 transition-all">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-gradient-to-br from-[var(--status-info)] to-blue-600 shadow-lg shadow-[var(--status-info)]/20">
                  <Users className="w-6 h-6 text-white" />
                </div>
                <div>
                  <div className="text-3xl font-bold text-[var(--text-primary)] stat-number">
                    {stats.translations}
                  </div>
                  <div className="text-sm text-[var(--text-muted)] font-medium">
                    {t("modpacks.card.translations")}
                  </div>
                </div>
              </div>
            </div>

            <div className="group p-6 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-primary)] hover:border-[var(--status-success)]/30 transition-all">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-gradient-to-br from-[var(--status-success)] to-emerald-600 shadow-lg shadow-[var(--status-success)]/20">
                  <Download className="w-6 h-6 text-white" />
                </div>
                <div>
                  <div className="text-3xl font-bold text-[var(--text-primary)] stat-number">
                    {stats.downloads.toLocaleString()}
                  </div>
                  <div className="text-sm text-[var(--text-muted)] font-medium">
                    {t("common.download")}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Latest Modpack Translations */}
      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-10">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/20">
                <Sparkles className="w-6 h-6 text-[var(--accent-primary)]" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-[var(--text-primary)]">
                  {t("home.sections.latestModpacks")}
                </h2>
                <p className="text-sm text-[var(--text-muted)]">{t("home.sections.latestModpacksDesc")}</p>
              </div>
            </div>
            <Link
              href="/modpacks?sort=latest"
              className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-[var(--accent-primary)] hover:text-white hover:bg-[var(--accent-primary)] rounded-xl transition-all"
            >
              {t("home.sections.viewAll")}
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {latestModpacks.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {latestModpacks.map((modpack: any, i: number) => (
                <div
                  key={modpack.id}
                  className={`animate-fade-in stagger-${(i % 5) + 1}`}
                  style={{ opacity: 0 }}
                >
                  <ModpackCard modpack={modpack} />
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-20 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-secondary)]">
              <p className="text-lg text-[var(--text-muted)]">
                {t("modpacks.noResults")}
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Latest Map Translations */}
      {latestMaps.length > 0 && (
        <section className="py-20 px-4 bg-gradient-to-b from-[var(--bg-secondary)]/50 to-[var(--bg-primary)]">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-10">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
                  <Globe className="w-6 h-6 text-amber-500" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-[var(--text-primary)]">
                    {t("home.sections.latestMaps")}
                  </h2>
                  <p className="text-sm text-[var(--text-muted)]">{t("home.sections.latestMapsDesc")}</p>
                </div>
              </div>
              <Link
                href="/maps?sort=latest"
                className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-[var(--accent-primary)] hover:text-white hover:bg-[var(--accent-primary)] rounded-xl transition-all"
              >
                {t("home.sections.viewAll")}
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {latestMaps.map((map: any, i: number) => (
                <div
                  key={map.id}
                  className={`animate-fade-in stagger-${(i % 5) + 1}`}
                  style={{ opacity: 0 }}
                >
                  <MapCard map={map} />
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Popular Modpack Translations */}
      {sortedPopular.length > 0 && (
        <section className="py-20 px-4 bg-gradient-to-b from-[var(--bg-primary)] to-[var(--bg-secondary)]">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-10">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-[var(--status-warning)]/10 border border-[var(--status-warning)]/20">
                  <TrendingUp className="w-6 h-6 text-[var(--status-warning)]" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-[var(--text-primary)]">
                    {t("home.sections.popularModpacks")}
                  </h2>
                  <p className="text-sm text-[var(--text-muted)]">{t("home.sections.popularModpacksDesc")}</p>
                </div>
              </div>
              <Link
                href="/modpacks?sort=downloads"
                className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-[var(--accent-primary)] hover:text-white hover:bg-[var(--accent-primary)] rounded-xl transition-all"
              >
                {t("home.sections.viewAll")}
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sortedPopular.map((modpack: any, i: number) => (
                <div
                  key={modpack.id}
                  className={`animate-fade-in stagger-${(i % 5) + 1}`}
                  style={{ opacity: 0 }}
                >
                  <ModpackCard modpack={modpack} />
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Popular Map Translations */}
      {sortedPopularMaps.length > 0 && (
        <section className="py-20 px-4 bg-gradient-to-b from-[var(--bg-secondary)] to-[var(--bg-primary)]">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-10">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                  <TrendingUp className="w-6 h-6 text-emerald-500" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-[var(--text-primary)]">
                    {t("home.sections.popularMaps")}
                  </h2>
                  <p className="text-sm text-[var(--text-muted)]">{t("home.sections.popularMapsDesc")}</p>
                </div>
              </div>
              <Link
                href="/maps?sort=downloads"
                className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-[var(--accent-primary)] hover:text-white hover:bg-[var(--accent-primary)] rounded-xl transition-all"
              >
                {t("home.sections.viewAll")}
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sortedPopularMaps.map((map: any, i: number) => (
                <div
                  key={map.id}
                  className={`animate-fade-in stagger-${(i % 5) + 1}`}
                  style={{ opacity: 0 }}
                >
                  <MapCard map={map} />
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
