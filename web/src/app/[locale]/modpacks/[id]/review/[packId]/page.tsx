import { getTranslations, setRequestLocale } from "next-intl/server";
import { prisma } from "@/lib/prisma";
import { notFound } from "next/navigation";
import ReviewClient from "@/components/ReviewClient";
import {
  BarChart3,
  FileText,
  Hash,
  Check,
  Clock,
  Cpu,
} from "lucide-react";

interface ReviewPageProps {
  params: Promise<{ locale: string; id: string; packId: string }>;
}

export default async function ReviewPage({ params }: ReviewPageProps) {
  const { locale, packId } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const pack = await prisma.translationPack.findUnique({
    where: { id: packId },
  });

  if (!pack) {
    notFound();
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 animate-fade-in">
      {/* Translation Stats */}
      {(pack.fileCount !== null || pack.totalEntries !== null || pack.totalTokens !== null || pack.durationSeconds !== null) && (
        <div className="glass rounded-xl p-6 mb-8">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-[var(--accent-primary)]" />
            <span className="text-lg font-bold text-[var(--text-primary)]">
              {t("translation.stats.title")}
            </span>
          </div>
          <div className="flex flex-col gap-2 text-sm text-[var(--text-secondary)]">
            {pack.fileCount !== null && (
              <span className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-[var(--text-muted)]" />
                {t("translation.stats.fileCount")}: {pack.fileCount.toLocaleString()}
              </span>
            )}
            {pack.totalEntries !== null && (
              <span className="flex items-center gap-2">
                <Hash className="w-4 h-4 text-[var(--text-muted)]" />
                {t("translation.stats.totalEntries")}: {pack.totalEntries.toLocaleString()}
              </span>
            )}
            {pack.translatedEntries !== null && pack.totalEntries !== null && (
              <span className="flex items-center gap-2">
                <Check className="w-4 h-4 text-[var(--status-success)]" />
                {t("translation.stats.translatedEntries")}: {pack.translatedEntries.toLocaleString()}
                <span className="text-[var(--text-muted)]">
                  ({((pack.translatedEntries / pack.totalEntries) * 100).toFixed(1)}%)
                </span>
              </span>
            )}
            {pack.durationSeconds !== null && (
              <span className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-[var(--text-muted)]" />
                {t("translation.stats.duration")}: {t("translation.stats.durationFormat", {
                  minutes: Math.floor(pack.durationSeconds / 60),
                  seconds: Math.round(pack.durationSeconds % 60)
                })}
              </span>
            )}
            {pack.totalTokens !== null && (
              <div className="flex flex-col gap-1">
                <span className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-[var(--text-muted)]" />
                  {t("translation.stats.totalTokens")}: {pack.totalTokens.toLocaleString()}
                </span>
                {pack.inputTokens !== null && pack.outputTokens !== null && (
                  <span className="text-xs text-[var(--text-muted)] pl-6">
                    ({pack.inputTokens.toLocaleString()} / {pack.outputTokens.toLocaleString()})
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      <ReviewClient packId={packId} />
    </div>
  );
}
