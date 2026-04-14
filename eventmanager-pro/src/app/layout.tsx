import './globals.css';
import type { Metadata, Viewport } from 'next';

export const metadata: Metadata = {
  title: 'EventManager Pro',
  description: 'Event- und Catering-Management für Lucky Event, Mettgenpin 1877 und Schänke 1998',
  manifest: '/manifest.webmanifest',
  applicationName: 'EventManager Pro',
  appleWebApp: {
    capable: true,
    title: 'EventManager Pro',
    statusBarStyle: 'black-translucent',
  },
};

export const viewport: Viewport = {
  themeColor: '#141925',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de" className="dark">
      <body className="min-h-screen bg-base-950">{children}</body>
    </html>
  );
}
