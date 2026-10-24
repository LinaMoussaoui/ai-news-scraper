import './globals.css';

export const metadata = {
  title: 'AI Trends & News Scraper | Analytics Dashboard',
  description: 'Real-time AI news monitoring, trend analysis, and research tools for AI students and researchers.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
