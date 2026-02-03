import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { prisma } from "@/lib/prisma";
import { notFound } from "next/navigation";
import Image from "next/image";
import type { Metadata, ResolvingMetadata } from "next";
import {
    Download,
    ExternalLink,
    Search,
    User,
    Calendar,
} from "lucide-react";
import Button from "@/components/ui/Button";
import MapTranslationList from "@/components/MapTranslationList";
import MapAdminActions from "@/components/MapAdminActions";

export const dynamic = "force-dynamic";

interface MapDetailPageProps {
    params: Promise<{ locale: string; id: string }>;
}

export async function generateMetadata(
    { params }: MapDetailPageProps,
    parent: ResolvingMetadata
): Promise<Metadata> {
    const { id } = await params;
    const mapId = parseInt(id, 10);

    if (isNaN(mapId)) {
        return {
            title: "맵을 찾을 수 없습니다",
        };
    }

    const map = await prisma.map.findUnique({
        where: { id: mapId },
    });

    if (!map) {
        return {
            title: "맵을 찾을 수 없습니다",
        };
    }

    const previousImages = (await parent).openGraph?.images || [];

    return {
        title: `${map.name} 한글패치 & 번역 다운로드`,
        description: `${map.name} 맵의 한글 번역을 다운로드하세요. ${map.summary}`,
        keywords: [map.name, "한글패치", "번역", "Map", "Minecraft", "마인크래프트"],
        openGraph: {
            title: `${map.name} 한글패치 다운로드`,
            description: map.summary || undefined,
            images: map.thumbnailUrl ? [map.thumbnailUrl, ...previousImages] : previousImages,
        },
    };
}

export default async function MapDetailPage({
    params,
}: MapDetailPageProps) {
    const { locale, id } = await params;
    setRequestLocale(locale);
    const t = await getTranslations();

    const mapId = parseInt(id, 10);
    let map = null;

    if (!isNaN(mapId)) {
        map = await prisma.map.findUnique({
            where: { id: mapId },
            include: {
                translations: {
                    where: { status: "approved" },
                    include: {
                        user: {
                            select: { name: true, avatar: true },
                        },
                    },
                    orderBy: { createdAt: "desc" },
                },
            },
        });
    }

    if (!map) {
        return (
            <div className="max-w-4xl mx-auto px-4 py-16 text-center animate-fade-in">
                <div className="glass rounded-xl p-8 md:p-16 border border-[var(--border-primary)]">
                    <div className="w-24 h-24 bg-[var(--bg-tertiary)] rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
                        <Search className="w-10 h-10 text-[var(--accent-primary)]" />
                    </div>
                    <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-4">
                        맵을 찾을 수 없습니다
                    </h1>
                    <Link href="/maps">
                        <Button size="lg" className="shadow-lg hover:shadow-xl transition-shadow">
                            맵 검색하러 가기
                        </Button>
                    </Link>
                </div>
            </div>
        );
    }

    // Calculate total downloads
    const totalDownloads = map.translations.reduce((sum, t) => sum + t.downloadCount, 0);

    // JSON-LD for SEO
    const jsonLd = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": map.name,
        "applicationCategory": "Game",
        "operatingSystem": "Windows, macOS, Linux",
        "description": map.summary,
        "image": map.thumbnailUrl,
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "KRW",
        },
        "author": {
            "@type": "Person",
            "name": map.author
        }
    };

    return (
        <div className="max-w-7xl mx-auto px-4 py-8 animate-fade-in">
            <script
                type="application/ld+json"
                dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
            />
            {/* Map Header */}
            <div className="glass rounded-xl p-6 mb-8">
                <div className="flex flex-col md:flex-row gap-6">
                    {/* Logo */}
                    {map.thumbnailUrl ? (
                        <Image
                            src={map.thumbnailUrl}
                            alt={map.name}
                            width={128}
                            height={128}
                            className="w-32 h-32 rounded-xl object-cover flex-shrink-0"
                        />
                    ) : (
                        <div className="w-32 h-32 rounded-xl bg-[var(--bg-tertiary)] flex items-center justify-center flex-shrink-0">
                            <span className="text-4xl font-bold text-[var(--text-muted)]">
                                {map.name.charAt(0)}
                            </span>
                        </div>
                    )}

                    {/* Info */}
                    <div className="flex-1">
                        <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-2">
                            {map.name}
                        </h1>
                        {map.author && (
                            <p className="flex items-center gap-2 text-[var(--text-secondary)] mb-4">
                                <User className="w-4 h-4" />
                                {map.author}
                            </p>
                        )}
                        <p className="text-[var(--text-secondary)] mb-4">{map.summary}</p>

                        {/* Stats */}
                        <div className="flex items-center gap-6 text-sm text-[var(--text-muted)]">
                            <span className="flex items-center gap-1.5">
                                <Download className="w-4 h-4" />
                                {totalDownloads.toLocaleString()} {t("maps.info.downloads")}
                            </span>
                            <span className="flex items-center gap-1.5">
                                <Calendar className="w-4 h-4" />
                                {new Date(map.createdAt).toLocaleDateString()}
                            </span>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-3 relative">
                        <MapAdminActions map={map} />
                        <Link href="/upload">
                            <Button className="w-full">{t("maps.uploadTranslation")}</Button>
                        </Link>
                        {map.originalLink && (
                            <a
                                href={map.originalLink}
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                <Button variant="secondary" className="w-full">
                                    <ExternalLink className="w-4 h-4" />
                                    원본 링크
                                </Button>
                            </a>
                        )}
                    </div>
                </div>
            </div>

            <MapTranslationList
                initialTranslations={map.translations.map((t) => ({
                    ...t,
                    createdAt: t.createdAt.toISOString(),
                }))}
                mapId={map.id}
            />
        </div>
    );
}
