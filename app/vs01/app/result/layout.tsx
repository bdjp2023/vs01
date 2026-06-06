// File: app/result/layout.tsx
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: '実行結果 - harakiriizm',
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
