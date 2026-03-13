import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { deleteFile } from "@/lib/storage";

// PATCH - 맵 번역 수정 (관리자 전용)
export async function PATCH(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user?.isAdmin) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 403 });
        }

        const { id } = await params;
        const body = await request.json();
        const {
            version,
            sourceLang,
            targetLang,
            status,
            resourcePackUrl,
            overrideFileUrl,
            originalLink,
            minecraftVersion,
        } = body;

        const updated = await prisma.mapTranslation.update({
            where: { id },
            data: {
                ...(version !== undefined && { version }),
                ...(sourceLang !== undefined && { sourceLang }),
                ...(targetLang !== undefined && { targetLang }),
                ...(status !== undefined && { status }),
                ...(resourcePackUrl !== undefined && { resourcePackUrl: resourcePackUrl || null }),
                ...(overrideFileUrl !== undefined && { overrideFileUrl: overrideFileUrl || null }),
                ...(originalLink !== undefined && { originalLink: originalLink || null }),
                ...(minecraftVersion !== undefined && { minecraftVersion: minecraftVersion || null }),
            },
            include: {
                user: { select: { name: true, avatar: true } },
            },
        });

        return NextResponse.json({ success: true, translation: updated });
    } catch (error) {
        console.error("Update map translation error:", error);
        return NextResponse.json(
            { error: "Failed to update map translation" },
            { status: 500 }
        );
    }
}

// DELETE - 맵 번역 삭제 (관리자 전용)
export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user?.isAdmin) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 403 });
        }

        const { id } = await params;

        const mapTranslation = await prisma.mapTranslation.findUnique({
            where: { id },
        });

        if (!mapTranslation) {
            return NextResponse.json(
                { error: "Map translation not found" },
                { status: 404 }
            );
        }

        if (mapTranslation.resourcePackUrl && !mapTranslation.resourcePackUrl.startsWith("http")) {
            try {
                await deleteFile(mapTranslation.resourcePackUrl);
            } catch (e) {
                console.error("Failed to delete map resource pack:", e);
            }
        }
        if (mapTranslation.overrideFileUrl && !mapTranslation.overrideFileUrl.startsWith("http")) {
            try {
                await deleteFile(mapTranslation.overrideFileUrl);
            } catch (e) {
                console.error("Failed to delete map override file:", e);
            }
        }

        await prisma.mapTranslation.delete({
            where: { id },
        });

        return NextResponse.json({ success: true });
    } catch (error) {
        console.error("Delete map translation error:", error);
        return NextResponse.json(
            { error: "Failed to delete map translation" },
            { status: 500 }
        );
    }
}
