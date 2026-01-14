import "next-auth";

declare module "next-auth" {
    interface Session {
        user: {
            id: string;
            discordId: string;
            name?: string | null;
            email?: string | null;
            image?: string | null;
            isAdmin: boolean;
        };
    }
}
