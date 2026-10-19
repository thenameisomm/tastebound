import type { Metadata } from "next";
import { Inter, Source_Serif_4 } from "next/font/google";
import { Nav } from "@/components/Nav";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const lyon = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-lyon",
  display: "swap",
});

export const metadata: Metadata = {
  title: "TasteBound — find the markets that already share your taste",
  description:
    "TasteBound scores origin markets by taste fit for a destination, compares them with real arrivals and finds the untapped ones. Taste fit, not a visitor forecast.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${lyon.variable}`}>
        <Nav />
        {children}
      </body>
    </html>
  );
}
