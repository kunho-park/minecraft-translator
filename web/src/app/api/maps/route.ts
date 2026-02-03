import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
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

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get("q");

    try {
        const maps = await prisma.map.findMany({
            where: query
                ? {
                    name: { contains: query },
                }
                : undefined,
            orderBy: { createdAt: "desc" },
            take: 20,
        });

        return NextResponse.json(maps);
    } catch (error) {
        console.error("Search maps error:", error);
        return NextResponse.json(
            { error: "Failed to search maps" },
            { status: 500 }
        );
    }
}

export async function POST(request: NextRequest) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const formData = await request.formData();
        const name = formData.get("name") as string;
        const summary = formData.get("summary") as string;
        const author = formData.get("author") as string;
        const originalLink = formData.get("originalLink") as string;
        const thumbnail = formData.get("thumbnail") as File | null;

        if (!name || !summary) {
            return NextResponse.json(
                { error: "Name and summary are required" },
                { status: 400 }
            );
        }

        let thumbnailUrl: string | null = null;

        if (thumbnail) {
            await ensureThumbnailsDir();
            const ext = thumbnail.name.split(".").pop() || "png";
            const fileName = `${uuidv4()}.${ext}`;
            const filePath = path.join(THUMBNAILS_DIR, fileName);
            const buffer = Buffer.from(await thumbnail.arrayBuffer());
            await fs.writeFile(filePath, buffer);
            thumbnailUrl = `/uploads/thumbnails/${fileName}`;
        }

        // Generate slug
        let slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
        if (!slug) slug = "untitled-map";

        // Ensure uniqueness
        let uniqueSlug = slug;
        let counter = 1;
        while (await prisma.map.findUnique({ where: { slug: uniqueSlug } })) {
            uniqueSlug = `${slug}-${counter}`;
            counter++;
        }

        const map = await prisma.map.create({
            data: {
                name,
                slug: uniqueSlug,
                summary,
                author,
                originalLink,
                thumbnailUrl,
            },
        });

        return NextResponse.json(map);
    } catch (error) {
        console.error("Create map error:", error);
        return NextResponse.json(
            { error: "Failed to create map" },
            { status: 500 }
        );
    }
}
