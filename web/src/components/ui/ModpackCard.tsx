"use client";

import { Link } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import { Download, Languages, User, ArrowUpRight } from "lucide-react";
import Image from "next/image";

interface ModpackCardProps {
  modpack: {
    id: number;
    name: string;
    slug: string;
    summary: string;
    logoUrl: string | null;
    author: string | null;
    totalDownloads: number;
    categories: string | null;
    _count?: {
      translationPacks: number;
    };
    translationPacks?: {
      targetLang: string;
      downloadCount: number;
      _count?: {
        reviews: number;
      };
    }[];
  };
}

export default function ModpackCard({ modpack }: ModpackCardProps) {
  const t = useTranslations();

  // Calculate total translation downloads
  const translationDownloads =
    modpack.translationPacks?.reduce(
      (sum, pack) => sum + (pack.downloadCount || 0),
      0
    ) || 0;

  // Get unique target languages
  const targetLanguages = [
    ...new Set(modpack.translationPacks?.map((p) => p.targetLang) || []),
  ];

  // Parse categories from JSON string
  let categories: { name: string; slug: string }[] = [];
  try {
    const parsed = modpack.categories
      ? (JSON.parse(modpack.categories) as { name: string; slug: string }[])
      : [];
    // Deduplicate categories by slug
    categories = parsed.filter(
      (category, index, self) =>
        index === self.findIndex((c) => c.slug === category.slug)
    );
  } catch {
    categories = [];
  }

  return (
    <Link href={`/modpacks/${modpack.id}`} className="block group">
      <article className="card p-5 h-full flex flex-col relative overflow-hidden">
        {/* Hover gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent-primary)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
        
        {/* Header */}
        <div className="flex gap-4 relative">
          {/* Logo */}
          <div className="flex-shrink-0">
            {modpack.logoUrl ? (
              <Image
                src={modpack.logoUrl}
                alt={modpack.name}
                width={72}
                height={72}
                className="w-[72px] h-[72px] rounded-xl object-cover ring-2 ring-[var(--border-primary)] group-hover:ring-[var(--accent-primary)]/30 transition-all"
                unoptimized={modpack.logoUrl.includes(".gif")}
              />
            ) : (
              <div className="w-[72px] h-[72px] rounded-xl bg-gradient-to-br from-[var(--accent-primary)]/20 to-[var(--bg-tertiary)] flex items-center justify-center ring-2 ring-[var(--border-primary)]">
                <span className="text-2xl font-bold text-[var(--accent-primary)]">
                  {modpack.name.charAt(0)}
                </span>
              </div>
            )}
          </div>

          {/* Title & Author */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] line-clamp-1 group-hover:text-[var(--accent-primary)] transition-colors">
                {modpack.name}
              </h3>
              <ArrowUpRight className="w-4 h-4 text-[var(--text-muted)] opacity-0 group-hover:opacity-100 transition-all group-hover:text-[var(--accent-primary)] flex-shrink-0" />
            </div>
            
            {modpack.author && (
              <p className="flex items-center gap-1.5 text-sm text-[var(--text-muted)] mt-1">
                <User className="w-3.5 h-3.5" />
                {modpack.author}
              </p>
            )}
            
            {/* Language badges */}
            {targetLanguages.length > 0 && (
              <div className="flex gap-1.5 mt-2 flex-wrap">
                {targetLanguages.slice(0, 3).map((lang) => (
                  <span
                    key={lang}
                    className="px-2 py-0.5 text-xs font-semibold rounded-md bg-[var(--status-info)]/12 text-[var(--status-info)] border border-[var(--status-info)]/20"
                    title={t(`languages.${lang}` as never)}
                  >
                    {lang.split("_")[0].toUpperCase()}
                  </span>
                ))}
                {targetLanguages.length > 3 && (
                  <span className="px-2 py-0.5 text-xs font-semibold rounded-md bg-[var(--bg-tertiary)] text-[var(--text-muted)]">
                    +{targetLanguages.length - 3}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Summary */}
        <p className="text-sm text-[var(--text-secondary)] line-clamp-2 mt-4 leading-relaxed flex-1">
          {modpack.summary}
        </p>

        {/* Categories */}
        {categories.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {categories.slice(0, 3).map((category) => (
              <span
                key={category.slug}
                className="px-2.5 py-1 text-xs font-medium rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-muted)] border border-[var(--border-secondary)]"
              >
                {category.name}
              </span>
            ))}
            {categories.length > 3 && (
              <span className="px-2.5 py-1 text-xs font-medium rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-muted)]">
                +{categories.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Stats */}
        <div className="flex items-center gap-6 mt-4 pt-4 border-t border-[var(--border-secondary)]">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-[var(--accent-primary)]/10">
              <Download className="w-4 h-4 text-[var(--accent-primary)]" />
            </div>
            <div>
              <span className="font-semibold text-[var(--text-primary)] stat-number">
                {translationDownloads.toLocaleString()}
              </span>
              <span className="text-xs text-[var(--text-muted)] ml-1">다운로드</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-[var(--status-info)]/10">
              <Languages className="w-4 h-4 text-[var(--status-info)]" />
            </div>
            <div>
              <span className="font-semibold text-[var(--text-primary)] stat-number">
                {modpack._count?.translationPacks || 0}
              </span>
              <span className="text-xs text-[var(--text-muted)] ml-1">{t("modpacks.card.translations")}</span>
            </div>
          </div>
        </div>
      </article>
    </Link>
  );
}
