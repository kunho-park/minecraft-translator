import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import fs from "fs/promises";
import path from "path";

const UPLOADS_DIR = path.join(process.cwd(), "uploads");

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id: packId } = await params;
        const { searchParams } = new URL(request.url);
        const type = searchParams.get("type"); // "resourcepack" or "override"

        if (!type) {
            return NextResponse.json(
                { error: "Missing type parameter" },
                { status: 400 }
            );
        }

        // Get translation pack (flattened schema - no versions)
        const translationPack = await prisma.translationPack.findUnique({
            where: { id: packId },
            include: {
                modpack: {
                    select: { name: true, slug: true },
                },
            },
        });

        if (!translationPack) {
            return NextResponse.json(
                { error: "Translation pack not found" },
                { status: 404 }
            );
        }

        // Only allow downloads for approved translations
        if (translationPack.status !== "approved") {
            return NextResponse.json(
                { error: "Translation is not approved" },
                { status: 403 }
            );
        }

        let filePath: string | null = null;
        let fileName: string;

        if (type === "resourcepack" && translationPack.resourcePackPath) {
            filePath = path.join(UPLOADS_DIR, translationPack.resourcePackPath);
            fileName = `${translationPack.modpack.slug}_${translationPack.modpackVersion}_resourcepack.zip`;
        } else if (type === "override" && translationPack.overrideFilePath) {
            filePath = path.join(UPLOADS_DIR, translationPack.overrideFilePath);
            fileName = `${translationPack.modpack.slug}_${translationPack.modpackVersion}_override.zip`;
        } else {
            return NextResponse.json(
                { error: "File type not available" },
                { status: 404 }
            );
        }

        // Check if file exists
        try {
            await fs.access(filePath);
        } catch {
            return NextResponse.json(
                { error: "File not found" },
                { status: 404 }
            );
        }

        // Read file
        const fileBuffer = await fs.readFile(filePath);

        // Update download count (flattened schema - downloadCount is on TranslationPack)
        await prisma.translationPack.update({
            where: { id: packId },
            data: {
                downloadCount: {
                    increment: 1,
                },
            },
        });

        // Return file
        return new NextResponse(fileBuffer, {
            headers: {
                "Content-Type": "application/zip",
                "Content-Disposition": `attachment; filename="${fileName}"`,
                "Content-Length": fileBuffer.length.toString(),
            },
        });
    } catch (error) {
        console.error("Download error:", error);
        return NextResponse.json(
            { error: "Failed to download file" },
            { status: 500 }
        );
    }
}
