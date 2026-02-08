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

        // Always go through the API to ensure download count is incremented
        window.open(`/api/maps/translations/${translationId}/download?type=${type}`, "_blank");
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
