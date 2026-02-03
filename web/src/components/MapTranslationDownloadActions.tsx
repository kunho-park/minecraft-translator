"use client";

import { useTranslations } from "next-intl";
import Button from "@/components/ui/Button";
import { FileArchive, FolderCog } from "lucide-react";

interface MapTranslationDownloadActionsProps {
    translationId: string;
    hasResourcePack: boolean;
    hasOverride: boolean;
}

export default function MapTranslationDownloadActions({
    translationId,
    hasResourcePack,
    hasOverride,
}: MapTranslationDownloadActionsProps) {
    const t = useTranslations();

    const handleDownload = (type: "resourcepack" | "override") => {
        const url = `/api/maps/translations/${translationId}/download?type=${type}`;
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", "");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div className="flex gap-2">
            {hasResourcePack && (
                <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleDownload("resourcepack")}
                >
                    <FileArchive className="w-4 h-4" />
                    {t("translation.files.resourcePack")}
                </Button>
            )}
            {hasOverride && (
                <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleDownload("override")}
                >
                    <FolderCog className="w-4 h-4" />
                    {t("translation.files.overrideFile")}
                </Button>
            )}
        </div>
    );
}
