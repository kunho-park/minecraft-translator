import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { getPresignedUploadUrl } from "@/lib/storage";
import { v4 as uuidv4 } from "uuid";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { files, anonymous } = body as {
      files: { type: string; contentType?: string }[];
      anonymous?: boolean;
    };

    const session = await getServerSession(authOptions);
    if (!session?.user && !anonymous) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    if (!files || !Array.isArray(files) || files.length === 0) {
      return NextResponse.json(
        { error: "files array is required" },
        { status: 400 }
      );
    }

    const id = uuidv4();
    const results = await Promise.all(
      files.map(async (file) => {
        let key: string;
        const ct = file.contentType || "application/zip";

        switch (file.type) {
          case "resourcepack":
            key = `translations/${id}/${id}_resourcepack.zip`;
            break;
          case "override":
            key = `translations/${id}/${id}_override.zip`;
            break;
          case "map-resourcepack":
            key = `maps/${id}_resourcepack.zip`;
            break;
          case "map-override":
            key = `maps/${id}_override.zip`;
            break;
          case "thumbnail": {
            const ext = ct.split("/").pop() || "png";
            key = `thumbnails/${id}.${ext}`;
            break;
          }
          default:
            throw new Error(`Unknown file type: ${file.type}`);
        }

        const url = await getPresignedUploadUrl(key, ct);
        return { type: file.type, key, uploadUrl: url };
      })
    );

    return NextResponse.json({ id, files: results });
  } catch (error) {
    console.error("Presigned URL error:", error);
    return NextResponse.json(
      { error: "Failed to generate upload URL" },
      { status: 500 }
    );
  }
}
