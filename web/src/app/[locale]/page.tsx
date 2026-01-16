import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { prisma } from "@/lib/prisma";
import { Search, ArrowRight, Package, Download, Users, Sparkles, TrendingUp, Zap } from "lucide-react";
import ModpackCard from "@/components/ui/ModpackCard";
import type { Metadata } from "next";

// Force dynamic rendering (no static generation)
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "홈",
  description:
    "최신 마인크래프트 모드팩 한글패치와 번역을 찾아보세요. 인기 있는 모드팩의 번역을 무료로 다운로드할 수 있습니다.",
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

  // Get stats
  const stats = {
    modpacks: await prisma.modpack.count({
      where: {
        translationPacks: {
          some: { status: "approved" },
        },
      },
    }),
    translations: await prisma.translationPack.count({
      where: { status: "approved" },
    }),
    downloads: (
      await prisma.translationPack.aggregate({
        where: { status: "approved" },
        _sum: { downloadCount: true },
      })
    )._sum.downloadCount || 0,
  };

  return (
    <div className="animate-fade-in">
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
            <span className="text-sm font-medium text-[var(--accent-primary)]">마인크래프트 모드팩 번역 허브</span>
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
                검색
              </button>
            </div>
          </form>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 px-4 border-y border-[var(--border-primary)] bg-[var(--bg-secondary)]/50">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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

      {/* Latest Translations */}
      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-10">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/20">
                <Sparkles className="w-6 h-6 text-[var(--accent-primary)]" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-[var(--text-primary)]">
                  {t("home.sections.latest")}
                </h2>
                <p className="text-sm text-[var(--text-muted)]">최근 추가된 번역</p>
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

      {/* Popular Translations */}
      {sortedPopular.length > 0 && (
        <section className="py-20 px-4 bg-gradient-to-b from-[var(--bg-secondary)] to-[var(--bg-primary)]">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-10">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-[var(--status-warning)]/10 border border-[var(--status-warning)]/20">
                  <TrendingUp className="w-6 h-6 text-[var(--status-warning)]" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-[var(--text-primary)]">
                    {t("home.sections.popular")}
                  </h2>
                  <p className="text-sm text-[var(--text-muted)]">가장 많이 다운로드된 번역</p>
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
    </div>
  );
}
