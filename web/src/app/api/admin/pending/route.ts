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

    // Fetch Modpack Translations
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

    // Fetch Map Translations
    const pendingMaps = await prisma.mapTranslation.findMany({
      where: { status: "pending" },
      include: {
        map: true,
        user: {
          select: { name: true, avatar: true, discordId: true },
        },
      },
      orderBy: { createdAt: "asc" },
    });

    // Normalize and combine
    const combined = [
      ...pendingTranslations.map((t) => ({
        ...t,
        type: "modpack",
      })),
      ...pendingMaps.map((t) => ({
        ...t,
        type: "map",
        modpackVersion: t.version,
        modpack: {
          ...t.map,
          logoUrl: t.map.thumbnailUrl,
        },
        resourcePackPath: t.resourcePackUrl,
        overrideFilePath: t.overrideFileUrl,
        isManualTranslation: true,
        llmModel: null,
        temperature: null,
        batchSize: null,
        usedGlossary: false,
        reviewed: false,
        fileCount: null,
        totalEntries: null,
        translatedEntries: null,
        inputTokens: null,
        outputTokens: null,
        totalTokens: null,
        durationSeconds: null,
        handlerStats: null,
        _count: { reviews: 0 },
      })),
    ].sort(
      (a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
    );

    return NextResponse.json(combined);
  } catch (error) {
    console.error("Fetch pending error:", error);
    return NextResponse.json(
      { error: "Failed to fetch pending translations" },
      { status: 500 }
    );
  }
}
