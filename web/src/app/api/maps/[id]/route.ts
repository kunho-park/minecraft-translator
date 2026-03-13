import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { uploadFile, getPublicUrl } from "@/lib/storage";
import { v4 as uuidv4 } from "uuid";

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
            const ext = thumbnail.name.split(".").pop() || "png";
            const key = `thumbnails/${uuidv4()}.${ext}`;
            const buffer = Buffer.from(await thumbnail.arrayBuffer());
            await uploadFile(key, buffer, thumbnail.type || "image/png");
            thumbnailUrl = getPublicUrl(key);
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
