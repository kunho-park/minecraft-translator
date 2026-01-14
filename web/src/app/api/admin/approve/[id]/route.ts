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
      id: updated.modpack.id,
      modpackName: updated.modpack.name,
      uploaderEmail: updated.user?.name || "익명",
      createdAt: updated.createdAt,
    });

    return NextResponse.json(updated);
  } catch (error) {
    console.error("Approve error:", error);
    return NextResponse.json(
      { error: "Failed to approve translation" },
      { status: 500 }
    );
  }
}
