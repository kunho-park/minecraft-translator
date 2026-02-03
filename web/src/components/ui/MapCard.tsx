"use client";

import { Link } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import { Download, Languages, User, ArrowUpRight } from "lucide-react";
import Image from "next/image";

interface MapCardProps {
    map: {
        id: number;
        name: string;
        slug: string;
        summary: string;
        thumbnailUrl: string | null;
        author: string | null;
        _count?: {
            translations: number;
        };
        translations?: {
            targetLang: string;
            downloadCount: number;
        }[];
    };
}

export default function MapCard({ map }: MapCardProps) {
    const t = useTranslations();

    // Calculate total translation downloads
    const translationDownloads =
        map.translations?.reduce(
            (sum, trans) => sum + (trans.downloadCount || 0),
            0
        ) || 0;

    // Get unique target languages
    const targetLanguages = [
        ...new Set(map.translations?.map((t) => t.targetLang) || []),
    ];

    return (
        <Link href={`/maps/${map.id}`} className="block group">
            <article className="card p-5 h-full flex flex-col relative overflow-hidden">
                {/* Hover gradient overlay */}
                <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent-primary)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

                {/* Header */}
                <div className="flex gap-4 relative">
                    {/* Logo */}
                    <div className="flex-shrink-0">
                        {map.thumbnailUrl ? (
                            <Image
                                src={map.thumbnailUrl}
                                alt={map.name}
                                width={72}
                                height={72}
                                className="w-[72px] h-[72px] rounded-xl object-cover ring-2 ring-[var(--border-primary)] group-hover:ring-[var(--accent-primary)]/30 transition-all"
                            />
                        ) : (
                            <div className="w-[72px] h-[72px] rounded-xl bg-gradient-to-br from-[var(--accent-primary)]/20 to-[var(--bg-tertiary)] flex items-center justify-center ring-2 ring-[var(--border-primary)]">
                                <span className="text-2xl font-bold text-[var(--accent-primary)]">
                                    {map.name.charAt(0)}
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Title & Author */}
                    <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                            <h3 className="text-lg font-semibold text-[var(--text-primary)] line-clamp-1 group-hover:text-[var(--accent-primary)] transition-colors">
                                {map.name}
                            </h3>
                            <ArrowUpRight className="w-4 h-4 text-[var(--text-muted)] opacity-0 group-hover:opacity-100 transition-all group-hover:text-[var(--accent-primary)] flex-shrink-0" />
                        </div>

                        {map.author && (
                            <p className="flex items-center gap-1.5 text-sm text-[var(--text-muted)] mt-1">
                                <User className="w-3.5 h-3.5" />
                                {map.author}
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
                    {map.summary}
                </p>

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
                                {map._count?.translations || 0}
                            </span>
                            <span className="text-xs text-[var(--text-muted)] ml-1">{t("modpacks.card.translations")}</span>
                        </div>
                    </div>
                </div>
            </article>
        </Link>
    );
}
