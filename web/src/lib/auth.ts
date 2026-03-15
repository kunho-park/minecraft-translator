import { AuthOptions } from "next-auth";
import { NextRequest } from "next/server";
import DiscordProvider from "next-auth/providers/discord";
import { getServerSession } from "next-auth";
import { prisma } from "./prisma";

// Admin Discord IDs from environment variable
const ADMIN_DISCORD_IDS = (process.env.ADMIN_DISCORD_IDS || "").split(",").filter(Boolean);

export const authOptions: AuthOptions = {
  providers: [
    DiscordProvider({
      clientId: process.env.DISCORD_CLIENT_ID || "",
      clientSecret: process.env.DISCORD_CLIENT_SECRET || "",
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "discord" && account.providerAccountId) {
        // Check if user exists, if not create
        const existingUser = await prisma.user.findUnique({
          where: { discordId: account.providerAccountId },
        });

        if (!existingUser) {
          await prisma.user.create({
            data: {
              discordId: account.providerAccountId,
              name: user.name || "Unknown",
              avatar: user.image,
              isAdmin: ADMIN_DISCORD_IDS.includes(account.providerAccountId),
            },
          });
        } else {
          // Update user info
          await prisma.user.update({
            where: { discordId: account.providerAccountId },
            data: {
              name: user.name || existingUser.name,
              avatar: user.image || existingUser.avatar,
              isAdmin: ADMIN_DISCORD_IDS.includes(account.providerAccountId),
            },
          });
        }
      }
      return true;
    },
    async session({ session, token }) {
      if (token.sub) {
        const dbUser = await prisma.user.findUnique({
          where: { discordId: token.sub },
        });
        if (dbUser) {
          session.user.id = dbUser.id;
          session.user.discordId = dbUser.discordId;
          session.user.isAdmin = dbUser.isAdmin;
        }
      }
      return session;
    },
    async jwt({ token, account }) {
      if (account) {
        token.sub = account.providerAccountId;
      }
      return token;
    },
  },
  pages: {
    signIn: "/auth/signin",
  },
  session: {
    strategy: "jwt",
  },
};

export interface AuthUser {
  id: string;
  discordId: string;
  name: string;
  isAdmin: boolean;
}

/**
 * Resolve the authenticated user from either a NextAuth session cookie
 * or an `Authorization: Bearer <token>` header (API token from desktop app).
 */
export async function getAuthFromRequest(
  request: NextRequest
): Promise<AuthUser | null> {
  const session = await getServerSession(authOptions);
  if (session?.user?.id) {
    return {
      id: session.user.id,
      discordId: session.user.discordId,
      name: session.user.name ?? "Unknown",
      isAdmin: session.user.isAdmin ?? false,
    };
  }

  const authHeader = request.headers.get("authorization");
  if (authHeader?.startsWith("Bearer ")) {
    const token = authHeader.slice(7);
    const apiToken = await prisma.apiToken.findUnique({
      where: { token },
      include: { user: true },
    });
    if (apiToken) {
      prisma.apiToken
        .update({
          where: { id: apiToken.id },
          data: { lastUsedAt: new Date() },
        })
        .catch(() => {});
      return {
        id: apiToken.user.id,
        discordId: apiToken.user.discordId,
        name: apiToken.user.name,
        isAdmin: apiToken.user.isAdmin,
      };
    }
  }

  return null;
}
