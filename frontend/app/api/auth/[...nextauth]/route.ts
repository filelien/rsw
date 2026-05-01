import NextAuth from 'next-auth'
import CredentialsProvider from 'next-auth/providers/credentials'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://gateway:8000'

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: 'credentials',
      credentials: { username: {}, password: {} },
      async authorize(credentials) {
        try {
          const res = await axios.post(`${API_URL}/api/v1/auth/login`, {
            username: credentials?.username,
            password: credentials?.password,
          })
          const { access_token, refresh_token, user } = res.data
          return { ...user, accessToken: access_token, refreshToken: refresh_token }
        } catch {
          return null
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) { token.accessToken = (user as any).accessToken; token.role = (user as any).role }
      return token
    },
    async session({ session, token }) {
      (session as any).accessToken = token.accessToken;
      (session.user as any).role = token.role
      return session
    },
  },
  pages: { signIn: '/auth/signin' },
  session: { strategy: 'jwt', maxAge: 60 * 60 },
})

export { handler as GET, handler as POST }
