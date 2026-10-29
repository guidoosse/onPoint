import './globals.css';

export const metadata = {
  title: 'OnPoint Portal',
  description: 'Unified personal portal for training, consultancy, finance, and life planning.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
