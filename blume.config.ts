import { defineConfig } from "blume";

export default defineConfig({
  title: "Siêu âm Sản Phụ khoa dựa trên vấn đề",
  description:
    "Tài liệu y khoa về Siêu âm Sản Phụ khoa dựa trên vấn đề (Problem-based Obstetric Ultrasound)",

  feedback: false,

  github: {
    owner: "MedPocket",
    repo: "problem-based-obstetric-ultrasound",
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
    fonts: {
      body: { name: "Be Vietnam Pro" },
      display: { name: "Be Vietnam Pro" },
    },
  },

  deployment: {
    output: "static",
    site:
      process.env.NETLIFY === "true"
        ? process.env.URL || "https://ultraso.netlify.app"
        : "https://medpocket.github.io",
    base: process.env.NETLIFY === "true" ? "/" : "/problem-based-obstetric-ultrasound",
  },
});
