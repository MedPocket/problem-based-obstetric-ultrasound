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
      site: false,
      logo: false,
    },
  },

  theme: {
    accent: "green",
    radius: "md",
    mode: "light",
    fonts: {
      body: "inter",
      display: "inter",
    },
  },

  deployment: {
    output: "static",
    base: process.env.NETLIFY === "true" ? "/" : "/problem-based-obstetric-ultrasound",
  },
});
