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
        const { id: packId } = await params;
        const { searchParams } = new URL(request.url);
        const type = searchParams.get("type"); // "resourcepack" or "override"

        if (!type) {
            return NextResponse.json(
                { error: "Missing type parameter" },
                { status: 400 }
            );
        }

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

        if (translationPack.status !== "approved" && !session?.user?.isAdmin) {
            return NextResponse.json(
                { error: "Translation is not approved" },
                { status: 403 }
            );
        }

        let r2Key: string | null = null;
        let fileName: string;

        if (type === "resourcepack" && translationPack.resourcePackPath) {
            r2Key = translationPack.resourcePackPath;
            fileName = `${translationPack.modpack.slug}_${translationPack.modpackVersion}_resourcepack.zip`;
        } else if (type === "override" && translationPack.overrideFilePath) {
            r2Key = translationPack.overrideFilePath;
            fileName = `${translationPack.modpack.slug}_${translationPack.modpackVersion}_override.zip`;
        } else {
            return NextResponse.json(
                { error: "File type not available" },
                { status: 404 }
            );
        }

        // External link - redirect
        if (r2Key.startsWith("http")) {
            await prisma.translationPack.update({
                where: { id: packId },
                data: { downloadCount: { increment: 1 } },
            });
            return NextResponse.redirect(r2Key);
        }

        const fileBuffer = await downloadFile(r2Key);

        await prisma.translationPack.update({
            where: { id: packId },
            data: { downloadCount: { increment: 1 } },
        });

        return new NextResponse(new Uint8Array(fileBuffer), {
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
