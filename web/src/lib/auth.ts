import { AuthOptions } from "next-auth";
import DiscordProvider from "next-auth/providers/discord";
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
