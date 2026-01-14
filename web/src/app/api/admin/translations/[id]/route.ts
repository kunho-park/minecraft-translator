import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { unlink } from "fs/promises";
import path from "path";

const UPLOADS_DIR = path.join(process.cwd(), "uploads");

// DELETE - 번역 삭제 (관리자 전용) - Flattened schema
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions);
  const { id } = await params;

  if (!session?.user?.isAdmin) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 403 });
  }

  try {
    // 번역팩 조회 (파일 경로 포함)
    const pack = await prisma.translationPack.findUnique({
      where: { id },
      select: {
        resourcePackPath: true,
        overrideFilePath: true,
      },
    });

    if (!pack) {
      return NextResponse.json({ error: "Translation not found" }, { status: 404 });
    }

    // 파일 삭제
    if (pack.resourcePackPath) {
      try {
        await unlink(path.join(UPLOADS_DIR, pack.resourcePackPath));
      } catch (e) {
        console.error("Failed to delete resource pack:", e);
      }
    }
    if (pack.overrideFilePath) {
      try {
        await unlink(path.join(UPLOADS_DIR, pack.overrideFilePath));
      } catch (e) {
        console.error("Failed to delete override file:", e);
      }
    }

    // DB에서 삭제 (Cascade로 reviews도 삭제됨)
    await prisma.translationPack.delete({
      where: { id },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error deleting translation:", error);
    return NextResponse.json(
      { error: "Failed to delete translation" },
      { status: 500 }
    );
  }
}

// PATCH - 번역 수정 (관리자 전용)
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions);
  const { id } = await params;

  if (!session?.user?.isAdmin) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 403 });
  }

  try {
    const body = await request.json();
    const { status, sourceLang, targetLang } = body;

    const updatedPack = await prisma.translationPack.update({
      where: { id },
      data: {
        ...(status && { status }),
        ...(sourceLang && { sourceLang }),
        ...(targetLang && { targetLang }),
      },
      include: {
        modpack: {
          select: {
            name: true,
          },
        },
      },
    });

    return NextResponse.json({ success: true, pack: updatedPack });
  } catch (error) {
    console.error("Error updating translation:", error);
    return NextResponse.json(
      { error: "Failed to update translation" },
      { status: 500 }
    );
  }
}
