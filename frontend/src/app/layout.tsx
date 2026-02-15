import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Header } from '@/components/layout/Header';

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'BossHelp - 게임 공략 AI 도우미',
  description: '하드코어 게임에서 막혔을 때, 3초 안에 정확한 답변을 알려주는 AI',
  keywords: ['게임 공략', 'Elden Ring', 'Sekiro', 'Hollow Knight', '소울라이크', 'AI 도우미'],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className={`${inter.variable} font-sans antialiased bg-bg text-white`}>
        <Header />
        {children}
      </body>
    </html>
  );
}
