import { MetadataRoute } from 'next';
import { PrismaClient } from '@prisma/client';
import { locales, defaultLocale } from '@/i18n/config';

// Force dynamic rendering to ensure we get the latest data from the DB
export const dynamic = 'force-dynamic';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
    const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'https://mcat.2odk.com';

    const prisma = new PrismaClient();

    let modpacks: { id: number; cachedAt: Date }[] = [];
    let maps: { id: number; updatedAt: Date }[] = [];

    try {
        [modpacks, maps] = await Promise.all([
            prisma.modpack.findMany({
                select: {
                    id: true,
                    cachedAt: true,
                },
                orderBy: {
                    cachedAt: 'desc',
                },
            }),
            prisma.map.findMany({
                select: {
                    id: true,
                    updatedAt: true,
                },
                orderBy: {
                    updatedAt: 'desc',
                },
            }),
        ]);
    } catch (error) {
        console.error('Failed to fetch data for sitemap:', error);
    } finally {
        await prisma.$disconnect();
    }

    const sitemapEntries: MetadataRoute.Sitemap = [];

    // Static routes to include
    const staticRoutes = [
        { path: '', priority: 1.0, changeFrequency: 'daily' as const },
        { path: '/modpacks', priority: 0.9, changeFrequency: 'daily' as const },
        { path: '/maps', priority: 0.9, changeFrequency: 'daily' as const },
        { path: '/upload', priority: 0.7, changeFrequency: 'weekly' as const },
        { path: '/my-uploads', priority: 0.5, changeFrequency: 'weekly' as const },
    ];

    // 1. Generate entries for static routes
    for (const route of staticRoutes) {
        for (const locale of locales) {
            const isDefault = locale === defaultLocale;
            const prefix = isDefault ? '' : `/${locale}`;
            const url = `${baseUrl}${prefix}${route.path}`;

            sitemapEntries.push({
                url,
                lastModified: new Date(),
                changeFrequency: route.changeFrequency,
                priority: route.priority,
            });
        }
    }

    // 2. Generate entries for dynamic modpack routes
    for (const modpack of modpacks) {
        for (const locale of locales) {
            const isDefault = locale === defaultLocale;
            const prefix = isDefault ? '' : `/${locale}`;
            const url = `${baseUrl}${prefix}/modpacks/${modpack.id}`;

            sitemapEntries.push({
                url,
                lastModified: modpack.cachedAt,
                changeFrequency: 'weekly',
                priority: 0.7,
            });
        }
    }

    // 3. Generate entries for dynamic map routes
    for (const map of maps) {
        for (const locale of locales) {
            const isDefault = locale === defaultLocale;
            const prefix = isDefault ? '' : `/${locale}`;
            const url = `${baseUrl}${prefix}/maps/${map.id}`;

            sitemapEntries.push({
                url,
                lastModified: map.updatedAt,
                changeFrequency: 'weekly',
                priority: 0.7,
            });
        }
    }

    return sitemapEntries;
}
