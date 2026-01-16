import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { notifySubmission } from "@/lib/discord";
import { getCurseForgeClient } from "@/lib/curseforge";
import { v4 as uuidv4 } from "uuid";
import fs from "fs/promises";
import path from "path";

// Ensure uploads directory exists
const UPLOADS_DIR = path.join(process.cwd(), "uploads");

async function ensureUploadsDir() {
  try {
    await fs.access(UPLOADS_DIR);
  } catch {
    await fs.mkdir(UPLOADS_DIR, { recursive: true });
  }
}

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    const formData = await request.formData();
    const curseforgeId = formData.get("curseforgeId") as string;
    const modpackVersion = formData.get("modpackVersion") as string;
    const sourceLang = formData.get("sourceLang") as string || "en_us";
    const targetLang = formData.get("targetLang") as string || "ko_kr";
    const isManualTranslation = formData.get("isManualTranslation") === "true";
    const llmModel = formData.get("llmModel") as string | null;
    const temperature = formData.get("temperature") as string | null;
    const batchSize = formData.get("batchSize") as string | null;
    const usedGlossary = formData.get("usedGlossary") === "true";
    const reviewed = formData.get("reviewed") === "true";
    const resourcePack = formData.get("resourcePack") as File | null;
    const overrideFile = formData.get("overrideFile") as File | null;
    const anonymous = formData.get("anonymous") === "true";

    // 번역 통계 필드
    const fileCount = formData.get("fileCount") as string | null;
    const totalEntries = formData.get("totalEntries") as string | null;
    const translatedEntries = formData.get("translatedEntries") as string | null;
    const inputTokens = formData.get("inputTokens") as string | null;
    const outputTokens = formData.get("outputTokens") as string | null;
    const totalTokens = formData.get("totalTokens") as string | null;
    const handlerStats = formData.get("handlerStats") as string | null;
    const durationSeconds = formData.get("durationSeconds") as string | null;

    // Validate required fields
    if (!curseforgeId || !modpackVersion) {
      return NextResponse.json(
        { error: "Missing required fields" },
        { status: 400 }
      );
    }

    if (!resourcePack && !overrideFile) {
      return NextResponse.json(
        { error: "At least one file is required" },
        { status: 400 }
      );
    }

    // Check if modpack exists in DB, if not fetch from CurseForge
    const cfId = parseInt(curseforgeId, 10);
    let modpack = await prisma.modpack.findUnique({
      where: { curseforgeId: cfId },
    });

    if (!modpack) {
      // Fetch from CurseForge
      const client = getCurseForgeClient();
      const cfMod = await client.getMod(cfId);

      // Extract categories (tags)
      const categories = cfMod.categories
        .filter((cat) => !cat.isClass && cat.classId === 4471)
        .map((cat) => ({ name: cat.name, slug: cat.slug }));

      modpack = await prisma.modpack.create({
        data: {
          curseforgeId: cfId,
          name: cfMod.name,
          slug: cfMod.slug,
          summary: cfMod.summary,
          logoUrl: cfMod.logo?.thumbnailUrl || null,
          author: cfMod.authors[0]?.name || null,
          categories: JSON.stringify(categories),
          gameVersions: JSON.stringify(
            cfMod.latestFiles
              .flatMap((f) => f.gameVersions)
              .filter((v, i, arr) => arr.indexOf(v) === i)
              .filter((v) => v.match(/^\d+\.\d+/))
          ),
          totalDownloads: cfMod.downloadCount,
        },
      });
    }

    // Ensure uploads directory exists
    await ensureUploadsDir();

    // Save files
    const packId = uuidv4();
    const packDir = path.join(UPLOADS_DIR, packId);
    await fs.mkdir(packDir, { recursive: true });

    let resourcePackPath: string | null = null;
    let overrideFilePath: string | null = null;

    if (resourcePack) {
      const rpFileName = `${packId}_resourcepack.zip`;
      const rpPath = path.join(packDir, rpFileName);
      const rpBuffer = Buffer.from(await resourcePack.arrayBuffer());
      await fs.writeFile(rpPath, rpBuffer);
      resourcePackPath = `${packId}/${rpFileName}`;
    }

    if (overrideFile) {
      const ofFileName = `${packId}_override.zip`;
      const ofPath = path.join(packDir, ofFileName);
      const ofBuffer = Buffer.from(await overrideFile.arrayBuffer());
      await fs.writeFile(ofPath, ofBuffer);
      overrideFilePath = `${packId}/${ofFileName}`;
    }

    // Create translation pack (flattened schema - no versions)
    const translationPack = await prisma.translationPack.create({
      data: {
        id: packId,
        modpackId: modpack.id,
        modpackVersion,
        userId: !anonymous && session?.user?.id ? session.user.id : null,
        sourceLang,
        targetLang,
        status: "pending",
        resourcePackPath,
        overrideFilePath,
        isManualTranslation,
        llmModel: isManualTranslation ? null : llmModel,
        temperature: isManualTranslation ? null : (temperature ? parseFloat(temperature) : null),
        batchSize: isManualTranslation ? null : (batchSize ? parseInt(batchSize, 10) : null),
        usedGlossary: isManualTranslation ? false : usedGlossary,
        reviewed,
        // 번역 통계 필드
        fileCount: fileCount ? parseInt(fileCount, 10) : null,
        totalEntries: totalEntries ? parseInt(totalEntries, 10) : null,
        translatedEntries: translatedEntries ? parseInt(translatedEntries, 10) : null,
        inputTokens: inputTokens ? parseInt(inputTokens, 10) : null,
        outputTokens: outputTokens ? parseInt(outputTokens, 10) : null,
        totalTokens: totalTokens ? parseInt(totalTokens, 10) : null,
        handlerStats: handlerStats || null,
        durationSeconds: durationSeconds ? parseFloat(durationSeconds) : null,
      },
    });

    // Send submission notification
    await notifySubmission({
      id: translationPack.id,
      modpackId: modpack.id,
      modpackName: modpack.name,
      modpackVersion: translationPack.modpackVersion,
      uploaderName: !anonymous ? session?.user?.name : undefined,
      sourceLang: translationPack.sourceLang,
      targetLang: translationPack.targetLang,
      isManualTranslation: translationPack.isManualTranslation,
      llmModel: translationPack.llmModel,
      createdAt: translationPack.createdAt,
      fileCount: translationPack.fileCount,
      totalEntries: translationPack.totalEntries,
      translatedEntries: translationPack.translatedEntries,
    });

    return NextResponse.json({
      success: true,
      packId: translationPack.id,
      message: "Translation uploaded successfully. It will be reviewed by an admin.",
    });
  } catch (error) {
    console.error("Upload error:", error);
    return NextResponse.json(
      { error: "Failed to upload translation" },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const modpackId = searchParams.get("modpackId");

  try {
    // Flattened schema - no versions
    const translations = await prisma.translationPack.findMany({
      where: {
        status: "approved",
        ...(modpackId ? { modpackId: parseInt(modpackId, 10) } : {}),
      },
      include: {
        modpack: true,
        user: {
          select: { name: true, avatar: true },
        },
        _count: {
          select: { reviews: true },
        },
      },
      orderBy: { createdAt: "desc" },
      take: 50,
    });

    return NextResponse.json(translations);
  } catch (error) {
    console.error("Fetch translations error:", error);
    return NextResponse.json(
      { error: "Failed to fetch translations" },
      { status: 500 }
    );
  }
}
