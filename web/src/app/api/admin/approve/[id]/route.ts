import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { notifyApproval } from "@/lib/discord";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.isAdmin) {
      return NextResponse.json(
        { error: "Admin access required" },
        { status: 403 }
      );
    }

    const { id } = await params;
    const { searchParams } = new URL(request.url);
    const type = searchParams.get("type") || "modpack";

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

      if (mapTranslation.status !== "pending") {
        return NextResponse.json(
          { error: "Translation is not pending" },
          { status: 400 }
        );
      }

      const updated = await prisma.mapTranslation.update({
        where: { id },
        data: { status: "approved" },
        include: {
          map: true,
          user: true,
        },
      });

      // Send Discord notification (Simplified for Maps)
      // You might want to create a separate notifyMapApproval function
      // For now, we skip or adapt notifyApproval if possible, but notifyApproval expects Modpack fields.
      // Let's skip notification for maps for now or implement it later.

      return NextResponse.json({
        ...updated,
        type: "map",
        modpackVersion: updated.version,
        modpack: {
          ...updated.map,
          logoUrl: updated.map.thumbnailUrl,
        },
      });
    } else {
      const translationPack = await prisma.translationPack.findUnique({
        where: { id },
      });

      if (!translationPack) {
        return NextResponse.json(
          { error: "Translation pack not found" },
          { status: 404 }
        );
      }

      if (translationPack.status !== "pending") {
        return NextResponse.json(
          { error: "Translation pack is not pending" },
          { status: 400 }
        );
      }

      const updated = await prisma.translationPack.update({
        where: { id },
        data: { status: "approved" },
        include: {
          modpack: true,
          user: true,
        },
      });

      // Send Discord notification
      await notifyApproval({
        id: updated.id,
        modpackId: updated.modpack.id,
        modpackName: updated.modpack.name,
        modpackVersion: updated.modpackVersion,
        uploaderName: updated.user?.name,
        sourceLang: updated.sourceLang,
        targetLang: updated.targetLang,
        isManualTranslation: updated.isManualTranslation,
        llmModel: updated.llmModel,
        createdAt: updated.createdAt,
        fileCount: updated.fileCount,
        totalEntries: updated.totalEntries,
        translatedEntries: updated.translatedEntries,
      });

      return NextResponse.json({
        ...updated,
        type: "modpack",
      });
    }
  } catch (error) {
    console.error("Approve error:", error);
    return NextResponse.json(
      { error: "Failed to approve translation" },
      { status: 500 }
    );
  }
}
