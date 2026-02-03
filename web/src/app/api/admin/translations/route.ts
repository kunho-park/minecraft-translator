import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

// GET - 모든 번역 목록 (관리자 전용)
export async function GET(request: Request) {
  const session = await getServerSession(authOptions);

  if (!session?.user?.isAdmin) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 403 });
  }

  try {
    const { searchParams } = new URL(request.url);
    const q = searchParams.get("q");

    const whereModpack = q
      ? {
        OR: [
          { modpack: { name: { contains: q } } },
          { user: { name: { contains: q } } },
          { user: { discordId: { contains: q } } },
        ],
      }
      : undefined;

    const whereMap = q
      ? {
        OR: [
          { map: { name: { contains: q } } },
          { user: { name: { contains: q } } },
          { user: { discordId: { contains: q } } },
        ],
      }
      : undefined;

    const translations = await prisma.translationPack.findMany({
      where: whereModpack,
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

    const mapTranslations = await prisma.mapTranslation.findMany({
      where: whereMap,
      include: {
        map: {
          select: {
            id: true,
            name: true,
            slug: true,
            thumbnailUrl: true,
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
      orderBy: { createdAt: "desc" },
    });

    // Normalize and combine
    const combined = [
      ...translations.map((t) => ({
        ...t,
        type: "modpack",
      })),
      ...mapTranslations.map((t) => ({
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
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );

    return NextResponse.json(combined);
  } catch (error) {
    console.error("Error fetching translations:", error);
    return NextResponse.json(
      { error: "Failed to fetch translations" },
      { status: 500 }
    );
  }
}
