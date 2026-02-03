import { getTranslations, setRequestLocale } from "next-intl/server";
import { prisma } from "@/lib/prisma";
import { Prisma } from "@prisma/client";
import { Globe } from "lucide-react";
import MapCard from "@/components/ui/MapCard";
import MapFilters from "./MapFilters";
import type { Metadata } from "next";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
    title: "맵 목록",
    description: "번역된 마인크래프트 맵 목록입니다.",
};

interface MapsPageProps {
    params: Promise<{ locale: string }>;
    searchParams: Promise<{
        q?: string;
        sort?: string;
        lang?: string;
    }>;
}

export default async function MapsPage({
    params,
    searchParams,
}: MapsPageProps) {
    const { locale } = await params;
    setRequestLocale(locale);
    const t = await getTranslations();
    const search = await searchParams;

    const query = search.q || "";
    const sortBy = search.sort || "latest";
    const langFilter = search.lang || "";

    // Build where clause for Map
    const whereClause: Prisma.MapWhereInput = {
        translations: {
            some: {
                status: "approved",
                ...(langFilter ? { targetLang: langFilter } : {}),
            },
        },
        ...(query
            ? {
                OR: [
                    { name: { contains: query } },
                    { summary: { contains: query } },
                    { author: { contains: query } },
                ],
            }
            : {}),
    };

    let maps: any[] = [];

    if (sortBy === "latest") {
        // Sort by latest translation
        const translations = await prisma.mapTranslation.findMany({
            where: {
                status: "approved",
                ...(langFilter ? { targetLang: langFilter } : {}),
                map: whereClause,
            },
            orderBy: { createdAt: "desc" },
            distinct: ["mapId"],
            take: 50,
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
        maps = translations.map((t) => t.map);
    } else {
        // Sort by name or downloads (if we had total downloads on Map, but we don't yet. We can sum them up in JS or just sort by name)
        maps = await prisma.map.findMany({
            where: whereClause,
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
            orderBy: { name: "asc" },
            take: 50,
        });
    }

    // Sort by downloads if needed
    if (sortBy === "downloads") {
        maps.sort((a, b) => {
            const aDownloads = a.translations.reduce(
                (sum: number, t: any) => sum + (t.downloadCount || 0),
                0
            );
            const bDownloads = b.translations.reduce(
                (sum: number, t: any) => sum + (t.downloadCount || 0),
                0
            );
            return bDownloads - aDownloads;
        });
    }

    // Get available languages
    const languages = await prisma.mapTranslation.findMany({
        where: { status: "approved" },
        select: { targetLang: true },
        distinct: ["targetLang"],
    });
    const availableLanguages = languages.map((l) => l.targetLang);

    return (
        <div className="max-w-7xl mx-auto px-4 py-10 animate-fade-in">
            {/* Header */}
            <div className="mb-10">
                <div className="flex items-center gap-4 mb-3">
                    <div className="p-3 rounded-xl bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/20">
                        <Globe className="w-6 h-6 text-[var(--accent-primary)]" />
                    </div>
                    <h1 className="text-3xl font-bold text-[var(--text-primary)]">
                        {t("maps.title")}
                    </h1>
                </div>
                <p className="text-[var(--text-secondary)] ml-[60px]">
                    {maps.length}개의 맵에서 번역을 찾아보세요
                </p>
            </div>

            {/* Filters */}
            <MapFilters
                query={query}
                sortBy={sortBy}
                langFilter={langFilter}
                availableLanguages={availableLanguages}
            />

            {/* Results */}
            {maps.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {maps.map((map, i) => (
                        <div
                            key={map.id}
                            className={`animate-fade-in stagger-${(i % 5) + 1}`}
                            style={{ opacity: 0 }}
                        >
                            <MapCard map={map} />
                        </div>
                    ))}
                </div>
            ) : (
                <div className="text-center py-20 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-secondary)]">
                    <Globe className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-4" />
                    <p className="text-lg text-[var(--text-muted)]">
                        {t("maps.noResults")}
                    </p>
                    <p className="text-sm text-[var(--text-muted)] mt-2">
                        검색어나 필터를 변경해보세요
                    </p>
                </div>
            )}
        </div>
    );
}
