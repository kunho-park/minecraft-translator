"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { useState } from "react";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import { FileArchive, FolderCog, BookOpen, ExternalLink } from "lucide-react";

interface TranslationDownloadActionsProps {
    packId: string;
    modpackId: number;
    resourcePackUrl: string | null;
    overrideFileUrl: string | null;
}

export default function TranslationDownloadActions({
    packId,
    modpackId,
    resourcePackUrl,
    overrideFileUrl,
}: TranslationDownloadActionsProps) {
    const t = useTranslations();
    const [downloadedRp, setDownloadedRp] = useState(false);
    const [downloadedOverride, setDownloadedOverride] = useState(false);
    const [showPopup, setShowPopup] = useState(false);

    const handleDownload = (type: "resourcepack" | "override") => {
        const url = type === "resourcepack" ? resourcePackUrl : overrideFileUrl;
        if (!url) return;

        if (url.startsWith("http")) {
            window.open(url, "_blank");
        } else {
            // Trigger download
            const downloadUrl = `/api/translations/${packId}/download?type=${type}`;
            const link = document.createElement("a");
            link.href = downloadUrl;
            link.setAttribute("download", "");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

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
                title={t("modpack.downloadPopup.title")}
            >
                <div className="space-y-6">
                    <p className="text-[var(--text-secondary)] leading-relaxed">
                        {t("modpack.downloadPopup.message")}
                    </p>
                    <div className="flex justify-end gap-3">
                        <Link href="/guide/apply" target="_blank" className="mr-auto">
                            <Button variant="outline" onClick={() => setShowPopup(false)}>
                                <BookOpen className="w-4 h-4 mr-2" />
                                {t("modpack.downloadPopup.guide")}
                            </Button>
                        </Link>
                        <Button variant="ghost" onClick={() => setShowPopup(false)}>
                            {t("modpack.downloadPopup.dismiss")}
                        </Button>
                        <Link href={`/modpacks/${modpackId}/review/${packId}`}>
                            <Button onClick={() => setShowPopup(false)}>
                                {t("modpack.downloadPopup.action")}
                            </Button>
                        </Link>
                    </div>
                </div>
            </Modal>
        </>
    );
}
