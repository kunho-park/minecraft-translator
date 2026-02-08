import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import fs from "fs/promises";
import path from "path";

const UPLOADS_DIR = path.join(process.cwd(), "uploads");

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const session = await getServerSession(authOptions);
        const { id: translationId } = await params;
        const { searchParams } = new URL(request.url);
        const type = searchParams.get("type"); // "resourcepack" or "override"

        if (!type) {
            return NextResponse.json(
                { error: "Missing type parameter" },
                { status: 400 }
            );
        }

        // Get map translation
        const translation = await prisma.mapTranslation.findUnique({
            where: { id: translationId },
            include: {
                map: {
                    select: { name: true, slug: true },
                },
            },
        });

        if (!translation) {
            return NextResponse.json(
                { error: "Translation not found" },
                { status: 404 }
            );
        }

        // Only allow downloads for approved translations or if user is admin
        if (translation.status !== "approved" && !session?.user?.isAdmin) {
            return NextResponse.json(
                { error: "Translation is not approved" },
                { status: 403 }
            );
        }

        let fileRelativePath: string | null = null;
        let fileName: string;

        if (type === "resourcepack" && translation.resourcePackUrl) {
            fileRelativePath = translation.resourcePackUrl;
            const ext = translation.resourcePackUrl.split(".").pop() || "zip";
            fileName = `${translation.map.slug}_${translation.version}_resourcepack.${ext}`;
        } else if (type === "override" && translation.overrideFileUrl) {
            fileRelativePath = translation.overrideFileUrl;
            const ext = translation.overrideFileUrl.split(".").pop() || "zip";
            fileName = `${translation.map.slug}_${translation.version}_override.${ext}`;
        } else {
            return NextResponse.json(
                { error: "File type not available" },
                { status: 404 }
            );
        }

        // If URL is external, increment download count and redirect to it
        if (fileRelativePath.startsWith("http")) {
            await prisma.mapTranslation.update({
                where: { id: translationId },
                data: {
                    downloadCount: {
                        increment: 1,
                    },
                },
            });
            return NextResponse.redirect(fileRelativePath);
        }

        // Build file path (relative paths are like "maps/uuid_resourcepack.zip")
        const filePath = path.join(UPLOADS_DIR, fileRelativePath);

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

        // Determine content type
        const ext = filePath.split(".").pop()?.toLowerCase();
        let contentType = "application/octet-stream";
        if (ext === "zip") contentType = "application/zip";
        else if (ext === "jar") contentType = "application/java-archive";

        // Update download count
        await prisma.mapTranslation.update({
            where: { id: translationId },
            data: {
                downloadCount: {
                    increment: 1,
                },
            },
        });

        // Return file
        return new NextResponse(fileBuffer, {
            headers: {
                "Content-Type": contentType,
                "Content-Disposition": `attachment; filename="${fileName}"`,
                "Content-Length": fileBuffer.length.toString(),
            },
        });
    } catch (error) {
        console.error("Map translation download error:", error);
        return NextResponse.json(
            { error: "Failed to download file" },
            { status: 500 }
        );
    }
}
