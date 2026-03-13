/**
 * Discord webhook utilities for notifications
 */

const DISCORD_WEBHOOK_URL =
    process.env.DISCORD_WEBHOOK_URL ||
    "https://discord.com/api/webhooks/1461007756172595438/R2aXXazk1vms-pduk0Z83jwoYiq9_69Ch5HRLyaPvLDGcMQ47LxRaZpdTw5H8wbQfq9m";

const DISCORD_ADMIN_WEBHOOK_URL = process.env.DISCORD_ADMIN_WEBHOOK_URL;

interface DiscordEmbed {
    title?: string;
    description?: string;
    color?: number;
    fields?: Array<{
        name: string;
        value: string;
        inline?: boolean;
    }>;
    timestamp?: string;
    footer?: {
        text: string;
        icon_url?: string;
    };
    url?: string;
    thumbnail?: {
        url: string;
    };
}

interface DiscordMessage {
    content?: string;
    embeds?: DiscordEmbed[];
}

export interface TranslationNotificationData {
    id: string;
    modpackId: number;
    modpackName: string;
    modpackVersion: string;
    uploaderName?: string | null;
    sourceLang: string;
    targetLang: string;
    isManualTranslation: boolean;
    llmModel?: string | null;
    createdAt: Date;
    fileCount?: number | null;
    totalEntries?: number | null;
    translatedEntries?: number | null;
}

/**
 * Send a message to Discord webhook
 */
export async function sendDiscordNotification(
    message: DiscordMessage,
    webhookUrl: string = DISCORD_WEBHOOK_URL
): Promise<void> {
    if (!webhookUrl) {
        console.warn("Discord webhook URL not configured");
        return;
    }

    try {
        const response = await fetch(webhookUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(message),
        });

        if (!response.ok) {
            throw new Error(`Discord webhook failed: ${response.statusText}`);
        }
    } catch (error) {
        console.error("Failed to send Discord notification:", error);
        // Don't throw - notification failure shouldn't break the main operation
    }
}

function getTranslationType(data: TranslationNotificationData): string {
    if (data.isManualTranslation) {
        return "수동 번역 (Manual)";
    }
    return `AI 번역 (${data.llmModel || "Unknown Model"})`;
}

function formatStats(data: TranslationNotificationData): string {
    const parts = [];
    if (data.fileCount) parts.push(`${data.fileCount}개 파일`);
    if (data.totalEntries) parts.push(`${data.totalEntries}개 항목`);
    return parts.length > 0 ? parts.join(" / ") : "정보 없음";
}

/**
 * Send approval notification (Public Channel)
 */
export async function notifyApproval(data: TranslationNotificationData): Promise<void> {
    const siteUrl = process.env.NEXTAUTH_URL || "http://localhost:3000";
    const packUrl = `${siteUrl}/modpacks/${data.modpackId}`;

    await sendDiscordNotification({
        embeds: [
            {
                title: "✅ 번역팩 승인 완료",
                description: `**${data.modpackName}** 번역팩이 검수를 통과하여 승인되었습니다!`,
                color: 0x00b578, // Green
                fields: [
                    {
                        name: "모드팩",
                        value: `${data.modpackName} (v${data.modpackVersion})`,
                        inline: true,
                    },
                    {
                        name: "언어",
                        value: `${data.sourceLang} ➔ ${data.targetLang}`,
                        inline: true,
                    },
                    {
                        name: "번역 방식",
                        value: getTranslationType(data),
                        inline: true,
                    },
                    {
                        name: "제작자",
                        value: data.uploaderName || "익명",
                        inline: true,
                    },
                    {
                        name: "통계",
                        value: formatStats(data),
                        inline: true,
                    },
                    {
                        name: "업로드 일시",
                        value: new Date(data.createdAt).toLocaleString("ko-KR", {
                            timeZone: "Asia/Seoul",
                        }),
                        inline: false,
                    },
                ],
                url: packUrl,
                timestamp: new Date().toISOString(),
                footer: {
                    text: "Minecraft Auto Translate",
                },
            },
        ],
    }, DISCORD_WEBHOOK_URL);
}

/**
 * Send submission notification (Admin Channel)
 */
export async function notifySubmission(data: TranslationNotificationData): Promise<void> {
    if (!DISCORD_ADMIN_WEBHOOK_URL) {
        console.warn("Admin Discord webhook URL not configured");
        return;
    }

    const siteUrl = process.env.NEXTAUTH_URL || "http://localhost:3000";

    // Let's link to the Admin Dashboard for now.
    const adminUrl = `${siteUrl}/admin`;

    await sendDiscordNotification({
        embeds: [
            {
                title: "🔍 번역 검수 요청",
                description: `새로운 번역팩이 업로드되어 검수가 필요합니다.\n**${data.modpackName}**`,
                color: 0xFFA500, // Orange
                fields: [
                    {
                        name: "모드팩",
                        value: `${data.modpackName} (v${data.modpackVersion})`,
                        inline: true,
                    },
                    {
                        name: "언어",
                        value: `${data.sourceLang} ➔ ${data.targetLang}`,
                        inline: true,
                    },
                    {
                        name: "번역 방식",
                        value: getTranslationType(data),
                        inline: true,
                    },
                    {
                        name: "제작자",
                        value: data.uploaderName || "익명",
                        inline: true,
                    },
                    {
                        name: "통계",
                        value: formatStats(data),
                        inline: true,
                    },
                ],
                url: adminUrl,
                timestamp: new Date().toISOString(),
                footer: {
                    text: "Review Required",
                },
            },
        ],
    }, DISCORD_ADMIN_WEBHOOK_URL);
}
