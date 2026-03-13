import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { downloadFile } from "@/lib/storage";

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

        if (translation.status !== "approved" && !session?.user?.isAdmin) {
            return NextResponse.json(
                { error: "Translation is not approved" },
                { status: 403 }
            );
        }

        let r2Key: string | null = null;
        let fileName: string;

        if (type === "resourcepack" && translation.resourcePackUrl) {
            r2Key = translation.resourcePackUrl;
            const ext = translation.resourcePackUrl.split(".").pop() || "zip";
            fileName = `${translation.map.slug}_${translation.version}_resourcepack.${ext}`;
        } else if (type === "override" && translation.overrideFileUrl) {
            r2Key = translation.overrideFileUrl;
            const ext = translation.overrideFileUrl.split(".").pop() || "zip";
            fileName = `${translation.map.slug}_${translation.version}_override.${ext}`;
        } else {
            return NextResponse.json(
                { error: "File type not available" },
                { status: 404 }
            );
        }

        // External link - redirect
        if (r2Key.startsWith("http")) {
            await prisma.mapTranslation.update({
                where: { id: translationId },
                data: { downloadCount: { increment: 1 } },
            });
            return NextResponse.redirect(r2Key);
        }

        const fileBuffer = await downloadFile(r2Key);

        const ext = r2Key.split(".").pop()?.toLowerCase();
        let contentType = "application/octet-stream";
        if (ext === "zip") contentType = "application/zip";
        else if (ext === "jar") contentType = "application/java-archive";

        await prisma.mapTranslation.update({
            where: { id: translationId },
            data: { downloadCount: { increment: 1 } },
        });

        return new NextResponse(new Uint8Array(fileBuffer), {
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
