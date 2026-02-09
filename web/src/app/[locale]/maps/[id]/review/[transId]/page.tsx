import { setRequestLocale } from "next-intl/server";
import { prisma } from "@/lib/prisma";
import { notFound } from "next/navigation";
import MapReviewClient from "@/components/MapReviewClient";

interface MapReviewPageProps {
  params: Promise<{ locale: string; id: string; transId: string }>;
}

export default async function MapReviewPage({ params }: MapReviewPageProps) {
  const { locale, transId } = await params;
  setRequestLocale(locale);

  const translation = await prisma.mapTranslation.findUnique({
    where: { id: transId },
    include: {
      map: { select: { name: true } },
    },
  });

  if (!translation) {
    notFound();
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 animate-fade-in">
      {/* Translation Info */}
      <div className="glass rounded-xl p-6 mb-8">
        <div className="text-sm text-[var(--text-muted)] mb-1">{translation.map.name}</div>
        <div className="flex items-center gap-3 text-[var(--text-secondary)]">
          <span className="font-medium text-[var(--text-primary)]">{translation.version}</span>
          <span className="badge">
            {translation.sourceLang} → {translation.targetLang}
          </span>
          {translation.minecraftVersion && (
            <span className="text-xs text-emerald-400">MC {translation.minecraftVersion}</span>
          )}
        </div>
      </div>

      <MapReviewClient mapTranslationId={transId} />
    </div>
  );
}
