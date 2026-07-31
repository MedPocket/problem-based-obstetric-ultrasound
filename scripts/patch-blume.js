import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const pathsToPatch = [
  path.join(__dirname, "..", "node_modules", "blume", "dist", "cli", "index.js"),
  path.join(__dirname, "..", "node_modules", "blume", "src", "astro", "templates.ts"),
];

for (const filepath of pathsToPatch) {
  if (fs.existsSync(filepath)) {
    let content = fs.readFileSync(filepath, "utf8");
    if (content.includes("site: siteHost,")) {
      content = content.replace("site: siteHost,", "site: undefined,");
      fs.writeFileSync(filepath, content, "utf8");
      console.log(`Successfully patched ${filepath}`);
    } else {
      console.log(`Already patched or "site: siteHost," not found in ${filepath}`);
    }
  } else {
    console.warn(`File not found: ${filepath}`);
  }
}
