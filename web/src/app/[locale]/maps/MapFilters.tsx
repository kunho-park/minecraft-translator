"use client";

import { useTranslations } from "next-intl";
import { Search, Languages, ArrowUpDown, Sparkles } from "lucide-react";
import { useRouter, usePathname } from "@/i18n/navigation";
import { useState, useTransition } from "react";

interface MapFiltersProps {
    query: string;
    sortBy: string;
    langFilter: string;
    availableLanguages: string[];
}

export default function MapFilters({
    query,
    sortBy,
    langFilter,
    availableLanguages,
}: MapFiltersProps) {
    const t = useTranslations();
    const router = useRouter();
    const pathname = usePathname();
    const [isPending, startTransition] = useTransition();

    const [searchQuery, setSearchQuery] = useState(query);
    const [selectedSort, setSelectedSort] = useState(sortBy);
    const [selectedLang, setSelectedLang] = useState(langFilter);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        const params = new URLSearchParams();
        if (searchQuery) params.set("q", searchQuery);
        if (selectedSort !== "latest") params.set("sort", selectedSort);
        if (selectedLang) params.set("lang", selectedLang);

        startTransition(() => {
            router.push(`${pathname}?${params.toString()}`);
        });
    };

    return (
        <div className="mb-8">
            <form onSubmit={handleSubmit} className="space-y-4">
                <div className="flex flex-col lg:flex-row gap-3">
                    {/* Search */}
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-muted)] pointer-events-none" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder={t("common.searchPlaceholder")}
                            className="w-full py-3 rounded-xl bg-[var(--bg-card)] border border-[var(--border-primary)] focus:border-[var(--accent-primary)] focus:ring-2 focus:ring-[var(--accent-primary)]/20 transition-all text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
                            style={{ paddingLeft: "2.75rem", paddingRight: "1rem" }}
                        />
                    </div>

                    {/* Language Filter */}
                    <div className="relative">
                        <Languages className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)] pointer-events-none z-10" />
                        <select
                            value={selectedLang}
                            onChange={(e) => setSelectedLang(e.target.value)}
                            className="pr-10 py-3 rounded-xl bg-[var(--bg-card)] border border-[var(--border-primary)] appearance-none cursor-pointer min-w-[160px] focus:border-[var(--accent-primary)] focus:ring-2 focus:ring-[var(--accent-primary)]/20 transition-all text-[var(--text-primary)]"
                            style={{ paddingLeft: "2.5rem" }}
                        >
                            <option value="">{t("modpacks.filters.language")}</option>
                            {availableLanguages.map((lang) => (
                                <option key={lang} value={lang}>
                                    {t(`languages.${lang}` as never)}
                                </option>
                            ))}
                        </select>
                        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                            <svg className="w-4 h-4 text-[var(--text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                        </div>
                    </div>

                    {/* Sort */}
                    <div className="relative">
                        <ArrowUpDown className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)] pointer-events-none z-10" />
                        <select
                            value={selectedSort}
                            onChange={(e) => setSelectedSort(e.target.value)}
                            className="pr-10 py-3 rounded-xl bg-[var(--bg-card)] border border-[var(--border-primary)] appearance-none cursor-pointer min-w-[160px] focus:border-[var(--accent-primary)] focus:ring-2 focus:ring-[var(--accent-primary)]/20 transition-all text-[var(--text-primary)]"
                            style={{ paddingLeft: "2.5rem" }}
                        >
                            <option value="latest">{t("modpacks.filters.latest")}</option>
                            <option value="downloads">
                                {t("modpacks.filters.downloads")}
                            </option>
                        </select>
                        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                            <svg className="w-4 h-4 text-[var(--text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                        </div>
                    </div>

                    {/* Submit */}
                    <button
                        type="submit"
                        disabled={isPending}
                        className="px-6 py-3 bg-[var(--accent-primary)] text-white rounded-xl font-semibold hover:bg-[var(--accent-secondary)] transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-[var(--accent-primary)]/20 hover:shadow-[var(--accent-primary)]/30 flex items-center justify-center gap-2"
                    >
                        {isPending ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <Sparkles className="w-4 h-4" />
                        )}
                        {isPending ? t("common.loading") : t("common.search")}
                    </button>
                </div>
            </form>
        </div>
    );
}
