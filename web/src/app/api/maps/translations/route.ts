import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { uploadFile } from "@/lib/storage";
import { v4 as uuidv4 } from "uuid";

export async function POST(request: NextRequest) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const formData = await request.formData();
        const mapId = formData.get("mapId") as string;
        const version = formData.get("version") as string;
        const resourcePack = formData.get("resourcePack") as File | null;
        const overrideFile = formData.get("overrideFile") as File | null;
        const resourcePackLink = formData.get("resourcePackLink") as string | null;
        const overrideFileLink = formData.get("overrideFileLink") as string | null;
        const resourcePackKey = formData.get("resourcePackKey") as string | null;
        const overrideFileKey = formData.get("overrideFileKey") as string | null;
        const originalLink = formData.get("originalLink") as string | null;
        const minecraftVersion = formData.get("minecraftVersion") as string | null;

        if (!mapId || !version || (!resourcePack && !overrideFile && !resourcePackLink && !overrideFileLink && !resourcePackKey && !overrideFileKey)) {
            return NextResponse.json(
                { error: "Missing required fields" },
                { status: 400 }
            );
        }

        const fileId = uuidv4();

        let resourcePackUrl: string | null = null;
        let overrideFileUrl: string | null = null;

        if (resourcePackKey) {
            resourcePackUrl = resourcePackKey;
        } else if (resourcePackLink) {
            resourcePackUrl = resourcePackLink;
        } else if (resourcePack) {
            const ext = resourcePack.name.split(".").pop() || "zip";
            const key = `maps/${fileId}_resourcepack.${ext}`;
            const buffer = Buffer.from(await resourcePack.arrayBuffer());
            await uploadFile(key, buffer, "application/zip");
            resourcePackUrl = key;
        }

        if (overrideFileKey) {
            overrideFileUrl = overrideFileKey;
        } else if (overrideFileLink) {
            overrideFileUrl = overrideFileLink;
        } else if (overrideFile) {
            const ext = overrideFile.name.split(".").pop() || "zip";
            const key = `maps/${fileId}_override.${ext}`;
            const buffer = Buffer.from(await overrideFile.arrayBuffer());
            await uploadFile(key, buffer, "application/zip");
            overrideFileUrl = key;
        }

        const translation = await prisma.mapTranslation.create({
            data: {
                mapId: parseInt(mapId, 10),
                version,
                userId: session.user.id,
                resourcePackUrl,
                overrideFileUrl,
                originalLink: originalLink || null,
                minecraftVersion: minecraftVersion || null,
                status: "pending",
            },
        });

        return NextResponse.json({ success: true, translationId: translation.id });
    } catch (error) {
        console.error("Upload map translation error:", error);
        return NextResponse.json(
            { error: "Failed to upload translation" },
            { status: 500 }
        );
    }
}
