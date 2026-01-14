"use client";

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import {
    Shield,
    Check,
    X,
    User,
    Calendar,
    FileArchive,
    FolderCog,
    Loader2,
    AlertCircle,
    Trash2,
    Edit,
    RefreshCw,
    Database,
} from "lucide-react";
import Button from "@/components/ui/Button";

interface RefreshResult {
    total: number;
    updated: number;
    failed: number;
    errors: string[];
}

// Flattened schema - no versions
interface Translation {
    id: string;
    modpackVersion: string;
    sourceLang: string;
    targetLang: string;
    status: string;
    resourcePackPath: string | null;
    overrideFilePath: string | null;
    isManualTranslation: boolean;
    llmModel: string | null;
    temperature: number | null;
    batchSize: number | null;
    usedGlossary: boolean;
    reviewed: boolean;
    downloadCount: number;
    createdAt: string;
    modpack: {
        id: number;
        name: string;
        slug: string;
        logoUrl: string | null;
    };
    user: {
        name: string;
        avatar: string | null;
        discordId: string;
    } | null;
    _count: {
        reviews: number;
    };
}

type TabType = "pending" | "all";

export default function AdminPage() {
    const t = useTranslations();
    const router = useRouter();
    const { data: session, status } = useSession();

    const [activeTab, setActiveTab] = useState<TabType>("pending");
    const [loading, setLoading] = useState(true);
    const [translations, setTranslations] = useState<Translation[]>([]);
    const [processing, setProcessing] = useState<string | null>(null);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editStatus, setEditStatus] = useState<string>("");
    const [refreshingModpacks, setRefreshingModpacks] = useState(false);
    const [refreshResult, setRefreshResult] = useState<RefreshResult | null>(null);

    useEffect(() => {
        if (status === "authenticated") {
            if (!session?.user?.isAdmin) {
                router.push("/");
                return;
            }
            fetchTranslations();
        } else if (status === "unauthenticated") {
            router.push("/");
        }
    }, [status, session, router, activeTab]);

    const fetchTranslations = async () => {
        setLoading(true);
        try {
            const endpoint = activeTab === "pending"
                ? "/api/admin/pending"
                : "/api/admin/translations";
            const response = await fetch(endpoint);
            if (response.ok) {
                const data = await response.json();
                setTranslations(data);
            }
        } catch (err) {
            console.error("Failed to fetch translations:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (id: string) => {
        if (!confirm(t("admin.confirmApprove"))) return;

        setProcessing(id);
        try {
            const response = await fetch(`/api/admin/approve/${id}`, {
                method: "POST",
            });
            if (response.ok) {
                if (activeTab === "pending") {
                    setTranslations((prev) => prev.filter((p) => p.id !== id));
                } else {
                    setTranslations((prev) =>
                        prev.map((p) => (p.id === id ? { ...p, status: "approved" } : p))
                    );
                }
            }
        } catch (err) {
            console.error("Failed to approve:", err);
        } finally {
            setProcessing(null);
        }
    };

    const handleReject = async (id: string) => {
        if (!confirm(t("admin.confirmReject"))) return;

        setProcessing(id);
        try {
            const response = await fetch(`/api/admin/reject/${id}`, {
                method: "POST",
            });
            if (response.ok) {
                if (activeTab === "pending") {
                    setTranslations((prev) => prev.filter((p) => p.id !== id));
                } else {
                    setTranslations((prev) =>
                        prev.map((p) => (p.id === id ? { ...p, status: "rejected" } : p))
                    );
                }
            }
        } catch (err) {
            console.error("Failed to reject:", err);
        } finally {
            setProcessing(null);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm(t("admin.confirmDelete"))) return;

        setProcessing(id);
        try {
            const response = await fetch(`/api/admin/translations/${id}`, {
                method: "DELETE",
            });
            if (response.ok) {
                setTranslations((prev) => prev.filter((p) => p.id !== id));
            }
        } catch (err) {
            console.error("Failed to delete:", err);
        } finally {
            setProcessing(null);
        }
    };

    const handleEditStart = (item: Translation) => {
        setEditingId(item.id);
        setEditStatus(item.status);
    };

    const handleEditSave = async (id: string) => {
        setProcessing(id);
        try {
            const response = await fetch(`/api/admin/translations/${id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: editStatus }),
            });
            if (response.ok) {
                setTranslations((prev) =>
                    prev.map((p) => (p.id === id ? { ...p, status: editStatus } : p))
                );
                setEditingId(null);
            }
        } catch (err) {
            console.error("Failed to update:", err);
        } finally {
            setProcessing(null);
        }
    };

    const handleRefreshModpacks = async () => {
        if (!confirm("모든 모드팩 정보를 CurseForge에서 새로 가져옵니다. 시간이 걸릴 수 있습니다. 계속하시겠습니까?")) return;

        setRefreshingModpacks(true);
        setRefreshResult(null);
        try {
            const response = await fetch("/api/admin/modpacks/refresh", {
                method: "POST",
            });
            if (response.ok) {
                const result = await response.json();
                setRefreshResult(result);
            }
        } catch (err) {
            console.error("Failed to refresh modpacks:", err);
        } finally {
            setRefreshingModpacks(false);
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

    if (status === "loading" || (status === "authenticated" && loading)) {
        return (
            <div className="flex items-center justify-center py-16">
                <Loader2 className="w-8 h-8 animate-spin text-[var(--accent-primary)]" />
            </div>
        );
    }

    if (!session?.user?.isAdmin) {
        return null;
    }

    const pendingCount = activeTab === "pending" ? translations.length : translations.filter(t => t.status === "pending").length;

    return (
        <div className="max-w-6xl mx-auto px-4 py-8 animate-fade-in">
            <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                    <Shield className="w-8 h-8 text-[var(--accent-primary)]" />
                    <h1 className="text-3xl font-bold text-[var(--text-primary)]">
                        {t("admin.title")}
                    </h1>
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        variant="secondary"
                        onClick={handleRefreshModpacks}
                        disabled={refreshingModpacks}
                    >
                        <Database className={`w-4 h-4 ${refreshingModpacks ? "animate-pulse" : ""}`} />
                        {refreshingModpacks ? "업데이트 중..." : "모드팩 정보 갱신"}
                    </Button>
                    <Button variant="secondary" onClick={fetchTranslations} disabled={loading}>
                        <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                        {t("common.refresh")}
                    </Button>
                </div>
            </div>

            {/* Refresh Result */}
            {refreshResult && (
                <div className={`mb-6 p-4 rounded-lg ${refreshResult.failed > 0 ? "bg-yellow-500/10 border border-yellow-500/30" : "bg-green-500/10 border border-green-500/30"}`}>
                    <div className="flex items-center gap-2 mb-2">
                        <Check className="w-5 h-5 text-green-500" />
                        <span className="font-medium text-[var(--text-primary)]">
                            모드팩 정보 갱신 완료
                        </span>
                    </div>
                    <div className="text-sm text-[var(--text-secondary)]">
                        전체 {refreshResult.total}개 중 {refreshResult.updated}개 업데이트, {refreshResult.failed}개 실패
                    </div>
                    {refreshResult.errors.length > 0 && (
                        <div className="mt-2 text-xs text-[var(--status-warning)]">
                            {refreshResult.errors.slice(0, 5).map((err, i) => (
                                <div key={i}>• {err}</div>
                            ))}
                            {refreshResult.errors.length > 5 && (
                                <div>... 그 외 {refreshResult.errors.length - 5}개 오류</div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Tabs */}
            <div className="flex gap-2 mb-6">
                <button
                    onClick={() => setActiveTab("pending")}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${activeTab === "pending"
                        ? "nav-active"
                        : "text-[var(--text-secondary)] hover:bg-[var(--bg-card)]"
                        }`}
                >
                    {t("admin.pendingReviews")} ({pendingCount})
                </button>
                <button
                    onClick={() => setActiveTab("all")}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${activeTab === "all"
                        ? "nav-active"
                        : "text-[var(--text-secondary)] hover:bg-[var(--bg-card)]"
                        }`}
                >
                    {t("admin.allTranslations")}
                </button>
            </div>

            {translations.length > 0 ? (
                <div className="space-y-4">
                    {translations.map((item) => {
                        const isProcessing = processing === item.id;
                        const isEditing = editingId === item.id;

                        return (
                            <div key={item.id} className="card p-5">
                                <div className="flex flex-col lg:flex-row gap-4">
                                    {/* Modpack Info */}
                                    <div className="flex gap-4 flex-1">
                                        {item.modpack.logoUrl ? (
                                            <Image
                                                src={item.modpack.logoUrl}
                                                alt={item.modpack.name}
                                                width={56}
                                                height={56}
                                                className="w-14 h-14 rounded-lg object-cover flex-shrink-0"
                                            />
                                        ) : (
                                            <div className="w-14 h-14 rounded-lg bg-[var(--bg-tertiary)] flex items-center justify-center flex-shrink-0">
                                                <span className="text-xl font-bold text-[var(--text-muted)]">
                                                    {item.modpack.name.charAt(0)}
                                                </span>
                                            </div>
                                        )}
                                        <div className="min-w-0 flex-1">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <h3 className="font-semibold text-[var(--text-primary)] truncate">
                                                    {item.modpack.name}
                                                </h3>
                                                {isEditing ? (
                                                    <select
                                                        value={editStatus}
                                                        onChange={(e) => setEditStatus(e.target.value)}
                                                        className="text-xs px-2 py-1 rounded"
                                                    >
                                                        <option value="pending">Pending</option>
                                                        <option value="approved">Approved</option>
                                                        <option value="rejected">Rejected</option>
                                                    </select>
                                                ) : (
                                                    <span className={`badge ${getStatusBadge(item.status)}`}>
                                                        {t(`translation.status.${item.status}` as never)}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-3 mt-1 text-sm text-[var(--text-muted)] flex-wrap">
                                                <span>
                                                    {t(`languages.${item.sourceLang}` as never)} →{" "}
                                                    {t(`languages.${item.targetLang}` as never)}
                                                </span>
                                                <span>{item.modpackVersion}</span>
                                                <span className="flex items-center gap-1">
                                                    <Calendar className="w-3 h-3" />
                                                    {new Date(item.createdAt).toLocaleDateString()}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Uploader & Stats */}
                                    <div className="flex items-center gap-4 text-sm">
                                        <div className="flex items-center gap-2 text-[var(--text-secondary)]">
                                            {item.user ? (
                                                <>
                                                    {item.user.avatar ? (
                                                        <Image
                                                            src={item.user.avatar}
                                                            alt={item.user.name}
                                                            width={24}
                                                            height={24}
                                                            className="w-6 h-6 rounded-full"
                                                        />
                                                    ) : (
                                                        <User className="w-5 h-5" />
                                                    )}
                                                    <span className="text-xs">{item.user.name}</span>
                                                </>
                                            ) : (
                                                <span className="text-xs text-[var(--text-muted)]">Anonymous</span>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-3 text-xs text-[var(--text-muted)]">
                                            {item.resourcePackPath && (
                                                <span title="Resource Pack">
                                                    <FileArchive className="w-4 h-4" />
                                                </span>
                                            )}
                                            {item.overrideFilePath && (
                                                <span title="Override File">
                                                    <FolderCog className="w-4 h-4" />
                                                </span>
                                            )}
                                            <span>{item.downloadCount} DL</span>
                                            <span>{item._count?.reviews || 0} Reviews</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="flex justify-end gap-2 mt-4 pt-3 border-t border-[var(--border-secondary)]">
                                    {isEditing ? (
                                        <>
                                            <Button
                                                variant="secondary"
                                                size="sm"
                                                onClick={() => setEditingId(null)}
                                            >
                                                {t("common.cancel")}
                                            </Button>
                                            <Button
                                                size="sm"
                                                onClick={() => handleEditSave(item.id)}
                                                disabled={isProcessing}
                                            >
                                                {t("common.save")}
                                            </Button>
                                        </>
                                    ) : (
                                        <>
                                            {item.status === "pending" && (
                                                <>
                                                    <Button
                                                        variant="danger"
                                                        size="sm"
                                                        onClick={() => handleReject(item.id)}
                                                        disabled={isProcessing}
                                                    >
                                                        <X className="w-4 h-4" />
                                                        {t("admin.actions.reject")}
                                                    </Button>
                                                    <Button
                                                        size="sm"
                                                        onClick={() => handleApprove(item.id)}
                                                        disabled={isProcessing}
                                                    >
                                                        <Check className="w-4 h-4" />
                                                        {t("admin.actions.approve")}
                                                    </Button>
                                                </>
                                            )}
                                            <Button
                                                variant="secondary"
                                                size="sm"
                                                onClick={() => handleEditStart(item)}
                                                disabled={isProcessing}
                                            >
                                                <Edit className="w-4 h-4" />
                                                {t("admin.actions.edit")}
                                            </Button>
                                            <Button
                                                variant="danger"
                                                size="sm"
                                                onClick={() => handleDelete(item.id)}
                                                disabled={isProcessing}
                                            >
                                                <Trash2 className="w-4 h-4" />
                                                {t("admin.actions.delete")}
                                            </Button>
                                        </>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            ) : (
                <div className="text-center py-16 glass rounded-xl">
                    <AlertCircle className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-4" />
                    <p className="text-[var(--text-muted)] text-lg">
                        {activeTab === "pending" ? t("admin.noPending") : t("admin.noTranslations")}
                    </p>
                </div>
            )}
        </div>
    );
}
