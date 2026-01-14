import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { getCurseForgeClient } from "@/lib/curseforge";

export async function POST() {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.isAdmin) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const client = getCurseForgeClient();

    // Get all modpacks
    const modpacks = await prisma.modpack.findMany({
      select: {
        id: true,
        curseforgeId: true,
        name: true,
      },
    });

    const results = {
      total: modpacks.length,
      updated: 0,
      failed: 0,
      errors: [] as string[],
    };

    // Update each modpack
    for (const modpack of modpacks) {
      try {
        const cfMod = await client.getMod(modpack.curseforgeId);

        // Extract categories (tags)
        const categories = cfMod.categories
          .filter((cat) => !cat.isClass && cat.classId === 4471)
          .map((cat) => ({ name: cat.name, slug: cat.slug }));

        // Extract game versions
        const gameVersions = cfMod.latestFiles
          .flatMap((f) => f.gameVersions)
          .filter((v, i, arr) => arr.indexOf(v) === i)
          .filter((v) => v.match(/^\d+\.\d+/))
          .sort()
          .reverse();

        await prisma.modpack.update({
          where: { id: modpack.id },
          data: {
            name: cfMod.name,
            slug: cfMod.slug,
            summary: cfMod.summary,
            logoUrl: cfMod.logo?.thumbnailUrl || null,
            author: cfMod.authors[0]?.name || null,
            categories: JSON.stringify(categories),
            gameVersions: JSON.stringify(gameVersions),
            totalDownloads: cfMod.downloadCount,
            cachedAt: new Date(),
          },
        });

        results.updated++;
      } catch (error) {
        results.failed++;
        results.errors.push(
          `${modpack.name}: ${error instanceof Error ? error.message : "Unknown error"}`
        );
      }

      // Rate limiting - wait 100ms between requests
      await new Promise((resolve) => setTimeout(resolve, 100));
    }

    return NextResponse.json(results);
  } catch (error) {
    console.error("Failed to refresh modpacks:", error);
    return NextResponse.json(
      { error: "Failed to refresh modpacks" },
      { status: 500 }
    );
  }
}
