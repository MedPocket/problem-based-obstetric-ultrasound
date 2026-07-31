import { defineConfig } from "blume";

export default defineConfig({
  title: "Ultraso",
  description: "Tài liệu về siêu âm lâm sàng.",

  feedback: false,

  github: {
    owner: "MedPocket",
    repo: "ultraso",
    branch: "main",
  },

  i18n: {
    defaultLocale: "vi",
    locales: [{ code: "vi", label: "Tiếng Việt" }],
    hideDefaultLocalePrefix: true,
  },

  seo: {
    og: {
      fonts: ["Be Vietnam Pro"],
    },
  },

  theme: {
    accent: "blue",
    radius: "md",
    mode: "system",
  },

  deployment: {
    output: "static",
    site:
      process.env.NETLIFY === "true"
        ? process.env.URL || "https://ultraso.netlify.app"
        : "https://medpocket.github.io",
    base: process.env.NETLIFY === "true" ? "/" : "/ultraso",
  },
});
