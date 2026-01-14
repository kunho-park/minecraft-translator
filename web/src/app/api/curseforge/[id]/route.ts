import { NextRequest, NextResponse } from "next/server";
import { getCurseForgeClient, extractCurseForgeId } from "@/lib/curseforge";

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const modId = extractCurseForgeId(id);

        if (!modId) {
            return NextResponse.json(
                { error: "Invalid modpack ID" },
                { status: 400 }
            );
        }

        const client = getCurseForgeClient();
        const mod = await client.getMod(modId);

        // Only allow modpacks (classId 4471)
        const isModpack = mod.categories.some(
            (cat) => cat.classId === 4471 || cat.id === 4471
        );
        if (!isModpack) {
            return NextResponse.json(
                { error: "This is not a modpack" },
                { status: 400 }
            );
        }

        // Extract non-class categories (actual tags)
        const tags = mod.categories
            .filter((cat) => !cat.isClass && cat.classId === 4471)
            .map((cat) => ({ name: cat.name, slug: cat.slug }));

        return NextResponse.json({
            id: mod.id,
            name: mod.name,
            slug: mod.slug,
            summary: mod.summary,
            logoUrl: mod.logo?.thumbnailUrl || null,
            author: mod.authors[0]?.name || null,
            categories: tags,
            gameVersions: mod.latestFiles
                .flatMap((f) => f.gameVersions)
                .filter((v, i, arr) => arr.indexOf(v) === i)
                .filter((v) => v.match(/^\d+\.\d+/))
                .sort()
                .reverse(),
            downloadCount: mod.downloadCount,
            websiteUrl: mod.links.websiteUrl,
        });
    } catch (error) {
        console.error("CurseForge API error:", error);
        return NextResponse.json(
            { error: "Failed to fetch modpack from CurseForge" },
            { status: 500 }
        );
    }
}
