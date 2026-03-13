import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { deleteFile } from "@/lib/storage";

// PATCH - 모드팩 번역 수정 (관리자 전용)
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
            modpackVersion,
            sourceLang,
            targetLang,
            status,
            isManualTranslation,
            llmModel,
            temperature,
            batchSize,
            usedGlossary,
            reviewed,
        } = body;

        const updated = await prisma.translationPack.update({
            where: { id },
            data: {
                ...(modpackVersion !== undefined && { modpackVersion }),
                ...(sourceLang !== undefined && { sourceLang }),
                ...(targetLang !== undefined && { targetLang }),
                ...(status !== undefined && { status }),
                ...(isManualTranslation !== undefined && { isManualTranslation }),
                ...(llmModel !== undefined && { llmModel: llmModel || null }),
                ...(temperature !== undefined && { temperature: temperature !== null ? parseFloat(temperature) : null }),
                ...(batchSize !== undefined && { batchSize: batchSize !== null ? parseInt(batchSize) : null }),
                ...(usedGlossary !== undefined && { usedGlossary }),
                ...(reviewed !== undefined && { reviewed }),
            },
            include: {
                user: { select: { name: true, avatar: true } },
                _count: { select: { reviews: true } },
            },
        });

        return NextResponse.json({ success: true, pack: updated });
    } catch (error) {
        console.error("Update translation pack error:", error);
        return NextResponse.json(
            { error: "Failed to update translation pack" },
            { status: 500 }
        );
    }
}

// DELETE - 모드팩 번역 삭제 (관리자 전용)
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

        const pack = await prisma.translationPack.findUnique({
            where: { id },
            select: {
                resourcePackPath: true,
                overrideFilePath: true,
            },
        });

        if (!pack) {
            return NextResponse.json(
                { error: "Translation pack not found" },
                { status: 404 }
            );
        }

        if (pack.resourcePackPath && !pack.resourcePackPath.startsWith("http")) {
            try {
                await deleteFile(pack.resourcePackPath);
            } catch (e) {
                console.error("Failed to delete resource pack:", e);
            }
        }
        if (pack.overrideFilePath && !pack.overrideFilePath.startsWith("http")) {
            try {
                await deleteFile(pack.overrideFilePath);
            } catch (e) {
                console.error("Failed to delete override file:", e);
            }
        }

        await prisma.translationPack.delete({
            where: { id },
        });

        return NextResponse.json({ success: true });
    } catch (error) {
        console.error("Delete translation pack error:", error);
        return NextResponse.json(
            { error: "Failed to delete translation pack" },
            { status: 500 }
        );
    }
}
