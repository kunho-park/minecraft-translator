import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

// GET - 모든 번역 목록 (관리자 전용) - Flattened schema
export async function GET() {
  const session = await getServerSession(authOptions);

  if (!session?.user?.isAdmin) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 403 });
  }

  try {
    const translations = await prisma.translationPack.findMany({
      include: {
        modpack: {
          select: {
            id: true,
            name: true,
            slug: true,
            logoUrl: true,
          },
        },
        user: {
          select: {
            name: true,
            avatar: true,
            discordId: true,
          },
        },
        _count: {
          select: { reviews: true },
        },
      },
      orderBy: { createdAt: "desc" },
    });

    return NextResponse.json(translations);
  } catch (error) {
    console.error("Error fetching translations:", error);
    return NextResponse.json(
      { error: "Failed to fetch translations" },
      { status: 500 }
    );
  }
}
