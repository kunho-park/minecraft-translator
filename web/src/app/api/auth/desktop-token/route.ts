import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { randomUUID } from "crypto";

export async function POST() {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const token = randomUUID();

    await prisma.apiToken.create({
      data: {
        token,
        userId: session.user.id,
        name: "Desktop App",
      },
    });

    const dbUser = await prisma.user.findUnique({
      where: { id: session.user.id },
    });

    return NextResponse.json({
      token,
      user: {
        name: dbUser?.name ?? session.user.name ?? "Unknown",
        discordId: dbUser?.discordId ?? session.user.discordId,
      },
    });
  } catch (error) {
    console.error("Desktop token generation error:", error);
    return NextResponse.json(
      { error: "Failed to generate token" },
      { status: 500 }
    );
  }
}
