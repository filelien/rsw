'use client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SessionProvider } from 'next-auth/react'
import { useState } from 'react'
import Sidebar from '@/components/layout/Sidebar'
import { usePathname } from 'next/navigation'

const AUTH_PATHS = ['/auth/signin', '/auth/signup']

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: { queries: { staleTime: 30_000, retry: 1 } }
  }))
  const pathname = usePathname()
  const isAuth = AUTH_PATHS.includes(pathname || '')

  return (
    <SessionProvider>
      <QueryClientProvider client={queryClient}>
        {isAuth ? children : <Sidebar>{children}</Sidebar>}
      </QueryClientProvider>
    </SessionProvider>
  )
}
