"use client";

import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { Link } from "@/i18n/navigation";
import Image from "next/image";
import {
  Clock,
  CheckCircle,
  XCircle,
  FileArchive,
  FolderCog,
  ExternalLink,
  RefreshCw,
  LogIn,
} from "lucide-react";
import Button from "@/components/ui/Button";

// Flattened schema - no versions
interface TranslationUpload {
  id: string;
  modpackVersion: string;
  status: "pending" | "approved" | "rejected";
  sourceLang: string;
  targetLang: string;
  isManualTranslation: boolean;
  llmModel: string | null;
  downloadCount: number;
  createdAt: string;
  updatedAt: string;
  modpack: {
    id: number;
    name: string;
    slug: string;
    logoUrl: string | null;
  };
}

export default function MyUploadsPage() {
  const t = useTranslations();
  const { data: session, status } = useSession();
  const [uploads, setUploads] = useState<TranslationUpload[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUploads = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/my-uploads");
      if (!res.ok) {
        throw new Error("Failed to fetch uploads");
      }
      const data = await res.json();
      setUploads(data.uploads || []);
    } catch (err) {
      setError(t("common.error"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (session) {
      fetchUploads();
    } else {
      setLoading(false);
    }
  }, [session]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "approved":
        return <CheckCircle className="w-5 h-5 text-[var(--status-success)]" />;
      case "rejected":
        return <XCircle className="w-5 h-5 text-[var(--status-error)]" />;
      default:
        return <Clock className="w-5 h-5 text-[var(--status-warning)]" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "approved":
        return "badge-success";
      case "rejected":
        return "badge-error";
      default:
        return "badge-warning";
    }
  };

  // Not logged in
  if (status === "unauthenticated") {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center animate-fade-in">
        <LogIn className="w-16 h-16 mx-auto mb-6 text-[var(--text-muted)]" />
        <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-4">
          {t("myUploads.loginRequired")}
        </h1>
        <p className="text-[var(--text-secondary)] mb-8">
          {t("myUploads.loginDescription")}
        </p>
        <Button onClick={() => window.location.href = "/api/auth/signin"}>
          {t("auth.signIn")}
        </Button>
      </div>
    );
  }

  // Loading
  if (status === "loading" || loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="spinner mx-auto mb-4" />
        <p className="text-[var(--text-muted)]">{t("common.loading")}</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-2">
            {t("myUploads.title")}
          </h1>
          <p className="text-[var(--text-secondary)]">
            {t("myUploads.description")}
          </p>
        </div>
        <Button variant="secondary" onClick={fetchUploads} disabled={loading}>
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          {t("common.refresh")}
        </Button>
      </div>

      {/* Status Legend */}
      <div className="glass rounded-lg p-4 mb-8">
        <h3 className="text-sm font-medium text-[var(--text-primary)] mb-3">
          {t("myUploads.statusLegend")}
        </h3>
        <div className="flex flex-wrap gap-6 text-sm">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-[var(--status-warning)]" />
            <span className="text-[var(--text-secondary)]">
              {t("translation.status.pending")}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-[var(--status-success)]" />
            <span className="text-[var(--text-secondary)]">
              {t("translation.status.approved")}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <XCircle className="w-4 h-4 text-[var(--status-error)]" />
            <span className="text-[var(--text-secondary)]">
              {t("translation.status.rejected")}
            </span>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-[var(--status-error)]/20 text-[var(--status-error)] p-4 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Uploads List - Flattened schema */}
      {uploads.length > 0 ? (
        <div className="space-y-4">
          {uploads.map((upload) => (
            <div key={upload.id} className="card p-5">
              <div className="flex flex-col md:flex-row gap-4">
                {/* Modpack Info */}
                <div className="flex items-start gap-4 flex-1">
                  {upload.modpack.logoUrl ? (
                    <Image
                      src={upload.modpack.logoUrl}
                      alt={upload.modpack.name}
                      width={64}
                      height={64}
                      className="w-16 h-16 rounded-lg object-cover flex-shrink-0"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-lg bg-[var(--bg-tertiary)] flex items-center justify-center flex-shrink-0">
                      <span className="text-xl font-bold text-[var(--text-muted)]">
                        {upload.modpack.name.charAt(0)}
                      </span>
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-[var(--text-primary)] truncate">
                        {upload.modpack.name}
                      </h3>
                      <span className={`badge ${getStatusBadge(upload.status)}`}>
                        {t(`translation.status.${upload.status}` as never)}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-3 text-sm text-[var(--text-secondary)]">
                      <span>
                        {t(`languages.${upload.sourceLang}` as never)} →{" "}
                        {t(`languages.${upload.targetLang}` as never)}
                      </span>
                      <span>•</span>
                      <span>{upload.modpackVersion}</span>
                      <span>•</span>
                      <span>
                        {t("myUploads.uploadedAt")}: {new Date(upload.createdAt).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-sm text-[var(--text-muted)]">
                      <span>
                        {upload.isManualTranslation
                          ? t("translation.metadata.manualTranslation")
                          : upload.llmModel || t("translation.metadata.aiTranslation")}
                      </span>
                      <span>•</span>
                      <span>{upload.downloadCount} {t("modpacks.card.downloads")}</span>
                    </div>
                  </div>
                </div>

                {/* Status & Actions */}
                <div className="flex items-center gap-3">
                  {getStatusIcon(upload.status)}
                  {upload.status === "approved" && (
                    <Link href={`/modpacks/${upload.modpack.id}`}>
                      <Button variant="secondary" size="sm">
                        <ExternalLink className="w-4 h-4" />
                        {t("myUploads.viewPage")}
                      </Button>
                    </Link>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 glass rounded-xl">
          <FileArchive className="w-16 h-16 mx-auto mb-6 text-[var(--text-muted)]" />
          <p className="text-[var(--text-muted)] text-lg mb-4">
            {t("myUploads.noUploads")}
          </p>
          <Link href="/upload">
            <Button>{t("myUploads.uploadFirst")}</Button>
          </Link>
        </div>
      )}
    </div>
  );
}
