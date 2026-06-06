// File: app/secret/harakiriim-03/layout.tsx
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: '秘密のフォルダ | harakiriizm',
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}