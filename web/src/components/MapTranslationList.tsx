"use client";

import { useTranslations } from "next-intl";
import { useState, useMemo } from "react";
import Image from "next/image";
import { Link } from "@/i18n/navigation";
import {
    User,
    Download,
    Calendar,
    Filter,
    ArrowUpDown
} from "lucide-react";
import Button from "@/components/ui/Button";
import MapTranslationDownloadActions from "./MapTranslationDownloadActions";

export interface MapTranslation {
    id: string;
    version: string;
    sourceLang: string;
    targetLang: string;
    status: string;
    resourcePackUrl: string | null;
    overrideFileUrl: string | null;
    downloadCount: number;
    createdAt: string;
    user: {
        name: string;
        avatar: string | null;
    } | null;
}

interface MapTranslationListProps {
    initialTranslations: MapTranslation[];
    mapId: number;
}

export default function MapTranslationList({
    initialTranslations,
    mapId,
}: MapTranslationListProps) {
    const t = useTranslations();
    const [sortBy, setSortBy] = useState<"latest" | "downloads" | "version">("latest");
    const [filterVersion, setFilterVersion] = useState<string>("all");

    // Helper for semantic version comparison
    const compareVersions = (v1: string, v2: string) => {
        const cleanV1 = v1.replace(/^v/i, '');
        const cleanV2 = v2.replace(/^v/i, '');
        return cleanV1.localeCompare(cleanV2, undefined, { numeric: true, sensitivity: 'base' });
    };

    // Get unique versions
    const versions = useMemo(() => {
        const v = new Set(initialTranslations.map(p => p.version));
        return Array.from(v).sort((a, b) => compareVersions(b, a));
    }, [initialTranslations]);

    // Filter logic
    const filteredTranslations = useMemo(() => {
        if (filterVersion === "all") return initialTranslations;
        return initialTranslations.filter(p => p.version === filterVersion);
    }, [initialTranslations, filterVersion]);

    // Sort logic
    const sortedTranslations = useMemo(() => {
        let sorted = [...filteredTranslations];

        switch (sortBy) {
            case "latest":
                sorted.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
                break;
            case "downloads":
                sorted.sort((a, b) => b.downloadCount - a.downloadCount);
                break;
            case "version":
                sorted.sort((a, b) => compareVersions(b.version, a.version));
                break;
        }
        return sorted;
    }, [filteredTranslations, sortBy]);

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
                            <option value="latest">{t("modpack.sort.latest")}</option>
                            <option value="version">{t("modpack.sort.version")}</option>
                            <option value="downloads">{t("modpack.sort.downloads")}</option>
                        </select>
                    </div>
                </div>
            </div>

            {sortedTranslations.length > 0 ? (
                <div className="space-y-6">
                    {sortedTranslations.map((trans) => (
                        <div key={trans.id} className="card p-6 hover:border-[var(--accent-primary)]/50 transition-all duration-200">
                            <div className="flex flex-col lg:flex-row gap-6">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-4">
                                        <span className="badge">
                                            {t(`languages.${trans.sourceLang}` as any)} →{" "}
                                            {t(`languages.${trans.targetLang}` as any)}
                                        </span>
                                        {trans.user && (
                                            <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                                                {trans.user.avatar ? (
                                                    <Image
                                                        src={trans.user.avatar}
                                                        alt={trans.user.name}
                                                        width={20}
                                                        height={20}
                                                        className="w-5 h-5 rounded-full"
                                                    />
                                                ) : (
                                                    <User className="w-4 h-4" />
                                                )}
                                                {trans.user.name}
                                            </div>
                                        )}
                                    </div>

                                    <div className="flex flex-wrap items-center gap-4 text-sm text-[var(--text-muted)] mb-4">
                                        <span className="flex items-center gap-1">
                                            <Download className="w-4 h-4" />
                                            {trans.downloadCount.toLocaleString()}
                                        </span>
                                        <span className="flex items-center gap-1">
                                            <Calendar className="w-4 h-4" />
                                            {new Date(trans.createdAt).toLocaleDateString()}
                                        </span>
                                    </div>

                                    <div className="p-4 rounded-lg bg-[var(--bg-secondary)] flex items-center justify-between">
                                        <div>
                                            <div className="font-medium text-[var(--text-primary)] mb-1">
                                                {trans.version}
                                            </div>
                                        </div>
                                        <MapTranslationDownloadActions
                                            translationId={trans.id}
                                            hasResourcePack={!!trans.resourcePackUrl}
                                            hasOverride={!!trans.overrideFileUrl}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="text-center py-16 glass rounded-xl">
                    <p className="text-[var(--text-muted)] text-lg mb-4">
                        {t("modpack.noTranslations")}
                    </p>
                    <Link href="/upload">
                        <Button>{t("maps.uploadTranslation")}</Button>
                    </Link>
                </div>
            )}
        </div>
    );
}
