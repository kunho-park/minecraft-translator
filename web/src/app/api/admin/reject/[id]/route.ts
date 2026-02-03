import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import path from "path";

const UPLOADS_DIR = path.join(process.cwd(), "uploads");

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

      await prisma.mapTranslation.update({
        where: { id },
        data: { status: "rejected" },
      });

      return NextResponse.json({ success: true });
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

      await prisma.translationPack.update({
        where: { id },
        data: { status: "rejected" },
      });

      return NextResponse.json({ success: true });
    }
  } catch (error) {
    console.error("Reject error:", error);
    return NextResponse.json(
      { error: "Failed to reject translation" },
      { status: 500 }
    );
  }
}
