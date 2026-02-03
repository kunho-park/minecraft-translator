import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import fs from "fs/promises";
import path from "path";
import { v4 as uuidv4 } from "uuid";

const UPLOADS_DIR = path.join(process.cwd(), "uploads", "maps");

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
        if (!session?.user) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const formData = await request.formData();
        const mapId = formData.get("mapId") as string;
        const version = formData.get("version") as string;
        const resourcePack = formData.get("resourcePack") as File | null;
        const overrideFile = formData.get("overrideFile") as File | null;

        if (!mapId || !version || (!resourcePack && !overrideFile)) {
            return NextResponse.json(
                { error: "Missing required fields" },
                { status: 400 }
            );
        }

        await ensureUploadsDir();
        const fileId = uuidv4();

        let resourcePackUrl: string | null = null;
        let overrideFileUrl: string | null = null;

        if (resourcePack) {
            const ext = resourcePack.name.split(".").pop() || "zip";
            const fileName = `${fileId}_resourcepack.${ext}`;
            const filePath = path.join(UPLOADS_DIR, fileName);
            const buffer = Buffer.from(await resourcePack.arrayBuffer());
            await fs.writeFile(filePath, buffer);
            resourcePackUrl = `maps/${fileName}`;
        }

        if (overrideFile) {
            const ext = overrideFile.name.split(".").pop() || "zip";
            const fileName = `${fileId}_override.${ext}`;
            const filePath = path.join(UPLOADS_DIR, fileName);
            const buffer = Buffer.from(await overrideFile.arrayBuffer());
            await fs.writeFile(filePath, buffer);
            overrideFileUrl = `maps/${fileName}`;
        }

        const translation = await prisma.mapTranslation.create({
            data: {
                mapId: parseInt(mapId, 10),
                version,
                userId: session.user.id,
                resourcePackUrl,
                overrideFileUrl,
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
