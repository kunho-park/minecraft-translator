"use client";

import { useState, useEffect, Suspense } from "react";
import { useTranslations } from "next-intl";
import { useSearchParams, useRouter } from "next/navigation";
import { useSession, signIn } from "next-auth/react";
import Image from "next/image";
import {
    Search,
    Upload,
    FileArchive,
    FolderCog,
    X,
    Check,
    AlertCircle,
    Loader2,
    Package,
    Globe,
    Plus,
    Link as LinkIcon,
    FileText,
} from "lucide-react";
import Button from "@/components/ui/Button";

interface ModpackInfo {
    id: number;
    name: string;
    slug: string;
    summary: string;
    logoUrl: string | null;
    author: string | null;
    gameVersions: string[];
    downloadCount: number;
}

interface MapInfo {
    id: number;
    name: string;
    slug: string;
    summary: string;
    thumbnailUrl: string | null;
    originalLink: string | null;
    author: string | null;
}

const LANGUAGE_OPTIONS = [
    { value: "en_us", label: "English" },
    { value: "ko_kr", label: "한국어" },
    { value: "ja_jp", label: "日本語" },
    { value: "zh_cn", label: "简体中文" },
    { value: "zh_tw", label: "繁體中文" },
];

function UploadContent() {
    const t = useTranslations();
    const router = useRouter();
    const searchParams = useSearchParams();
    const { data: session, status } = useSession();

    const [activeTab, setActiveTab] = useState<"modpack" | "map">("modpack");
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    // --- Modpack State ---
    const [searchQuery, setSearchQuery] = useState(searchParams.get("modpack") || "");
    const [modpack, setModpack] = useState<ModpackInfo | null>(null);

    const [resourcePackType, setResourcePackType] = useState<"file" | "link">("file");
    const [resourcePack, setResourcePack] = useState<File | null>(null);
    const [resourcePackLink, setResourcePackLink] = useState("");

    const [overrideFileType, setOverrideFileType] = useState<"file" | "link">("file");
    const [overrideFile, setOverrideFile] = useState<File | null>(null);
    const [overrideFileLink, setOverrideFileLink] = useState("");

    const [modpackVersion, setModpackVersion] = useState("");
    const [sourceLang, setSourceLang] = useState("en_us");
    const [targetLang, setTargetLang] = useState("ko_kr");
    const [isManualTranslation, setIsManualTranslation] = useState(false);
    const [llmModel, setLlmModel] = useState("");
    const [temperature, setTemperature] = useState("");
    const [batchSize, setBatchSize] = useState("");
    const [usedGlossary, setUsedGlossary] = useState(false);
    const [reviewed, setReviewed] = useState(false);

    // --- Map State ---
    const [mapSearchQuery, setMapSearchQuery] = useState("");
    const [selectedMap, setSelectedMap] = useState<MapInfo | null>(null);
    const [isCreatingMap, setIsCreatingMap] = useState(false);
    const [newMapName, setNewMapName] = useState("");
    const [newMapSummary, setNewMapSummary] = useState("");
    const [newMapAuthor, setNewMapAuthor] = useState("");
    const [newMapLink, setNewMapLink] = useState("");
    const [newMapThumbnail, setNewMapThumbnail] = useState<File | null>(null);

    const [mapResourcePackType, setMapResourcePackType] = useState<"file" | "link">("file");
    const [mapResourcePack, setMapResourcePack] = useState<File | null>(null);
    const [mapResourcePackLink, setMapResourcePackLink] = useState("");

    const [mapOverrideFileType, setMapOverrideFileType] = useState<"file" | "link">("file");
    const [mapOverrideFile, setMapOverrideFile] = useState<File | null>(null);
    const [mapOverrideFileLink, setMapOverrideFileLink] = useState("");

    const [mapVersion, setMapVersion] = useState("");

    // Auto-search if modpack ID is in URL
    useEffect(() => {
        const modpackId = searchParams.get("modpack");
        if (modpackId) {
            handleSearchModpack(modpackId);
        }
    }, [searchParams]);

    const handleSearchModpack = async (query?: string) => {
        const searchValue = query || searchQuery;
        if (!searchValue) return;

        setLoading(true);
        setError(null);
        setModpack(null);

        try {
            const response = await fetch(`/api/curseforge/${searchValue}`);
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || "Failed to fetch modpack");
            }
            const data = await response.json();
            setModpack(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Unknown error");
        } finally {
            setLoading(false);
        }
    };

    const handleSearchMap = async (query?: string) => {
        const searchValue = query || mapSearchQuery;
        if (!searchValue) return;

        setLoading(true);
        setError(null);
        setSelectedMap(null);

        try {
            const response = await fetch(`/api/maps?q=${encodeURIComponent(searchValue)}`);
            if (!response.ok) {
                throw new Error("Failed to search maps");
            }
            const data = await response.json();
            if (data.length > 0) {
                setSelectedMap(data[0]);
            } else {
                setError(t("maps.noResults"));
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Unknown error");
        } finally {
            setLoading(false);
        }
    };

    const handleFileChange = (
        e: React.ChangeEvent<HTMLInputElement>,
        type: "resourcePack" | "overrideFile" | "mapResourcePack" | "mapOverrideFile" | "thumbnail"
    ) => {
        const file = e.target.files?.[0];
        if (file) {
            if (type === "resourcePack") setResourcePack(file);
            else if (type === "overrideFile") setOverrideFile(file);
            else if (type === "mapResourcePack") setMapResourcePack(file);
            else if (type === "mapOverrideFile") setMapOverrideFile(file);
            else if (type === "thumbnail") setNewMapThumbnail(file);
        }
    };

    const handleModpackSubmit = async () => {
        const hasResourcePack = resourcePackType === "file" ? !!resourcePack : !!resourcePackLink;
        const hasOverrideFile = overrideFileType === "file" ? !!overrideFile : !!overrideFileLink;

        if (!modpack || !modpackVersion || (!hasResourcePack && !hasOverrideFile)) {
            setError("Please fill in all required fields");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append("curseforgeId", modpack.id.toString());
            formData.append("modpackVersion", modpackVersion);
            formData.append("sourceLang", sourceLang);
            formData.append("targetLang", targetLang);
            formData.append("isManualTranslation", isManualTranslation.toString());
            if (!isManualTranslation) {
                if (llmModel) formData.append("llmModel", llmModel);
                if (temperature) formData.append("temperature", temperature);
                if (batchSize) formData.append("batchSize", batchSize);
                formData.append("usedGlossary", usedGlossary.toString());
            }
            formData.append("reviewed", reviewed.toString());

            if (resourcePackType === "file" && resourcePack) {
                formData.append("resourcePack", resourcePack);
            } else if (resourcePackType === "link" && resourcePackLink) {
                formData.append("resourcePackLink", resourcePackLink);
            }

            if (overrideFileType === "file" && overrideFile) {
                formData.append("overrideFile", overrideFile);
            } else if (overrideFileType === "link" && overrideFileLink) {
                formData.append("overrideFileLink", overrideFileLink);
            }

            const response = await fetch("/api/translations", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || "Failed to upload");
            }

            setSuccess(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Upload failed");
        } finally {
            setLoading(false);
        }
    };

    const handleMapSubmit = async () => {
        const hasResourcePack = mapResourcePackType === "file" ? !!mapResourcePack : !!mapResourcePackLink;
        const hasOverrideFile = mapOverrideFileType === "file" ? !!mapOverrideFile : !!mapOverrideFileLink;

        if ((!hasResourcePack && !hasOverrideFile) || !mapVersion) {
            setError("Please fill in all required fields");
            return;
        }

        if (isCreatingMap && (!newMapName || !newMapSummary)) {
            setError("Please fill in map details");
            return;
        }

        if (!isCreatingMap && !selectedMap) {
            setError("Please select a map");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            let mapId = selectedMap?.id;

            // Create Map if needed
            if (isCreatingMap) {
                const mapFormData = new FormData();
                mapFormData.append("name", newMapName);
                mapFormData.append("summary", newMapSummary);
                if (newMapAuthor) mapFormData.append("author", newMapAuthor);
                if (newMapLink) mapFormData.append("originalLink", newMapLink);
                if (newMapThumbnail) mapFormData.append("thumbnail", newMapThumbnail);

                const mapResponse = await fetch("/api/maps", {
                    method: "POST",
                    body: mapFormData,
                });

                if (!mapResponse.ok) {
                    const data = await mapResponse.json();
                    throw new Error(data.error || "Failed to create map");
                }

                const newMap = await mapResponse.json();
                mapId = newMap.id;
            }

            // Upload Translation
            const formData = new FormData();
            formData.append("mapId", mapId!.toString());
            formData.append("version", mapVersion);

            if (mapResourcePackType === "file" && mapResourcePack) {
                formData.append("resourcePack", mapResourcePack);
            } else if (mapResourcePackType === "link" && mapResourcePackLink) {
                formData.append("resourcePackLink", mapResourcePackLink);
            }

            if (mapOverrideFileType === "file" && mapOverrideFile) {
                formData.append("overrideFile", mapOverrideFile);
            } else if (mapOverrideFileType === "link" && mapOverrideFileLink) {
                formData.append("overrideFileLink", mapOverrideFileLink);
            }

            const response = await fetch("/api/maps/translations", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || "Failed to upload translation");
            }

            setSuccess(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Upload failed");
        } finally {
            setLoading(false);
        }
    };

    const renderFileInput = (
        label: string,
        type: "file" | "link",
        setType: (t: "file" | "link") => void,
        file: File | null,
        setFile: (e: React.ChangeEvent<HTMLInputElement>) => void,
        link: string,
        setLink: (s: string) => void,
        fileInputName: string
    ) => (
        <div>
            <div className="flex justify-between items-center mb-2">
                <label className="block text-sm text-[var(--text-secondary)]">
                    {label}
                </label>
                <div className="flex bg-[var(--bg-tertiary)] rounded-lg p-1">
                    <button
                        onClick={() => setType("file")}
                        className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${type === "file"
                            ? "bg-[var(--bg-card)] text-[var(--text-primary)] shadow-sm"
                            : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
                            }`}
                    >
                        파일
                    </button>
                    <button
                        onClick={() => setType("link")}
                        className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${type === "link"
                            ? "bg-[var(--bg-card)] text-[var(--text-primary)] shadow-sm"
                            : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
                            }`}
                    >
                        링크
                    </button>
                </div>
            </div>

            {type === "file" ? (
                <div className="relative">
                    <input
                        type="file"
                        accept=".zip"
                        onChange={setFile}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    <div
                        className={`p-8 rounded-lg border-2 border-dashed transition-colors ${file
                            ? "border-[var(--accent-primary)] bg-[var(--accent-primary)]/10"
                            : "border-[var(--border-primary)] hover:border-[var(--text-muted)]"
                            } flex flex-col items-center justify-center gap-3`}
                    >
                        <FileArchive
                            className={`w-10 h-10 ${file
                                ? "text-[var(--accent-primary)]"
                                : "text-[var(--text-muted)]"
                                }`}
                        />
                        {file ? (
                            <div className="flex items-center gap-2">
                                <span className="text-[var(--text-primary)]">
                                    {file.name}
                                </span>
                                <button
                                    onClick={(e) => {
                                        e.preventDefault();
                                        // Reset file logic handled by parent state update via setFile(null) equivalent
                                        // But here setFile expects event. 
                                        // We need a clear handler.
                                        // For simplicity, user can just click to replace.
                                    }}
                                    className="text-[var(--text-muted)] hover:text-[var(--status-error)]"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        ) : (
                            <span className="text-[var(--text-muted)]">
                                {t("upload.files.dropzone")}
                            </span>
                        )}
                    </div>
                </div>
            ) : (
                <div className="relative">
                    <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-muted)] pointer-events-none" />
                    <input
                        type="url"
                        value={link}
                        onChange={(e) => setLink(e.target.value)}
                        placeholder="https://example.com/download.zip"
                        className="w-full pr-4 py-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border-primary)] focus:border-[var(--accent-primary)] focus:ring-2 focus:ring-[var(--accent-primary)]/20 transition-all"
                        style={{ paddingLeft: "3.5rem" }}
                    />
                </div>
            )}
        </div>
    );

    if (status === "loading") {
        return <LoadingFallback />;
    }

    if (status === "unauthenticated") {
        return (
            <div className="max-w-2xl mx-auto px-4 py-16 text-center animate-fade-in">
                <div className="w-16 h-16 rounded-full bg-[var(--bg-secondary)] flex items-center justify-center mx-auto mb-6">
                    <Upload className="w-8 h-8 text-[var(--text-muted)]" />
                </div>
                <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-4">
                    {t("upload.loginRequired")}
                </h1>
                <p className="text-[var(--text-secondary)] mb-8">
                    {t("upload.loginDescription")}
                </p>
                <Button onClick={() => signIn("discord")}>{t("auth.signIn")}</Button>
            </div>
        );
    }

    if (success) {
        return (
            <div className="max-w-2xl mx-auto px-4 py-16 text-center animate-fade-in">
                <div className="w-16 h-16 rounded-full bg-[var(--status-success)]/20 flex items-center justify-center mx-auto mb-6">
                    <Check className="w-8 h-8 text-[var(--status-success)]" />
                </div>
                <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-4">
                    {t("upload.success.title")}
                </h1>
                <p className="text-[var(--text-secondary)] mb-8">
                    {t("upload.success.message")}
                </p>
                <Button onClick={() => router.push(activeTab === "modpack" ? "/modpacks" : "/maps")}>
                    {activeTab === "modpack" ? t("nav.modpacks") : t("nav.maps")}
                </Button>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto px-4 py-8 animate-fade-in">
            <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-8">
                {t("upload.title")}
            </h1>

            {/* Tabs */}
            <div className="flex gap-4 mb-8 border-b border-[var(--border-primary)]">
                <button
                    onClick={() => { setActiveTab("modpack"); setStep(1); }}
                    className={`pb-3 px-4 font-medium transition-colors relative ${activeTab === "modpack"
                        ? "text-[var(--accent-primary)]"
                        : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <Package className="w-4 h-4" />
                        {t("nav.modpacks")}
                    </div>
                    {activeTab === "modpack" && (
                        <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[var(--accent-primary)]" />
                    )}
                </button>
                <button
                    onClick={() => { setActiveTab("map"); setStep(1); }}
                    className={`pb-3 px-4 font-medium transition-colors relative ${activeTab === "map"
                        ? "text-[var(--accent-primary)]"
                        : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <Globe className="w-4 h-4" />
                        {t("nav.maps")}
                    </div>
                    {activeTab === "map" && (
                        <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[var(--accent-primary)]" />
                    )}
                </button>
            </div>

            {/* Progress Steps */}
            <div className="flex items-center justify-center gap-4 mb-12">
                {[1, 2, 3].map((s) => (
                    <div key={s} className="flex items-center">
                        <div
                            className={`w-10 h-10 rounded-full flex items-center justify-center font-medium transition-colors ${step >= s
                                ? "bg-[var(--accent-primary)] text-white"
                                : "bg-[var(--bg-card)] text-[var(--text-muted)]"
                                }`}
                        >
                            {s}
                        </div>
                        {s < 3 && (
                            <div
                                className={`w-16 h-1 mx-2 rounded ${step > s ? "bg-[var(--accent-primary)]" : "bg-[var(--bg-card)]"
                                    }`}
                            />
                        )}
                    </div>
                ))}
            </div>

            {error && (
                <div className="mb-6 p-4 rounded-lg bg-[var(--status-error)]/20 text-[var(--status-error)] flex items-center gap-3">
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                    {error}
                </div>
            )}

            {/* --- MODPACK FLOW --- */}
            {activeTab === "modpack" && (
                <>
                    {step === 1 && (
                        <div className="glass rounded-xl p-6">
                            <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-6">
                                {t("upload.steps.modpack")}
                            </h2>
                            <div className="space-y-4">
                                <label className="block">
                                    <span className="text-sm text-[var(--text-secondary)] mb-2 block">
                                        {t("upload.modpack.searchLabel")}
                                    </span>
                                    <div className="flex gap-3">
                                        <div className="flex-1 relative">
                                            <input
                                                type="text"
                                                value={searchQuery}
                                                onChange={(e) => setSearchQuery(e.target.value)}
                                                placeholder={t("upload.modpack.searchPlaceholder")}
                                                className="w-full"
                                                onKeyDown={(e) => e.key === "Enter" && handleSearchModpack()}
                                            />
                                        </div>
                                        <Button
                                            onClick={() => handleSearchModpack()}
                                            disabled={loading || !searchQuery}
                                            loading={loading}
                                        >
                                            <Search className="w-4 h-4" />
                                            {t("upload.modpack.searchButton")}
                                        </Button>
                                    </div>
                                </label>
                                {modpack && (
                                    <div className="mt-6 p-4 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-primary)]">
                                        <div className="flex gap-4">
                                            {modpack.logoUrl ? (
                                                <Image
                                                    src={modpack.logoUrl}
                                                    alt={modpack.name}
                                                    width={64}
                                                    height={64}
                                                    className="w-16 h-16 rounded-lg object-cover"
                                                />
                                            ) : (
                                                <div className="w-16 h-16 rounded-lg bg-[var(--bg-tertiary)] flex items-center justify-center">
                                                    <span className="text-2xl font-bold text-[var(--text-muted)]">
                                                        {modpack.name.charAt(0)}
                                                    </span>
                                                </div>
                                            )}
                                            <div className="flex-1">
                                                <h3 className="font-semibold text-[var(--text-primary)]">
                                                    {modpack.name}
                                                </h3>
                                                {modpack.author && (
                                                    <p className="text-sm text-[var(--text-muted)]">
                                                        by {modpack.author}
                                                    </p>
                                                )}
                                                <p className="text-sm text-[var(--text-secondary)] mt-1 line-clamp-2">
                                                    {modpack.summary}
                                                </p>
                                            </div>
                                        </div>
                                        <p className="text-sm text-[var(--accent-primary)] mt-4">
                                            {t("upload.modpack.confirm")}
                                        </p>
                                    </div>
                                )}
                            </div>
                            <div className="flex justify-end mt-6">
                                <Button onClick={() => setStep(2)} disabled={!modpack}>
                                    {t("common.submit")} →
                                </Button>
                            </div>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="glass rounded-xl p-6">
                            <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-6">
                                {t("upload.steps.files")}
                            </h2>
                            <div className="space-y-6">
                                {renderFileInput(
                                    t("upload.files.resourcePack"),
                                    resourcePackType,
                                    setResourcePackType,
                                    resourcePack,
                                    (e) => handleFileChange(e, "resourcePack"),
                                    resourcePackLink,
                                    setResourcePackLink,
                                    "resourcePack"
                                )}
                                {renderFileInput(
                                    t("upload.files.overrideFile"),
                                    overrideFileType,
                                    setOverrideFileType,
                                    overrideFile,
                                    (e) => handleFileChange(e, "overrideFile"),
                                    overrideFileLink,
                                    setOverrideFileLink,
                                    "overrideFile"
                                )}
                            </div>
                            <div className="flex justify-between mt-6">
                                <Button variant="secondary" onClick={() => setStep(1)}>
                                    ← {t("common.cancel")}
                                </Button>
                                <Button
                                    onClick={() => setStep(3)}
                                    disabled={
                                        !((resourcePackType === "file" && resourcePack) || (resourcePackType === "link" && resourcePackLink)) &&
                                        !((overrideFileType === "file" && overrideFile) || (overrideFileType === "link" && overrideFileLink))
                                    }
                                >
                                    {t("common.submit")} →
                                </Button>
                            </div>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="glass rounded-xl p-6">
                            <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-6">
                                {t("upload.steps.metadata")}
                            </h2>
                            <div className="space-y-4">
                                <div className="mb-6">
                                    <label className="block text-sm text-[var(--text-secondary)] mb-3">
                                        {t("upload.metadata.translationType")}
                                    </label>
                                    <div className="flex gap-4">
                                        <button
                                            type="button"
                                            onClick={() => setIsManualTranslation(false)}
                                            className={`flex-1 p-4 rounded-lg border-2 transition-all ${!isManualTranslation
                                                ? "border-[var(--accent-primary)] bg-[var(--accent-primary)]/10 text-[var(--accent-primary)]"
                                                : "border-[var(--border-primary)] text-[var(--text-secondary)] hover:border-[var(--text-muted)]"
                                                }`}
                                        >
                                            <div className="font-medium">{t("upload.metadata.aiTranslation")}</div>
                                            <div className="text-xs mt-1 opacity-70">{t("upload.metadata.aiTranslationDesc")}</div>
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setIsManualTranslation(true)}
                                            className={`flex-1 p-4 rounded-lg border-2 transition-all ${isManualTranslation
                                                ? "border-[var(--accent-primary)] bg-[var(--accent-primary)]/10 text-[var(--accent-primary)]"
                                                : "border-[var(--border-primary)] text-[var(--text-secondary)] hover:border-[var(--text-muted)]"
                                                }`}
                                        >
                                            <div className="font-medium">{t("upload.metadata.manualTranslation")}</div>
                                            <div className="text-xs mt-1 opacity-70">{t("upload.metadata.manualTranslationDesc")}</div>
                                        </button>
                                    </div>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <label className="block">
                                        <span className="text-sm text-[var(--text-secondary)] mb-2 block">
                                            {t("upload.metadata.version")} *
                                        </span>
                                        <input
                                            type="text"
                                            value={modpackVersion}
                                            onChange={(e) => setModpackVersion(e.target.value)}
                                            placeholder={t("upload.metadata.versionPlaceholder")}
                                            className="w-full"
                                            required
                                        />
                                    </label>
                                    <label className="block">
                                        <span className="text-sm text-[var(--text-secondary)] mb-2 block">
                                            {t("upload.metadata.sourceLang")}
                                        </span>
                                        <select
                                            value={sourceLang}
                                            onChange={(e) => setSourceLang(e.target.value)}
                                            className="w-full"
                                        >
                                            {LANGUAGE_OPTIONS.map((opt) => (
                                                <option key={opt.value} value={opt.value}>
                                                    {opt.label}
                                                </option>
                                            ))}
                                        </select>
                                    </label>
                                    <label className="block">
                                        <span className="text-sm text-[var(--text-secondary)] mb-2 block">
                                            {t("upload.metadata.targetLang")}
                                        </span>
                                        <select
                                            value={targetLang}
                                            onChange={(e) => setTargetLang(e.target.value)}
                                            className="w-full"
                                        >
                                            {LANGUAGE_OPTIONS.map((opt) => (
                                                <option key={opt.value} value={opt.value}>
                                                    {opt.label}
                                                </option>
                                            ))}
                                        </select>
                                    </label>
                                    {!isManualTranslation && (
                                        <>
                                            <label className="block">
                                                <span className="text-sm text-[var(--text-secondary)] mb-2 block">
                                                    {t("upload.metadata.model")}
                                                </span>
                                                <input
                                                    type="text"
                                                    value={llmModel}
                                                    onChange={(e) => setLlmModel(e.target.value)}
                                                    placeholder={t("upload.metadata.modelPlaceholder")}
                                                    className="w-full"
                                                />
                                            </label>
                                            <label className="block">
                                                <span className="text-sm text-[var(--text-secondary)] mb-2 block">
                                                    {t("upload.metadata.temperature")}
                                                </span>
                                                <input
                                                    type="number"
                                                    step="0.1"
                                                    min="0"
                                                    max="2"
                                                    value={temperature}
                                                    onChange={(e) => setTemperature(e.target.value)}
                                                    className="w-full"
                                                />
                                            </label>
                                            <label className="block">
                                                <span className="text-sm text-[var(--text-secondary)] mb-2 block">
                                                    {t("upload.metadata.batchSize")}
                                                </span>
                                                <input
                                                    type="number"
                                                    min="1"
                                                    value={batchSize}
                                                    onChange={(e) => setBatchSize(e.target.value)}
                                                    className="w-full"
                                                />
                                            </label>
                                        </>
                                    )}
                                </div>
                                <div className="flex flex-wrap gap-6 mt-4">
                                    {!isManualTranslation && (
                                        <label className="flex items-center gap-2 cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={usedGlossary}
                                                onChange={(e) => setUsedGlossary(e.target.checked)}
                                                className="w-5 h-5 rounded border-[var(--border-primary)] bg-[var(--bg-secondary)]"
                                            />
                                            <span className="text-sm text-[var(--text-secondary)]">
                                                {t("upload.metadata.usedGlossary")}
                                            </span>
                                        </label>
                                    )}
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={reviewed}
                                            onChange={(e) => setReviewed(e.target.checked)}
                                            className="w-5 h-5 rounded border-[var(--border-primary)] bg-[var(--bg-secondary)]"
                                        />
                                        <span className="text-sm text-[var(--text-secondary)]">
                                            {t("upload.metadata.reviewed")}
                                        </span>
                                    </label>
                                </div>
                            </div>
                            <div className="flex justify-between mt-6">
                                <Button variant="secondary" onClick={() => setStep(2)}>
                                    ← {t("common.cancel")}
                                </Button>
                                <Button
                                    onClick={handleModpackSubmit}
                                    disabled={loading || !modpackVersion}
                                    loading={loading}
                                >
                                    <Upload className="w-4 h-4" />
                                    {t("upload.submitButton")}
                                </Button>
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* --- MAP FLOW --- */}
            {activeTab === "map" && (
                <>
                    {step === 1 && (
                        <div className="glass rounded-xl p-6">
                            <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-6">
                                맵 선택 또는 생성
                            </h2>

                            {!isCreatingMap ? (
                                <div className="space-y-4">
                                    <label className="block">
                                        <span className="text-sm text-[var(--text-secondary)] mb-2 block">
                                            맵 검색
                                        </span>
                                        <div className="flex gap-3">
                                            <div className="flex-1 relative">
                                                <input
                                                    type="text"
                                                    value={mapSearchQuery}
                                                    onChange={(e) => setMapSearchQuery(e.target.value)}
                                                    placeholder="맵 이름 검색..."
                                                    className="w-full"
                                                    onKeyDown={(e) => e.key === "Enter" && handleSearchMap()}
                                                />
                                            </div>
                                            <Button
                                                onClick={() => handleSearchMap()}
                                                disabled={loading || !mapSearchQuery}
                                                loading={loading}
                                            >
                                                <Search className="w-4 h-4" />
                                                검색
                                            </Button>
                                        </div>
                                    </label>

                                    {selectedMap && (
                                        <div className="mt-6 p-4 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-primary)]">
                                            <div className="flex gap-4">
                                                {selectedMap.thumbnailUrl ? (
                                                    <Image
                                                        src={selectedMap.thumbnailUrl}
                                                        alt={selectedMap.name}
                                                        width={64}
                                                        height={64}
                                                        className="w-16 h-16 rounded-lg object-cover"
                                                    />
                                                ) : (
                                                    <div className="w-16 h-16 rounded-lg bg-[var(--bg-tertiary)] flex items-center justify-center">
                                                        <span className="text-2xl font-bold text-[var(--text-muted)]">
                                                            {selectedMap.name.charAt(0)}
                                                        </span>
                                                    </div>
                                                )}
                                                <div className="flex-1">
                                                    <h3 className="font-semibold text-[var(--text-primary)]">
                                                        {selectedMap.name}
                                                    </h3>
                                                    {selectedMap.author && (
                                                        <p className="text-sm text-[var(--text-muted)]">
                                                            by {selectedMap.author}
                                                        </p>
                                                    )}
                                                    <p className="text-sm text-[var(--text-secondary)] mt-1 line-clamp-2">
                                                        {selectedMap.summary}
                                                    </p>
                                                </div>
                                            </div>
                                            <p className="text-sm text-[var(--accent-primary)] mt-4">
                                                이 맵이 맞나요?
                                            </p>
                                        </div>
                                    )}

                                    <div className="pt-4 border-t border-[var(--border-primary)]">
                                        <p className="text-sm text-[var(--text-secondary)] mb-3">
                                            찾으시는 맵이 없나요?
                                        </p>
                                        <Button variant="secondary" onClick={() => setIsCreatingMap(true)}>
                                            <Plus className="w-4 h-4" />
                                            새로운 맵 등록하기
                                        </Button>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-4 animate-fade-in">
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="font-medium text-[var(--text-primary)]">새 맵 정보 입력</h3>
                                        <Button variant="ghost" size="sm" onClick={() => setIsCreatingMap(false)}>
                                            취소
                                        </Button>
                                    </div>

                                    <label className="block">
                                        <span className="text-sm text-[var(--text-secondary)] mb-2 block">맵 이름 *</span>
                                        <input
                                            type="text"
                                            value={newMapName}
                                            onChange={(e) => setNewMapName(e.target.value)}
                                            className="w-full"
                                            required
                                        />
                                    </label>

                                    <label className="block">
                                        <span className="text-sm text-[var(--text-secondary)] mb-2 block">설명 *</span>
                                        <textarea
                                            value={newMapSummary}
                                            onChange={(e) => setNewMapSummary(e.target.value)}
                                            className="w-full h-24 resize-none"
                                            required
                                        />
                                    </label>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <label className="block">
                                            <span className="text-sm text-[var(--text-secondary)] mb-2 block">제작자</span>
                                            <input
                                                type="text"
                                                value={newMapAuthor}
                                                onChange={(e) => setNewMapAuthor(e.target.value)}
                                                className="w-full"
                                            />
                                        </label>
                                        <label className="block">
                                            <span className="text-sm text-[var(--text-secondary)] mb-2 block">원본 링크</span>
                                            <input
                                                type="url"
                                                value={newMapLink}
                                                onChange={(e) => setNewMapLink(e.target.value)}
                                                className="w-full"
                                                placeholder="https://..."
                                            />
                                        </label>
                                    </div>

                                    <label className="block">
                                        <span className="text-sm text-[var(--text-secondary)] mb-2 block">썸네일 이미지</span>
                                        <input
                                            type="file"
                                            accept="image/*"
                                            onChange={(e) => handleFileChange(e, "thumbnail")}
                                            className="w-full text-sm text-[var(--text-secondary)] file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-[var(--accent-primary)] file:text-white hover:file:bg-[var(--accent-secondary)]"
                                        />
                                    </label>
                                </div>
                            )}

                            <div className="flex justify-end mt-6">
                                <Button
                                    onClick={() => setStep(2)}
                                    disabled={(!selectedMap && !isCreatingMap) || (isCreatingMap && (!newMapName || !newMapSummary))}
                                >
                                    다음 →
                                </Button>
                            </div>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="glass rounded-xl p-6">
                            <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-6">
                                파일 및 버전 정보
                            </h2>
                            <div className="space-y-6">
                                {renderFileInput(
                                    "리소스팩 (ZIP)",
                                    mapResourcePackType,
                                    setMapResourcePackType,
                                    mapResourcePack,
                                    (e) => handleFileChange(e, "mapResourcePack"),
                                    mapResourcePackLink,
                                    setMapResourcePackLink,
                                    "mapResourcePack"
                                )}
                                {renderFileInput(
                                    "덮어쓰기 파일 (ZIP)",
                                    mapOverrideFileType,
                                    setMapOverrideFileType,
                                    mapOverrideFile,
                                    (e) => handleFileChange(e, "mapOverrideFile"),
                                    mapOverrideFileLink,
                                    setMapOverrideFileLink,
                                    "mapOverrideFile"
                                )}

                                <label className="block">
                                    <span className="text-sm text-[var(--text-secondary)] mb-2 block">
                                        맵 버전 *
                                    </span>
                                    <input
                                        type="text"
                                        value={mapVersion}
                                        onChange={(e) => setMapVersion(e.target.value)}
                                        placeholder="예: 1.0.0"
                                        className="w-full"
                                        required
                                    />
                                </label>
                            </div>

                            <div className="flex justify-between mt-6">
                                <Button variant="secondary" onClick={() => setStep(1)}>
                                    ← 이전
                                </Button>
                                <Button
                                    onClick={handleMapSubmit}
                                    disabled={
                                        loading ||
                                        (!((mapResourcePackType === "file" && mapResourcePack) || (mapResourcePackType === "link" && mapResourcePackLink)) &&
                                            !((mapOverrideFileType === "file" && mapOverrideFile) || (mapOverrideFileType === "link" && mapOverrideFileLink))) ||
                                        !mapVersion
                                    }
                                    loading={loading}
                                >
                                    <Upload className="w-4 h-4" />
                                    업로드
                                </Button>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

function LoadingFallback() {
    return (
        <div className="max-w-3xl mx-auto px-4 py-8 flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-[var(--accent-primary)]" />
        </div>
    );
}

export default function UploadPage() {
    return (
        <Suspense fallback={<LoadingFallback />}>
            <UploadContent />
        </Suspense>
    );
}
