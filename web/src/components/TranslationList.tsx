"use client";

import { useTranslations } from "next-intl";
import { useState, useMemo } from "react";
import Image from "next/image";
import { Link } from "@/i18n/navigation";
import {
  User,
  Star,
  Check,
  X,
  MessageSquare,
  PenLine,
  Bot,
  ThermometerSun,
  Layers,
  BookOpen,
  CheckCircle,
  BarChart3,
  FileText,
  Hash,
  Clock,
  Cpu,
  Download,
  ThumbsUp,
  Filter,
  ArrowUpDown
} from "lucide-react";
import Button from "@/components/ui/Button";
import TranslationDownloadActions from "@/components/TranslationDownloadActions";

export interface TranslationPack {
  id: string;
  sourceLang: string;
  targetLang: string;
  modpackVersion: string;
  createdAt: string;
  isManualTranslation: boolean;
  llmModel: string | null;
  temperature: number | null;
  batchSize: number | null;
  usedGlossary: boolean;
  reviewed: boolean;
  downloadCount: number;
  resourcePackPath: string | null;
  overrideFilePath: string | null;
  fileCount: number | null;
  totalEntries: number | null;
  translatedEntries: number | null;
  durationSeconds: number | null;
  totalTokens: number | null;
  inputTokens: number | null;
  outputTokens: number | null;
  handlerStats: string | null;
  user: {
    name: string;
    avatar: string | null;
  } | null;
  _count: {
    reviews: number;
  };
}

export interface ReviewStats {
  avgRating: number;
}

export interface WorksStats {
  works: number;
  notWorks: number;
}

interface TranslationListProps {
  initialPacks: TranslationPack[];
  reviewStats: Record<string, ReviewStats>;
  worksStats: Record<string, WorksStats>;
  modpackId: number;
  modpackCurseforgeId: number;
}

export default function TranslationList({
  initialPacks,
  reviewStats,
  worksStats,
  modpackId,
  modpackCurseforgeId
}: TranslationListProps) {
  const t = useTranslations();
  const [sortBy, setSortBy] = useState<"latest" | "downloads" | "rating" | "recommended" | "version">("recommended");
  const [filterVersion, setFilterVersion] = useState<string>("all");

  // Helper for semantic version comparison
  const compareVersions = (v1: string, v2: string) => {
    const cleanV1 = v1.replace(/^v/i, '');
    const cleanV2 = v2.replace(/^v/i, '');
    return cleanV1.localeCompare(cleanV2, undefined, { numeric: true, sensitivity: 'base' });
  };

  // Get unique versions
  const versions = useMemo(() => {
    const v = new Set(initialPacks.map(p => p.modpackVersion));
    return Array.from(v).sort((a, b) => compareVersions(b, a));
  }, [initialPacks]);

  // Recommended logic (global)
  const recommendedPackId = useMemo(() => {
    if (initialPacks.length === 0) return null;

    // Sort by version (desc) then by date (desc) to find true latest version
    const sortedByVersionAndDate = [...initialPacks].sort((a, b) => {
      const versionDiff = compareVersions(b.modpackVersion, a.modpackVersion);
      if (versionDiff !== 0) return versionDiff;
      return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
    });

    const latestVersion = sortedByVersionAndDate[0].modpackVersion;

    const candidates = initialPacks.filter(p => p.modpackVersion === latestVersion);

    const sortedCandidates = candidates.sort((a, b) => {
      const ratingA = reviewStats[a.id]?.avgRating || 0;
      const ratingB = reviewStats[b.id]?.avgRating || 0;
      if (ratingB !== ratingA) return ratingB - ratingA;

      // If rating equal, use download count
      if (b.downloadCount !== a.downloadCount) return b.downloadCount - a.downloadCount;

      const worksA = worksStats[a.id]?.works || 0;
      const worksB = worksStats[b.id]?.works || 0;
      return worksB - worksA;
    });

    return sortedCandidates[0]?.id || null;
  }, [initialPacks, reviewStats, worksStats]);

  // Filter logic
  const filteredPacks = useMemo(() => {
    if (filterVersion === "all") return initialPacks;
    return initialPacks.filter(p => p.modpackVersion === filterVersion);
  }, [initialPacks, filterVersion]);

  // Sort logic
  const sortedPacks = useMemo(() => {
    let sorted = [...filteredPacks];

    switch (sortBy) {
      case "latest":
        sorted.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
        break;
      case "downloads":
        sorted.sort((a, b) => b.downloadCount - a.downloadCount);
        break;
      case "rating":
        sorted.sort((a, b) => {
          const ratingA = reviewStats[a.id]?.avgRating || 0;
          const ratingB = reviewStats[b.id]?.avgRating || 0;
          if (ratingB !== ratingA) return ratingB - ratingA;
          return 0;
        });
        break;
      case "version":
        sorted.sort((a, b) => compareVersions(b.modpackVersion, a.modpackVersion));
        break;
      case "recommended":
        if (recommendedPackId) {
          sorted.sort((a, b) => {
            if (a.id === recommendedPackId) return -1;
            if (b.id === recommendedPackId) return 1;
            // Fallback sort: Version desc -> Date desc
            const versionDiff = compareVersions(b.modpackVersion, a.modpackVersion);
            if (versionDiff !== 0) return versionDiff;
            return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
          });
        } else {
          // Fallback sort: Version desc -> Date desc
          sorted.sort((a, b) => {
            const versionDiff = compareVersions(b.modpackVersion, a.modpackVersion);
            if (versionDiff !== 0) return versionDiff;
            return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
          });
        }
        break;
    }
    return sorted;
  }, [filteredPacks, sortBy, recommendedPackId, reviewStats]);

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <h2 className="text-2xl font-bold text-[var(--text-primary)]">
          {t("modpack.translations")}
        </h2>

        <div className="flex flex-wrap items-center gap-3">
          {/* Version Filter */}
          <div className="flex items-center gap-2 bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-lg px-3 py-1.5 transition-colors focus-within:ring-2 focus-within:ring-[var(--accent-primary)]">
            <Filter className="w-4 h-4 text-[var(--text-secondary)]" />
            <select
              value={filterVersion}
              onChange={(e) => setFilterVersion(e.target.value)}
              className="bg-transparent text-sm text-[var(--text-primary)] focus:outline-none min-w-[100px]"
            >
              <option value="all">{t("modpack.filter.allVersions")}</option>
              {versions.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>

          <div className="w-px h-6 bg-[var(--border-secondary)] hidden sm:block" />

          {/* Sort */}
          <div className="flex items-center gap-2 bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-lg px-3 py-1.5 transition-colors focus-within:ring-2 focus-within:ring-[var(--accent-primary)]">
            <ArrowUpDown className="w-4 h-4 text-[var(--text-secondary)]" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-transparent text-sm text-[var(--text-primary)] focus:outline-none min-w-[100px]"
            >
              <option value="recommended">{t("modpack.sort.recommended")}</option>
              <option value="latest">{t("modpack.sort.latest")}</option>
              <option value="version">{t("modpack.sort.version")}</option>
              <option value="downloads">{t("modpack.sort.downloads")}</option>
              <option value="rating">{t("modpack.sort.rating")}</option>
            </select>
          </div>
        </div>
      </div>

      {sortedPacks.length > 0 ? (
        <div className="space-y-6">
          {sortedPacks.map((pack) => {
            const stats = reviewStats[pack.id];
            const works = worksStats[pack.id] || { works: 0, notWorks: 0 };
            const isRecommended = pack.id === recommendedPackId;

            return (
              <div key={pack.id} className={`card p-6 transition-all duration-200 ${isRecommended ? 'ring-2 ring-[var(--accent-primary)] bg-[var(--accent-primary)]/5 shadow-md shadow-[var(--accent-primary)]/10' : 'hover:border-[var(--accent-primary)]/50'}`}>
                {isRecommended && (
                  <div className="mb-4 animate-fade-in">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--accent-primary)] text-white text-xs font-bold shadow-sm">
                      <ThumbsUp className="w-3 h-3" />
                      {t("modpack.recommended.badge")}
                    </span>
                    <span className="ml-2 text-xs text-[var(--accent-primary)] font-medium">
                      {t("modpack.recommended.reason")}
                    </span>
                  </div>
                )}
                <div className="flex flex-col lg:flex-row gap-6">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-4">
                      <span className="badge">
                        {t(`languages.${pack.sourceLang}` as any)} →{" "}
                        {t(`languages.${pack.targetLang}` as any)}
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

                    <div className="flex flex-wrap items-center gap-4 text-sm text-[var(--text-muted)] mb-4">
                      <span className="flex items-center gap-1">
                        <Download className="w-4 h-4" />
                        {pack.downloadCount.toLocaleString()}
                      </span>
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

                        <TranslationDownloadActions
                          packId={pack.id}
                          modpackId={modpackId}
                          resourcePackUrl={pack.resourcePackPath}
                          overrideFileUrl={pack.overrideFilePath}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-[var(--border-secondary)]">
                  <Link
                    href={`/modpacks/${modpackId}/review/${pack.id}`}
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
          <Link href={`/upload?modpack=${modpackCurseforgeId}`}>
            <Button>{t("modpack.uploadTranslation")}</Button>
          </Link>
        </div>
      )}
    </div>
  );
}
