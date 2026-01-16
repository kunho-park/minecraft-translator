import { getTranslations, setRequestLocale } from "next-intl/server";
import { FileArchive, FolderCog, AlertTriangle, Info, Terminal, Monitor, Folder } from "lucide-react";

interface GuidePageProps {
  params: Promise<{ locale: string }>;
}

export default async function GuidePage({ params }: GuidePageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("guide.apply");

  return (
    <div className="container mx-auto px-4 py-12 max-w-4xl animate-fade-in">
      <h1 className="text-3xl font-bold mb-8 text-[var(--text-primary)]">{t("title")}</h1>

      <div className="space-y-8">
        {/* Resource Pack Section */}
        <section className="bg-[var(--bg-card)] rounded-xl border border-[var(--border-primary)] overflow-hidden shadow-sm">
          <div className="p-6 border-b border-[var(--border-secondary)] bg-[var(--bg-secondary)]/50">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 text-blue-500 rounded-lg">
                <FileArchive className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-semibold text-[var(--text-primary)]">{t("resourcePack.title")}</h2>
            </div>
          </div>
          <div className="p-6 space-y-4">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[var(--bg-secondary)] flex items-center justify-center font-bold text-[var(--text-secondary)] border border-[var(--border-secondary)]">1</div>
              <p className="text-[var(--text-secondary)] pt-1">{t("resourcePack.step1")}</p>
            </div>
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[var(--bg-secondary)] flex items-center justify-center font-bold text-[var(--text-secondary)] border border-[var(--border-secondary)]">2</div>
              <p className="text-[var(--text-secondary)] pt-1">{t("resourcePack.step2")}</p>
            </div>
            <div className="mt-4 p-4 bg-blue-500/5 border border-blue-500/10 rounded-lg flex gap-3">
              <Info className="w-5 h-5 text-blue-500 flex-shrink-0" />
              <p className="text-sm text-blue-600 dark:text-blue-400">{t("resourcePack.tip")}</p>
            </div>
          </div>
        </section>

        {/* Override File Section */}
        <section className="bg-[var(--bg-card)] rounded-xl border border-[var(--border-primary)] overflow-hidden shadow-sm">
          <div className="p-6 border-b border-[var(--border-secondary)] bg-[var(--bg-secondary)]/50">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-500/10 text-amber-500 rounded-lg">
                <FolderCog className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-[var(--text-primary)]">{t("override.title")}</h2>
                <p className="text-sm text-[var(--text-secondary)] mt-1">{t("override.description")}</p>
              </div>
            </div>
          </div>
          
          <div className="p-6 space-y-8">
            {/* CurseForge Instructions */}
            <div className="bg-[var(--bg-secondary)]/30 rounded-xl p-5 border border-[var(--border-secondary)]/50">
              <h3 className="flex items-center gap-2 text-lg font-semibold text-[var(--text-primary)] mb-4">
                <Monitor className="w-5 h-5 text-[var(--accent-primary)]" />
                {t("override.curseforge.title")}
              </h3>
              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[var(--bg-card)] flex items-center justify-center font-bold text-[var(--text-secondary)] border border-[var(--border-secondary)] shadow-sm">1</div>
                  <p className="text-[var(--text-secondary)] pt-1">{t("override.curseforge.step1")}</p>
                </div>
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[var(--bg-card)] flex items-center justify-center font-bold text-[var(--text-secondary)] border border-[var(--border-secondary)] shadow-sm">2</div>
                  <p className="text-[var(--text-secondary)] pt-1">{t("override.curseforge.step2")}</p>
                </div>
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[var(--bg-card)] flex items-center justify-center font-bold text-[var(--text-secondary)] border border-[var(--border-secondary)] shadow-sm">3</div>
                  <p className="text-[var(--text-secondary)] pt-1">{t("override.curseforge.step3")}</p>
                </div>
              </div>
            </div>

            {/* Other Launchers */}
            <div className="bg-[var(--bg-secondary)]/30 rounded-xl p-5 border border-[var(--border-secondary)]/50">
              <h3 className="flex items-center gap-2 text-lg font-semibold text-[var(--text-primary)] mb-4">
                <Folder className="w-5 h-5 text-[var(--accent-primary)]" />
                {t("override.otherLaunchers.title")}
              </h3>
              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[var(--bg-card)] flex items-center justify-center font-bold text-[var(--text-secondary)] border border-[var(--border-secondary)] shadow-sm">1</div>
                  <p className="text-[var(--text-secondary)] pt-1">{t("override.otherLaunchers.step1")}</p>
                </div>
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[var(--bg-card)] flex items-center justify-center font-bold text-[var(--text-secondary)] border border-[var(--border-secondary)] shadow-sm">2</div>
                  <p className="text-[var(--text-secondary)] pt-1">{t("override.otherLaunchers.step2")}</p>
                </div>
              </div>
            </div>

            {/* Warning Section */}
            <div className="p-4 bg-red-500/5 border border-red-500/10 rounded-lg space-y-3">
              <div className="flex items-center gap-2 text-red-600 dark:text-red-400 font-medium">
                <AlertTriangle className="w-5 h-5" />
                {t("override.warning.title")}
              </div>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                {t("override.warning.content")}
              </p>
              <div className="text-sm font-medium text-red-600 dark:text-red-400">
                {t("override.warning.backup")}
              </div>
              <p className="text-sm text-[var(--text-secondary)]">
                {t("override.warning.troubleshoot")}
              </p>
            </div>

            {/* Technical Details */}
            <div className="pt-4 border-t border-[var(--border-secondary)]">
              <div className="flex items-start gap-3">
                <Terminal className="w-5 h-5 text-[var(--text-muted)] mt-1" />
                <div>
                  <h4 className="font-medium text-[var(--text-primary)]">{t("override.details.title")}</h4>
                  <p className="text-sm text-[var(--text-secondary)] mt-1">{t("override.details.content")}</p>
                  <code className="block mt-2 p-2 bg-[var(--bg-secondary)] rounded text-sm font-mono text-[var(--text-secondary)]">
                    {t("override.details.list")}
                  </code>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
