"use client";

import { useTranslations } from "next-intl";
import { useState, useMemo } from "react";
import Image from "next/image";
import { Link } from "@/i18n/navigation";
import { useRouter } from "next/navigation";
import {
    User,
    Download,
    Calendar,
    Filter,
    ArrowUpDown,
    ExternalLink,
    Gamepad2,
    Edit,
    Trash2,
    Loader2,
    Save,
    X,
    Check,
    CheckCircle,
    AlertCircle,
    Star,
    MessageSquare,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import MapTranslationDownloadActions from "./MapTranslationDownloadActions";

export interface MapTranslation {
    id: string;
    version: string;
    sourceLang: string;
    targetLang: string;
    status: string;
    resourcePackUrl: string | null;
    overrideFileUrl: string | null;
    originalLink: string | null;
    minecraftVersion: string | null;
    downloadCount: number;
    createdAt: string;
    user: {
        name: string;
        avatar: string | null;
    } | null;
    _count: {
        reviews: number;
    };
}

export interface MapReviewStats {
    avgRating: number;
}

export interface MapWorksStats {
    works: number;
    notWorks: number;
}

interface MapTranslationListProps {
    initialTranslations: MapTranslation[];
    mapId: number;
    mapOriginalLink?: string | null;
    reviewStats: Record<string, MapReviewStats>;
    worksStats: Record<string, MapWorksStats>;
    isAdmin?: boolean;
}

export default function MapTranslationList({
    initialTranslations,
    mapId,
    mapOriginalLink,
    reviewStats,
    worksStats,
    isAdmin = false,
}: MapTranslationListProps) {
    const t = useTranslations();
    const router = useRouter();
    const [sortBy, setSortBy] = useState<"latest" | "downloads" | "version">("latest");
    const [filterVersion, setFilterVersion] = useState<string>("all");
    const [editingTrans, setEditingTrans] = useState<MapTranslation | null>(null);
    const [editLoading, setEditLoading] = useState(false);
    const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
    const [deleteLoading, setDeleteLoading] = useState(false);

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

    // Admin edit handler
    const handleEditSubmit = async (formData: {
        version: string;
        sourceLang: string;
        targetLang: string;
        status: string;
        resourcePackUrl: string;
        overrideFileUrl: string;
        originalLink: string;
        minecraftVersion: string;
    }) => {
        if (!editingTrans) return;
        setEditLoading(true);
        try {
            const res = await fetch(`/api/maps/translations/${editingTrans.id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });
            if (!res.ok) throw new Error("Failed to update");
            setEditingTrans(null);
            router.refresh();
        } catch (error) {
            console.error(error);
            alert("수정 실패");
        } finally {
            setEditLoading(false);
        }
    };

    // Admin delete handler
    const handleDelete = async (transId: string) => {
        setDeleteLoading(true);
        try {
            const res = await fetch(`/api/maps/translations/${transId}`, {
                method: "DELETE",
            });
            if (!res.ok) throw new Error("Failed to delete");
            setDeleteConfirm(null);
            router.refresh();
        } catch (error) {
            console.error(error);
            alert("삭제 실패");
        } finally {
            setDeleteLoading(false);
        }
    };

    // Status badge helper
    const getStatusBadge = (status: string) => {
        switch (status) {
            case "approved":
                return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-500/15 text-green-400 border border-green-500/20"><CheckCircle className="w-3 h-3" />승인됨</span>;
            case "pending":
                return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-500/15 text-yellow-400 border border-yellow-500/20"><AlertCircle className="w-3 h-3" />대기중</span>;
            case "rejected":
                return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/15 text-red-400 border border-red-500/20"><X className="w-3 h-3" />거절됨</span>;
            default:
                return null;
        }
    };

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
                            {/* Admin controls */}
                            {isAdmin && (
                                <div className="flex items-center justify-between mb-3 pb-3 border-b border-[var(--border-secondary)]">
                                    <div className="flex items-center gap-2">
                                        {getStatusBadge(trans.status)}
                                        <span className="text-xs text-[var(--text-muted)]">ID: {trans.id.slice(0, 8)}...</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Button size="sm" variant="secondary" onClick={() => setEditingTrans(trans)}>
                                            <Edit className="w-3.5 h-3.5" />
                                            수정
                                        </Button>
                                        <Button size="sm" variant="secondary" onClick={() => setDeleteConfirm(trans.id)} className="text-red-400 hover:text-red-300 hover:border-red-500/50">
                                            <Trash2 className="w-3.5 h-3.5" />
                                            삭제
                                        </Button>
                                    </div>
                                </div>
                            )}
                            <div className="flex flex-col lg:flex-row gap-6">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-4 flex-wrap">
                                        <span className="badge">
                                            {t(`languages.${trans.sourceLang}` as any)} →{" "}
                                            {t(`languages.${trans.targetLang}` as any)}
                                        </span>
                                        {trans.minecraftVersion && (
                                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
                                                <Gamepad2 className="w-3 h-3" />
                                                MC {trans.minecraftVersion}
                                            </span>
                                        )}
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
                                        {reviewStats[trans.id] && (
                                            <span className="flex items-center gap-1">
                                                <Star className="w-4 h-4 text-yellow-500" />
                                                {reviewStats[trans.id].avgRating.toFixed(1)}
                                            </span>
                                        )}
                                        {worksStats[trans.id] && (
                                            <>
                                                <span className="flex items-center gap-1 text-[var(--status-success)]">
                                                    <Check className="w-4 h-4" />
                                                    {worksStats[trans.id].works} {t("review.works.yes")}
                                                </span>
                                                <span className="flex items-center gap-1 text-[var(--status-error)]">
                                                    <X className="w-4 h-4" />
                                                    {worksStats[trans.id].notWorks} {t("review.works.no")}
                                                </span>
                                            </>
                                        )}
                                        <span className="flex items-center gap-1">
                                            <MessageSquare className="w-4 h-4" />
                                            {trans._count.reviews} {t("review.title")}
                                        </span>
                                        <span className="flex items-center gap-1">
                                            <Calendar className="w-4 h-4" />
                                            {new Date(trans.createdAt).toLocaleDateString()}
                                        </span>
                                    </div>

                                    <div className="p-4 rounded-lg bg-[var(--bg-secondary)] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                                        <div>
                                            <div className="font-medium text-[var(--text-primary)] mb-1">
                                                {trans.version}
                                            </div>
                                        </div>
                                        <div className="flex flex-wrap items-center gap-2">
                                            {(trans.originalLink || mapOriginalLink) && (
                                                <a
                                                    href={trans.originalLink || mapOriginalLink!}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                >
                                                    <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-white border-amber-500">
                                                        <ExternalLink className="w-4 h-4" />
                                                        맵 다운로드
                                                    </Button>
                                                </a>
                                            )}
                                            <MapTranslationDownloadActions
                                                translationId={trans.id}
                                                mapId={mapId}
                                                resourcePackUrl={trans.resourcePackUrl}
                                                overrideFileUrl={trans.overrideFileUrl}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="mt-4 pt-4 border-t border-[var(--border-secondary)]">
                                <Link
                                    href={`/maps/${mapId}/review/${trans.id}`}
                                    className="text-sm text-[var(--accent-primary)] hover:text-[var(--accent-hover)] transition-colors"
                                >
                                    {t("review.writeReview")} →
                                </Link>
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

            {/* Admin Edit Modal */}
            {editingTrans && (
                <MapTranslationEditModal
                    translation={editingTrans}
                    loading={editLoading}
                    onClose={() => setEditingTrans(null)}
                    onSubmit={handleEditSubmit}
                />
            )}

            {/* Admin Delete Confirm Modal */}
            <Modal
                isOpen={deleteConfirm !== null}
                onClose={() => setDeleteConfirm(null)}
                title="번역 삭제 확인"
            >
                <div className="space-y-4">
                    <p className="text-[var(--text-secondary)]">
                        이 번역을 정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
                    </p>
                    <div className="flex justify-end gap-3">
                        <Button variant="secondary" onClick={() => setDeleteConfirm(null)}>
                            취소
                        </Button>
                        <Button
                            onClick={() => deleteConfirm && handleDelete(deleteConfirm)}
                            disabled={deleteLoading}
                            className="bg-red-500 hover:bg-red-600 text-white border-red-500"
                        >
                            {deleteLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                            삭제
                        </Button>
                    </div>
                </div>
            </Modal>
        </div>
    );
}

// Map Translation Edit Modal Component
function MapTranslationEditModal({
    translation,
    loading,
    onClose,
    onSubmit,
}: {
    translation: MapTranslation;
    loading: boolean;
    onClose: () => void;
    onSubmit: (data: {
        version: string;
        sourceLang: string;
        targetLang: string;
        status: string;
        resourcePackUrl: string;
        overrideFileUrl: string;
        originalLink: string;
        minecraftVersion: string;
    }) => void;
}) {
    const [formData, setFormData] = useState({
        version: translation.version,
        sourceLang: translation.sourceLang,
        targetLang: translation.targetLang,
        status: translation.status,
        resourcePackUrl: translation.resourcePackUrl || "",
        overrideFileUrl: translation.overrideFileUrl || "",
        originalLink: translation.originalLink || "",
        minecraftVersion: translation.minecraftVersion || "",
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit(formData);
    };

    return (
        <Modal isOpen={true} onClose={onClose} title="맵 번역 수정">
            <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">버전</label>
                        <input
                            type="text"
                            value={formData.version}
                            onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                            className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">마인크래프트 버전</label>
                        <input
                            type="text"
                            value={formData.minecraftVersion}
                            onChange={(e) => setFormData({ ...formData, minecraftVersion: e.target.value })}
                            className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">원본 언어</label>
                        <input
                            type="text"
                            value={formData.sourceLang}
                            onChange={(e) => setFormData({ ...formData, sourceLang: e.target.value })}
                            className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">번역 언어</label>
                        <input
                            type="text"
                            value={formData.targetLang}
                            onChange={(e) => setFormData({ ...formData, targetLang: e.target.value })}
                            className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
                            required
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">상태</label>
                    <select
                        value={formData.status}
                        onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                        className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
                    >
                        <option value="pending">대기중</option>
                        <option value="approved">승인됨</option>
                        <option value="rejected">거절됨</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">리소스팩 URL/경로</label>
                    <input
                        type="text"
                        value={formData.resourcePackUrl}
                        onChange={(e) => setFormData({ ...formData, resourcePackUrl: e.target.value })}
                        className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
                        placeholder="maps/파일명.zip 또는 https://..."
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">오버라이드 파일 URL/경로</label>
                    <input
                        type="text"
                        value={formData.overrideFileUrl}
                        onChange={(e) => setFormData({ ...formData, overrideFileUrl: e.target.value })}
                        className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
                        placeholder="maps/파일명.zip 또는 https://..."
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">맵 원본 링크</label>
                    <input
                        type="text"
                        value={formData.originalLink}
                        onChange={(e) => setFormData({ ...formData, originalLink: e.target.value })}
                        className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
                        placeholder="https://..."
                    />
                </div>

                <div className="flex justify-end gap-3 pt-2">
                    <Button type="button" variant="secondary" onClick={onClose}>
                        취소
                    </Button>
                    <Button type="submit" disabled={loading}>
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                        저장
                    </Button>
                </div>
            </form>
        </Modal>
    );
}
