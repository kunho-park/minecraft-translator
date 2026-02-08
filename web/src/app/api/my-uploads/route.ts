import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function GET() {
  const session = await getServerSession(authOptions);

  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    // Flattened schema - no versions
    const translationPacks = await prisma.translationPack.findMany({
      where: {
        userId: session.user.id,
      },
      include: {
        modpack: {
          select: {
            id: true,
            name: true,
            slug: true,
            logoUrl: true,
          },
        },
      },
      orderBy: {
        createdAt: "desc",
      },
    });

    const mapTranslations = await prisma.mapTranslation.findMany({
      where: {
        userId: session.user.id,
      },
      include: {
        map: {
          select: {
            id: true,
            name: true,
            thumbnailUrl: true,
          },
        },
      },
      orderBy: {
        createdAt: "desc",
      },
    });

    return NextResponse.json({
      uploads: translationPacks,
      mapUploads: mapTranslations,
    });
  } catch (error) {
    console.error("Error fetching user uploads:", error);
    return NextResponse.json(
      { error: "Failed to fetch uploads" },
      { status: 500 }
    );
  }
}
