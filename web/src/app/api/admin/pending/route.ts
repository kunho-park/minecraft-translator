import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function GET() {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.isAdmin) {
      return NextResponse.json(
        { error: "Admin access required" },
        { status: 403 }
      );
    }

    // Flattened schema - no versions
    const pendingTranslations = await prisma.translationPack.findMany({
      where: { status: "pending" },
      include: {
        modpack: true,
        user: {
          select: { name: true, avatar: true, discordId: true },
        },
      },
      orderBy: { createdAt: "asc" },
    });

    return NextResponse.json(pendingTranslations);
  } catch (error) {
    console.error("Fetch pending error:", error);
    return NextResponse.json(
      { error: "Failed to fetch pending translations" },
      { status: 500 }
    );
  }
}
