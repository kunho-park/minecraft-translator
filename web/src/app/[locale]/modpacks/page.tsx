import { getTranslations, setRequestLocale } from "next-intl/server";
import { prisma } from "@/lib/prisma";
import { Prisma } from "@prisma/client";
import { Package } from "lucide-react";
import ModpackCard from "@/components/ui/ModpackCard";
import ModpackFilters from "./ModpackFilters";
import type { Metadata } from "next";

// Force dynamic rendering (no static generation)
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "모드팩 목록",
  description:
    "번역된 마인크래프트 모드팩 목록입니다. 원하는 모드팩의 한글패치를 검색하고 다운로드하세요.",
};

interface ModpacksPageProps {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{
    q?: string;
    sort?: string;
    lang?: string;
    tags?: string;
  }>;
}

export default async function ModpacksPage({
  params,
  searchParams,
}: ModpacksPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();
  const search = await searchParams;

  const query = search.q || "";
  const sortBy = search.sort || "latest";
  const langFilter = search.lang || "";
  const tagsFilter = search.tags ? search.tags.split(",") : [];

  // Build where clause for Modpack
  const whereClause: Prisma.ModpackWhereInput = {
    translationPacks: {
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
    ...(tagsFilter.length > 0
      ? {
        AND: tagsFilter.map((tag) => ({
          categories: { contains: tag },
        })),
      }
      : {}),
  };

  let modpacks: any[] = [];

  if (sortBy === "latest") {
    // For 'latest' sort, we want to sort by the creation time of the TranslationPack,
    // not the Modpack's cachedAt time.
    const packs = await prisma.translationPack.findMany({
      where: {
        status: "approved",
        ...(langFilter ? { targetLang: langFilter } : {}),
        modpack: whereClause,
      },
      orderBy: { createdAt: "desc" },
      distinct: ["modpackId"],
      take: 50,
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
    modpacks = packs.map((p) => p.modpack);
  } else {
    // For other sorts (name, downloads), we query Modpack directly
    modpacks = await prisma.modpack.findMany({
      where: whereClause,
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
      orderBy:
        sortBy === "downloads"
          ? { totalDownloads: "desc" }
          : { name: "asc" },
      take: 50,
    });
  }

  // If sorting by translation downloads, do it in JS (existing logic)
  let sortedModpacks = modpacks;
  if (sortBy === "downloads") {
    sortedModpacks = [...modpacks].sort((a, b) => {
      const aDownloads = a.translationPacks.reduce(
        (sum: number, tp: any) => sum + (tp.downloadCount || 0),
        0
      );
      const bDownloads = b.translationPacks.reduce(
        (sum: number, tp: any) => sum + (tp.downloadCount || 0),
        0
      );
      return bDownloads - aDownloads;
    });
  }

  // Get available languages
  const languages = await prisma.translationPack.findMany({
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
            <Package className="w-6 h-6 text-[var(--accent-primary)]" />
          </div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">
            {t("modpacks.title")}
          </h1>
        </div>
        <p className="text-[var(--text-secondary)] ml-[60px]">
          {sortedModpacks.length}개의 모드팩에서 번역을 찾아보세요
        </p>
      </div>

      {/* Filters */}
      <ModpackFilters
        query={query}
        sortBy={sortBy}
        langFilter={langFilter}
        tagsFilter={tagsFilter}
        availableLanguages={availableLanguages}
      />

      {/* Results */}
      {sortedModpacks.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedModpacks.map((modpack, i) => (
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
          <Package className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-4" />
          <p className="text-lg text-[var(--text-muted)]">
            {t("modpacks.noResults")}
          </p>
          <p className="text-sm text-[var(--text-muted)] mt-2">
            검색어나 필터를 변경해보세요
          </p>
        </div>
      )}
    </div>
  );
}
