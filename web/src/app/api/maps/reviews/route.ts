import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { headers } from "next/headers";

// IP 주소 가져오기
function getClientIP(request: NextRequest): string {
  // Cloudflare
  const cfConnectingIP = request.headers.get("cf-connecting-ip");
  if (cfConnectingIP) return cfConnectingIP;

  // X-Forwarded-For (프록시/로드밸런서)
  const forwardedFor = request.headers.get("x-forwarded-for");
  if (forwardedFor) {
    return forwardedFor.split(",")[0].trim();
  }

  // X-Real-IP (nginx)
  const realIP = request.headers.get("x-real-ip");
  if (realIP) return realIP;

  // 기본값
  return "unknown";
}

// IP별 리뷰 제한 확인 (동일 번역에 24시간 내 1개)
async function checkIPRateLimit(mapTranslationId: string, ipAddress: string): Promise<boolean> {
  const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);

  const existingReview = await prisma.mapReview.findFirst({
    where: {
      mapTranslationId,
      ipAddress,
      isAnonymous: true,
      createdAt: {
        gte: oneDayAgo,
      },
    },
  });

  return !existingReview; // true면 리뷰 가능
}

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    const body = await request.json();
    const { mapTranslationId, works, rating, comment } = body;

    // Validate required fields
    if (!mapTranslationId || typeof works !== "boolean" || !rating) {
      return NextResponse.json(
        { error: "Missing required fields (mapTranslationId, works, rating)" },
        { status: 400 }
      );
    }

    if (rating < 1 || rating > 5) {
      return NextResponse.json(
        { error: "Rating must be between 1 and 5" },
        { status: 400 }
      );
    }

    // Check if map translation exists and is approved
    const mapTranslation = await prisma.mapTranslation.findUnique({
      where: { id: mapTranslationId },
    });

    if (!mapTranslation) {
      return NextResponse.json(
        { error: "Map translation not found" },
        { status: 404 }
      );
    }

    if (mapTranslation.status !== "approved") {
      return NextResponse.json(
        { error: "Cannot review unapproved translations" },
        { status: 400 }
      );
    }

    // 로그인 사용자
    if (session?.user?.id) {
      // Check if user already reviewed this translation
      const existingReview = await prisma.mapReview.findFirst({
        where: {
          mapTranslationId,
          userId: session.user.id,
        },
      });

      if (existingReview) {
        // Update existing review
        const review = await prisma.mapReview.update({
          where: { id: existingReview.id },
          data: {
            works,
            rating,
            comment: comment || null,
          },
        });
        return NextResponse.json(review);
      }

      // Create new review (logged in user)
      const review = await prisma.mapReview.create({
        data: {
          mapTranslationId,
          userId: session.user.id,
          works,
          rating,
          comment: comment || null,
          isAnonymous: false,
        },
      });

      return NextResponse.json(review);
    }

    // 익명 사용자 (IP 기반 제한)
    const ipAddress = getClientIP(request);

    // IP 제한 확인
    const canReview = await checkIPRateLimit(mapTranslationId, ipAddress);
    if (!canReview) {
      return NextResponse.json(
        { error: "You have already reviewed this translation. Anonymous users can review once per 24 hours." },
        { status: 429 }
      );
    }

    // Create anonymous review
    const review = await prisma.mapReview.create({
      data: {
        mapTranslationId,
        works,
        rating,
        comment: comment || null,
        ipAddress,
        isAnonymous: true,
      },
    });

    return NextResponse.json(review);
  } catch (error) {
    console.error("Map review error:", error);
    return NextResponse.json(
      { error: "Failed to submit review" },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const mapTranslationId = searchParams.get("mapTranslationId");

  if (!mapTranslationId) {
    return NextResponse.json(
      { error: "mapTranslationId is required" },
      { status: 400 }
    );
  }

  try {
    const reviews = await prisma.mapReview.findMany({
      where: { mapTranslationId },
      include: {
        user: {
          select: { name: true, avatar: true },
        },
      },
      orderBy: { createdAt: "desc" },
    });

    // IP 주소는 클라이언트에 노출하지 않음
    const sanitizedReviews = reviews.map((review: any) => ({
      ...review,
      ipAddress: undefined,
    }));

    return NextResponse.json(sanitizedReviews);
  } catch (error) {
    console.error("Fetch map reviews error:", error);
    return NextResponse.json(
      { error: "Failed to fetch reviews" },
      { status: 500 }
    );
  }
}
