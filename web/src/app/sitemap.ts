import { MetadataRoute } from 'next';
import { PrismaClient } from '@prisma/client';
import { locales, defaultLocale } from '@/i18n/config';

// Force dynamic rendering to ensure we get the latest modpacks from the DB
export const dynamic = 'force-dynamic';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
    const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'https://mcat.2odk.com';

    // Create a local instance of PrismaClient since we couldn't locate the shared instance.
    // In a high-traffic scenario, this should be replaced with a singleton instance.
    const prisma = new PrismaClient();

    let modpacks: { id: number; cachedAt: Date }[] = [];

    try {
        modpacks = await prisma.modpack.findMany({
            select: {
                id: true,
                cachedAt: true,
            },
            orderBy: {
                cachedAt: 'desc',
            },
        });
    } catch (error) {
        console.error('Failed to fetch modpacks for sitemap:', error);
    } finally {
        await prisma.$disconnect();
    }

    const sitemapEntries: MetadataRoute.Sitemap = [];

    // Static routes to include
    const staticRoutes = [
        '',            // Home page
        '/modpacks',   // Modpack list
        '/upload',     // Upload page
        '/my-uploads', // My Uploads page
    ];

    // 1. Generate entries for static routes
    for (const route of staticRoutes) {
        for (const locale of locales) {
            const isDefault = locale === defaultLocale;
            // With localePrefix: 'as-needed', default locale has no prefix
            const prefix = isDefault ? '' : `/${locale}`;
            // Ensure we don't have double slashes if route is empty
            const path = route === '' ? '' : route;
            const url = `${baseUrl}${prefix}${path}`;

            sitemapEntries.push({
                url,
                lastModified: new Date(),
                changeFrequency: 'daily',
                priority: route === '' ? 1.0 : 0.8,
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
                priority: 0.6,
            });
        }
    }

    return sitemapEntries;
}
