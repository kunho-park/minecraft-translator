"use client";

import { useTranslations } from "next-intl";
import Button from "@/components/ui/Button";
import { FileArchive, FolderCog, ExternalLink } from "lucide-react";

interface MapTranslationDownloadActionsProps {
    translationId: string;
    resourcePackUrl: string | null;
    overrideFileUrl: string | null;
}

export default function MapTranslationDownloadActions({
    translationId,
    resourcePackUrl,
    overrideFileUrl,
}: MapTranslationDownloadActionsProps) {
    const t = useTranslations();

    const handleDownload = (type: "resourcepack" | "override") => {
        const url = type === "resourcepack" ? resourcePackUrl : overrideFileUrl;
        if (!url) return;

        if (url.startsWith("http")) {
            window.open(url, "_blank");
        } else {
            const downloadUrl = `/api/maps/translations/${translationId}/download?type=${type}`;
            const link = document.createElement("a");
            link.href = downloadUrl;
            link.setAttribute("download", "");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    };

    return (
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
    );
}
