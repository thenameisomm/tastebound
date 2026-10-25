import type { Metadata } from "next";
import { Anton, Inter, JetBrains_Mono } from "next/font/google";
import { AssistantProvider } from "@/components/assistant/AssistantProvider";
import { Footer } from "@/components/Footer";
import { Nav } from "@/components/Nav";
import "./globals.css";

const anton = Anton({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-display-family",
  display: "swap",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-ui-family",
  display: "swap",
});

const jetBrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono-family",
  display: "swap",
});

export const metadata: Metadata = {
  title: "TasteBound — the markets that already share your taste",
  description:
    "TasteBound scores origin markets by taste fit for a destination, compares them with real arrivals and finds the untapped ones. Taste fit, not a visitor forecast.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${anton.variable} ${inter.variable} ${jetBrainsMono.variable}`}
    >
      <body>
        <AssistantProvider>
          <Nav />
          {children}
          <Footer />
        </AssistantProvider>
      </body>
    </html>
  );
}
