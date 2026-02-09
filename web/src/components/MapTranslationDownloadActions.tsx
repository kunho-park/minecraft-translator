"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { useState } from "react";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import { FileArchive, FolderCog, ExternalLink, BookOpen, AlertCircle } from "lucide-react";

interface MapTranslationDownloadActionsProps {
    translationId: string;
    mapId: number;
    resourcePackUrl: string | null;
    overrideFileUrl: string | null;
}

export default function MapTranslationDownloadActions({
    translationId,
    mapId,
    resourcePackUrl,
    overrideFileUrl,
}: MapTranslationDownloadActionsProps) {
    const t = useTranslations();
    const [downloadedRp, setDownloadedRp] = useState(false);
    const [downloadedOverride, setDownloadedOverride] = useState(false);
    const [showPopup, setShowPopup] = useState(false);

    const handleDownload = (type: "resourcepack" | "override") => {
        const url = type === "resourcepack" ? resourcePackUrl : overrideFileUrl;
        if (!url) return;

        // Always go through the API to ensure download count is incremented
        window.open(`/api/maps/translations/${translationId}/download?type=${type}`, "_blank");

        // Update state
        if (type === "resourcepack") {
            setDownloadedRp(true);
            // If there's no override, OR if override is already downloaded, show popup
            if (!overrideFileUrl || downloadedOverride) {
                setShowPopup(true);
            }
        } else {
            setDownloadedOverride(true);
            // If resource pack is already downloaded, show popup
            if (downloadedRp) {
                setShowPopup(true);
            }
        }
    };

    return (
        <>
            <div className="flex gap-2">
                {resourcePackUrl && (
                    <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => handleDownload("resourcepack")}
                    >
                        {resourcePackUrl.startsWith("http") ? <ExternalLink className="w-4 h-4" /> : <FileArchive className="w-4 h-4" />}
                        {t("translation.files.resourcePack")}
                    </Button>
                )}
                {overrideFileUrl && (
                    <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => handleDownload("override")}
                    >
                        {overrideFileUrl.startsWith("http") ? <ExternalLink className="w-4 h-4" /> : <FolderCog className="w-4 h-4" />}
                        {t("translation.files.overrideFile")}
                    </Button>
                )}
            </div>

            <Modal
                isOpen={showPopup}
                onClose={() => setShowPopup(false)}
                title={t("maps.downloadPopup.title")}
            >
                <div className="space-y-6">
                    <p className="text-[var(--text-secondary)] leading-relaxed">
                        {t("maps.downloadPopup.message")}
                    </p>
                    <div className="p-3 rounded-lg bg-[var(--status-info)]/10 border border-[var(--status-info)]/20 flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 text-[var(--status-info)] flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-[var(--status-info)]">
                            {t("maps.downloadPopup.guideNotice")}
                        </p>
                    </div>
                    <div className="flex justify-end gap-3">
                        <Button variant="ghost" onClick={() => setShowPopup(false)}>
                            {t("maps.downloadPopup.dismiss")}
                        </Button>
                        <Link href={`/maps/${mapId}/review/${translationId}`}>
                            <Button onClick={() => setShowPopup(false)}>
                                {t("maps.downloadPopup.action")}
                            </Button>
                        </Link>
                    </div>
                </div>
            </Modal>
        </>
    );
}
