import type { MetadataRoute } from "next";

const base = "https://sealquery-web.onrender.com";

export default function sitemap(): MetadataRoute.Sitemap {
  return ["", "/security", "/status", "/pricing", "/docs"].map((path) => ({
    url: `${base}${path}`,
    lastModified: new Date("2026-11-11"),
    changeFrequency: path === "" ? "daily" : "weekly",
    priority: path === "" ? 1 : 0.7,
  }));
}
