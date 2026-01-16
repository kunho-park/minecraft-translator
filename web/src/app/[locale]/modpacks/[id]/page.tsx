import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { prisma } from "@/lib/prisma";
import { notFound } from "next/navigation";
import Image from "next/image";
import type { Metadata, ResolvingMetadata } from "next";

// Force dynamic rendering (no static generation)
export const dynamic = "force-dynamic";

import TranslationDownloadActions from "@/components/TranslationDownloadActions";
import {
  Download,
  ExternalLink,
  Search,
  User,
  Calendar,
  Check,
  X,
  MessageSquare,
  Star,
  ThermometerSun,
  Layers,
  BookOpen,
  CheckCircle,
  Bot,
  PenLine,
  BarChart3,
  FileText,
  Hash,
  Clock,
  Cpu,
} from "lucide-react";
import Button from "@/components/ui/Button";

interface ModpackDetailPageProps {
  params: Promise<{ locale: string; id: string }>;
}

export async function generateMetadata(
  { params }: ModpackDetailPageProps,
  parent: ResolvingMetadata
): Promise<Metadata> {
  const { id } = await params;
  const modpackId = parseInt(id, 10);

  if (isNaN(modpackId)) {
    return {
      title: "모드팩을 찾을 수 없습니다",
    };
  }

  const modpack = await prisma.modpack.findUnique({
    where: { id: modpackId },
  });

  if (!modpack) {
    return {
      title: "모드팩을 찾을 수 없습니다",
    };
  }

  const previousImages = (await parent).openGraph?.images || [];

  return {
    title: `${modpack.name} 한글패치 & 번역 다운로드`,
    description: `${modpack.name} 모드팩의 한글 번역, 퀘스트 번역을 다운로드하세요. ${modpack.summary}`,
    keywords: [modpack.name, "한글패치", "번역", "Modpack", "Minecraft", "마인크래프트"],
    openGraph: {
      title: `${modpack.name} 한글패치 다운로드`,
      description: modpack.summary || undefined,
      images: modpack.logoUrl ? [modpack.logoUrl, ...previousImages] : previousImages,
    },
  };
}

export default async function ModpackDetailPage({
  params,
}: ModpackDetailPageProps) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const modpackId = parseInt(id, 10);
  let modpack = null;

  if (!isNaN(modpackId)) {
    modpack = await prisma.modpack.findUnique({
      where: { id: modpackId },
      include: {
        translationPacks: {
          where: { status: "approved" },
          include: {
            user: {
              select: { name: true, avatar: true },
            },
            _count: {
              select: { reviews: true },
            },
          },
          orderBy: { createdAt: "desc" },
        },
      },
    });
  }

  if (!modpack) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center animate-fade-in">
        <div className="glass rounded-xl p-8 md:p-16 border border-[var(--border-primary)]">
          <div className="w-24 h-24 bg-[var(--bg-tertiary)] rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
            <Search className="w-10 h-10 text-[var(--accent-primary)]" />
          </div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-4">
            모드팩을 찾을 수 없습니다
          </h1>
          <p className="text-lg text-[var(--text-secondary)] mb-8 max-w-lg mx-auto leading-relaxed">
            사이트가 개편되어 페이지 주소가 변경되었습니다.
            <br />
            아래 버튼을 눌러 모드팩을 다시 검색해주세요.
          </p>
          <Link href="/modpacks">
            <Button size="lg" className="shadow-lg hover:shadow-xl transition-shadow">
              모드팩 검색하러 가기
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  // Get reviews for all translation packs
  const reviewStats = await prisma.review.groupBy({
    by: ["packId"],
    where: {
      packId: {
        in: modpack.translationPacks.map((tp) => tp.id),
      },
    },
    _avg: {
      rating: true,
    },
    _count: {
      works: true,
    },
  });

  const reviewStatsMap = new Map(
    reviewStats.map((r) => [r.packId, { avgRating: r._avg.rating || 0 }])
  );

  // Get works count
  const worksCount = await prisma.review.groupBy({
    by: ["packId", "works"],
    where: {
      packId: {
        in: modpack.translationPacks.map((tp) => tp.id),
      },
    },
    _count: true,
  });

  const worksMap = new Map<string, { works: number; notWorks: number }>();
  worksCount.forEach((w) => {
    const current = worksMap.get(w.packId) || { works: 0, notWorks: 0 };
    if (w.works) {
      current.works = w._count;
    } else {
      current.notWorks = w._count;
    }
    worksMap.set(w.packId, current);
  });

  const gameVersions = modpack.gameVersions
    ? JSON.parse(modpack.gameVersions)
    : [];

  // JSON-LD for SEO
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": modpack.name,
    "applicationCategory": "Game",
    "operatingSystem": "Windows, macOS, Linux",
    "description": modpack.summary,
    "image": modpack.logoUrl,
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "KRW",
    },
    "author": {
      "@type": "Person",
      "name": modpack.author
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 animate-fade-in">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      {/* Modpack Header */}
      <div className="glass rounded-xl p-6 mb-8">
        <div className="flex flex-col md:flex-row gap-6">
          {/* Logo */}
          {modpack.logoUrl ? (
            <Image
              src={modpack.logoUrl}
              alt={modpack.name}
              width={128}
              height={128}
              className="w-32 h-32 rounded-xl object-cover flex-shrink-0"
            />
          ) : (
            <div className="w-32 h-32 rounded-xl bg-[var(--bg-tertiary)] flex items-center justify-center flex-shrink-0">
              <span className="text-4xl font-bold text-[var(--text-muted)]">
                {modpack.name.charAt(0)}
              </span>
            </div>
          )}

          {/* Info */}
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-2">
              {modpack.name}
            </h1>
            {modpack.author && (
              <p className="flex items-center gap-2 text-[var(--text-secondary)] mb-4">
                <User className="w-4 h-4" />
                {modpack.author}
              </p>
            )}
            <p className="text-[var(--text-secondary)] mb-4">{modpack.summary}</p>

            {/* Game versions */}
            {gameVersions.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {gameVersions.slice(0, 5).map((v: string) => (
                  <span key={v} className="badge">
                    {v}
                  </span>
                ))}
                {gameVersions.length > 5 && (
                  <span className="badge">+{gameVersions.length - 5}</span>
                )}
              </div>
            )}

            {/* Stats */}
            <div className="flex items-center gap-6 text-sm text-[var(--text-muted)]">
              <span className="flex items-center gap-1.5">
                <Download className="w-4 h-4" />
                {modpack.totalDownloads.toLocaleString()} {t("modpack.info.downloads")}
              </span>
              <span className="flex items-center gap-1.5">
                <Calendar className="w-4 h-4" />
                {new Date(modpack.cachedAt).toLocaleDateString()}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-3">
            <Link href={`/upload?modpack=${modpack.curseforgeId}`}>
              <Button className="w-full">{t("modpack.uploadTranslation")}</Button>
            </Link>
            <a
              href={`https://www.curseforge.com/minecraft/modpacks/${modpack.slug}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button variant="secondary" className="w-full">
                <ExternalLink className="w-4 h-4" />
                CurseForge
              </Button>
            </a>
          </div>
        </div>
      </div>

      {/* Translations */}
      <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-6">
        {t("modpack.translations")}
      </h2>

      {modpack.translationPacks.length > 0 ? (
        <div className="space-y-6">
          {modpack.translationPacks.map((pack) => {
            const stats = reviewStatsMap.get(pack.id);
            const works = worksMap.get(pack.id) || { works: 0, notWorks: 0 };

            return (
              <div key={pack.id} className="card p-6">
                <div className="flex flex-col lg:flex-row gap-6">
                  {/* Translation Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-4">
                      <span className="badge">
                        {t(`languages.${pack.sourceLang}` as never)} →{" "}
                        {t(`languages.${pack.targetLang}` as never)}
                      </span>
                      {pack.user && (
                        <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                          {pack.user.avatar ? (
                            <Image
                              src={pack.user.avatar}
                              alt={pack.user.name}
                              width={20}
                              height={20}
                              className="w-5 h-5 rounded-full"
                            />
                          ) : (
                            <User className="w-4 h-4" />
                          )}
                          {pack.user.name}
                        </div>
                      )}
                    </div>

                    {/* Stats row */}
                    <div className="flex flex-wrap items-center gap-4 text-sm text-[var(--text-muted)] mb-4">
                      {stats && (
                        <span className="flex items-center gap-1">
                          <Star className="w-4 h-4 text-yellow-500" />
                          {stats.avgRating.toFixed(1)}
                        </span>
                      )}
                      <span className="flex items-center gap-1 text-[var(--status-success)]">
                        <Check className="w-4 h-4" />
                        {works.works} {t("review.works.yes")}
                      </span>
                      <span className="flex items-center gap-1 text-[var(--status-error)]">
                        <X className="w-4 h-4" />
                        {works.notWorks} {t("review.works.no")}
                      </span>
                      <span className="flex items-center gap-1">
                        <MessageSquare className="w-4 h-4" />
                        {pack._count.reviews} {t("review.title")}
                      </span>
                    </div>

                    {/* Translation Pack Details (Flattened - no versions) */}
                    <div className="p-4 rounded-lg bg-[var(--bg-secondary)]">
                      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-medium text-[var(--text-primary)]">
                              {pack.modpackVersion}
                            </span>
                            <span className="text-xs text-[var(--text-muted)]">
                              {new Date(pack.createdAt).toLocaleDateString()}
                            </span>
                          </div>
                          <div className="flex flex-wrap gap-3 text-xs text-[var(--text-muted)]">
                            {/* Translation Type Badge */}
                            {pack.isManualTranslation ? (
                              <span className="flex items-center gap-1 text-blue-400">
                                <PenLine className="w-3 h-3" />
                                {t("translation.metadata.manualTranslation")}
                              </span>
                            ) : (
                              <span className="flex items-center gap-1 text-purple-400">
                                <Bot className="w-3 h-3" />
                                {t("translation.metadata.aiTranslation")}
                              </span>
                            )}
                            {/* AI-specific metadata */}
                            {!pack.isManualTranslation && pack.llmModel && (
                              <span className="flex items-center gap-1">
                                <ThermometerSun className="w-3 h-3" />
                                {pack.llmModel}
                                {pack.temperature !== null &&
                                  ` (${pack.temperature})`}
                              </span>
                            )}
                            {!pack.isManualTranslation && pack.batchSize && (
                              <span className="flex items-center gap-1">
                                <Layers className="w-3 h-3" />
                                Batch: {pack.batchSize}
                              </span>
                            )}
                            {!pack.isManualTranslation && pack.usedGlossary && (
                              <span className="flex items-center gap-1 text-[var(--accent-primary)]">
                                <BookOpen className="w-3 h-3" />
                                {t("translation.metadata.usedGlossary")}
                              </span>
                            )}
                            {pack.reviewed && (
                              <span className="flex items-center gap-1 text-[var(--status-success)]">
                                <CheckCircle className="w-3 h-3" />
                                {t("translation.metadata.reviewed")}
                              </span>
                            )}
                          </div>

                          {/* Translation Stats - 번역 통계가 있는 경우에만 표시 */}
                          {(pack.fileCount !== null || pack.totalEntries !== null || pack.totalTokens !== null || pack.durationSeconds !== null) && (
                            <div className="mt-3 pt-3 border-t border-[var(--border-secondary)]">
                              <div className="flex items-center gap-2 mb-2">
                                <BarChart3 className="w-3 h-3 text-[var(--accent-primary)]" />
                                <span className="text-xs font-medium text-[var(--text-secondary)]">
                                  {t("translation.stats.title")}
                                </span>
                              </div>
                              <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-[var(--text-muted)]">
                                {pack.fileCount !== null && (
                                  <span className="flex items-center gap-1">
                                    <FileText className="w-3 h-3" />
                                    {t("translation.stats.fileCount")}: {pack.fileCount.toLocaleString()}
                                  </span>
                                )}
                                {pack.totalEntries !== null && (
                                  <span className="flex items-center gap-1">
                                    <Hash className="w-3 h-3" />
                                    {t("translation.stats.totalEntries")}: {pack.totalEntries.toLocaleString()}
                                  </span>
                                )}
                                {pack.translatedEntries !== null && pack.totalEntries !== null && (
                                  <span className="flex items-center gap-1 text-[var(--status-success)]">
                                    <Check className="w-3 h-3" />
                                    {t("translation.stats.translatedEntries")}: {pack.translatedEntries.toLocaleString()}
                                    {" "}({((pack.translatedEntries / pack.totalEntries) * 100).toFixed(1)}%)
                                  </span>
                                )}
                                {pack.durationSeconds !== null && (
                                  <span className="flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {t("translation.stats.duration")}: {t("translation.stats.durationFormat", {
                                      minutes: Math.floor(pack.durationSeconds / 60),
                                      seconds: Math.round(pack.durationSeconds % 60)
                                    })}
                                  </span>
                                )}
                                {pack.totalTokens !== null && (
                                  <span className="flex items-center gap-1">
                                    <Cpu className="w-3 h-3" />
                                    {t("translation.stats.totalTokens")}: {pack.totalTokens.toLocaleString()}
                                    {pack.inputTokens !== null && pack.outputTokens !== null && (
                                      <span className="text-[var(--text-muted)]">
                                        ({pack.inputTokens.toLocaleString()} / {pack.outputTokens.toLocaleString()})
                                      </span>
                                    )}
                                  </span>
                                )}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Download buttons */}
                        <TranslationDownloadActions
                          packId={pack.id}
                          modpackId={modpack.id}
                          hasResourcePack={!!pack.resourcePackPath}
                          hasOverride={!!pack.overrideFilePath}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Write review link */}
                <div className="mt-4 pt-4 border-t border-[var(--border-secondary)]">
                  <Link
                    href={`/modpacks/${modpack.id}/review/${pack.id}`}
                    className="text-sm text-[var(--accent-primary)] hover:text-[var(--accent-hover)] transition-colors"
                  >
                    {t("review.writeReview")} →
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-16 glass rounded-xl">
          <p className="text-[var(--text-muted)] text-lg mb-4">
            {t("modpack.noTranslations")}
          </p>
          <Link href={`/upload?modpack=${modpack.curseforgeId}`}>
            <Button>{t("modpack.uploadTranslation")}</Button>
          </Link>
        </div>
      )}
    </div>
  );
}
