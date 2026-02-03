import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import fs from "fs/promises";
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

    // Flattened schema - no versions
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

    // Update status to rejected instead of deleting
    await prisma.translationPack.update({
      where: { id },
      data: { status: "rejected" },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Reject error:", error);
    return NextResponse.json(
      { error: "Failed to reject translation" },
      { status: 500 }
    );
  }
}
