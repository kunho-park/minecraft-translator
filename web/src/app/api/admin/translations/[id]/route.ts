import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { deleteFile } from "@/lib/storage";

// DELETE - 번역 삭제 (관리자 전용)
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions);
  const { id } = await params;
  const { searchParams } = new URL(request.url);
  const type = searchParams.get("type") || "modpack";

  if (!session?.user?.isAdmin) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 403 });
  }

  try {
    if (type === "map") {
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
    } else {
      const pack = await prisma.translationPack.findUnique({
        where: { id },
        select: {
          resourcePackPath: true,
          overrideFilePath: true,
        },
      });

      if (!pack) {
        return NextResponse.json(
          { error: "Translation not found" },
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
    }
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
  const { searchParams } = new URL(request.url);
  const type = searchParams.get("type") || "modpack";

  if (!session?.user?.isAdmin) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 403 });
  }

  try {
    const body = await request.json();
    const { status, sourceLang, targetLang, discordId } = body;

    let userIdUpdate = {};
    if (discordId !== undefined) {
      if (discordId === "") {
        // Optionally allow unassigning?
      } else {
        const user = await prisma.user.findUnique({
          where: { discordId },
        });

        if (!user) {
          return NextResponse.json(
            { error: "해당 Discord ID를 가진 사용자를 찾을 수 없습니다." },
            { status: 400 }
          );
        }
        userIdUpdate = { userId: user.id };
      }
    }

    if (type === "map") {
      const updated = await prisma.mapTranslation.update({
        where: { id },
        data: {
          ...(status && { status }),
          ...(sourceLang && { sourceLang }),
          ...(targetLang && { targetLang }),
          ...userIdUpdate,
        },
        include: {
          map: true,
          user: true,
        },
      });

      return NextResponse.json({
        success: true,
        pack: {
          ...updated,
          type: "map",
          modpackVersion: updated.version,
          modpack: {
            ...updated.map,
            logoUrl: updated.map.thumbnailUrl,
          },
        },
      });
    } else {
      const updatedPack = await prisma.translationPack.update({
        where: { id },
        data: {
          ...(status && { status }),
          ...(sourceLang && { sourceLang }),
          ...(targetLang && { targetLang }),
          ...userIdUpdate,
        },
        include: {
          modpack: {
            select: {
              name: true,
            },
          },
          user: {
            select: {
              name: true,
              avatar: true,
              discordId: true,
            },
          },
        },
      });

      return NextResponse.json({
        success: true,
        pack: {
          ...updatedPack,
          type: "modpack",
        },
      });
    }
  } catch (error) {
    console.error("Error updating translation:", error);
    return NextResponse.json(
      { error: "Failed to update translation" },
      { status: 500 }
    );
  }
}
