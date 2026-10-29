import type { NextAuthOptions } from 'next-auth';
import KeycloakProvider from 'next-auth/providers/keycloak';

const issuer = process.env.KEYCLOAK_FRONTEND_ISSUER || 'http://localhost:8080/realms/onpoint';

export const authOptions: NextAuthOptions = {
  providers: [
    KeycloakProvider({
      clientId: process.env.KEYCLOAK_FRONTEND_CLIENT_ID || 'onpoint-frontend',
      clientSecret: process.env.KEYCLOAK_FRONTEND_CLIENT_SECRET || 'change_me',
      issuer,
    }),
  ],
  session: {
    strategy: 'jwt',
  },
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account?.access_token) {
        token.accessToken = account.access_token;
      }
      const username =
        profile && typeof profile === 'object'
          ? (profile as Record<string, unknown>).preferred_username
          : undefined;
      if (typeof username === 'string' && username.length > 0) {
        token.preferredUsername = username;
      }
      return token;
    },
    async session({ session, token }) {
      if (token.accessToken) {
        session.accessToken = token.accessToken as string;
      }
      if (session.user && token.preferredUsername) {
        session.user.name = token.preferredUsername as string;
      }
      return session;
    },
  },
};