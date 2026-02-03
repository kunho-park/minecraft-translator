import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import fs from "fs/promises";
import path from "path";
import { v4 as uuidv4 } from "uuid";

const THUMBNAILS_DIR = path.join(process.cwd(), "public", "uploads", "thumbnails");

async function ensureThumbnailsDir() {
    try {
        await fs.access(THUMBNAILS_DIR);
    } catch {
        await fs.mkdir(THUMBNAILS_DIR, { recursive: true });
    }
}

export async function PATCH(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user?.isAdmin) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 403 });
        }

        const { id } = await params;
        const mapId = parseInt(id, 10);

        const formData = await request.formData();
        const name = formData.get("name") as string;
        const summary = formData.get("summary") as string;
        const author = formData.get("author") as string;
        const originalLink = formData.get("originalLink") as string;
        const thumbnail = formData.get("thumbnail") as File | null;

        let thumbnailUrl: string | undefined;

        if (thumbnail) {
            await ensureThumbnailsDir();
            const ext = thumbnail.name.split(".").pop() || "png";
            const fileName = `${uuidv4()}.${ext}`;
            const filePath = path.join(THUMBNAILS_DIR, fileName);
            const buffer = Buffer.from(await thumbnail.arrayBuffer());
            await fs.writeFile(filePath, buffer);
            thumbnailUrl = `/uploads/thumbnails/${fileName}`;
        }

        const updatedMap = await prisma.map.update({
            where: { id: mapId },
            data: {
                ...(name && { name }),
                ...(summary && { summary }),
                ...(author !== undefined && { author }),
                ...(originalLink !== undefined && { originalLink }),
                ...(thumbnailUrl && { thumbnailUrl }),
            },
        });

        return NextResponse.json(updatedMap);
    } catch (error) {
        console.error("Update map error:", error);
        return NextResponse.json(
            { error: "Failed to update map" },
            { status: 500 }
        );
    }
}
