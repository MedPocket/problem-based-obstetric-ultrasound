import fs from "node:fs";
import path from "node:path";

let hasErrors = false;

function logError(msg: string) {
  console.error(`❌ ${msg}`);
  hasErrors = true;
}

function logSuccess(msg: string) {
  console.log(`✅ ${msg}`);
}

console.log("🔍 Running fast content validation...\n");

function findFiles(dir: string, pattern: RegExp): string[] {
  const results: string[] = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...findFiles(fullPath, pattern));
    } else if (entry.isFile() && pattern.test(entry.name)) {
      results.push(fullPath);
    }
  }
  return results;
}

// 1. Validate Duplicate Image Names in assets/
const assetFiles = findFiles("assets", /\.(png|webp|jpg|jpeg|svg|gif)$/i);
const imageBasenames = new Map<string, string>(); // basename -> relative path

for (const assetPath of assetFiles) {
  const base = path.basename(assetPath);
  if (imageBasenames.has(base)) {
    logError(
      `Duplicate image name '${base}' found in '${assetPath}' and '${imageBasenames.get(base)}'`,
    );
  } else {
    imageBasenames.set(base, assetPath);
  }
}

// 2. Validate meta.ts referenced files
const metaFiles = findFiles("docs", /^meta\.ts$/);
for (const metaPath of metaFiles) {
  const dir = path.dirname(metaPath);
  const content = fs.readFileSync(metaPath, "utf-8");
  const pagesMatch = content.match(/pages:\s*\[([\s\S]*?)\]/);
  if (pagesMatch) {
    const rawPages = pagesMatch[1];
    const pageSlugs = Array.from(rawPages.matchAll(/["'](.*?)["']/g)).map((m) => m[1]);
    for (const slug of pageSlugs) {
      const targetFile = path.join(dir, `${slug}.mdx`);
      if (!fs.existsSync(targetFile)) {
        logError(`meta.ts in '${dir}' references missing file '${targetFile}'`);
      }
    }
  }
}

// 3. Build route map of valid site routes
const mdxFiles = findFiles("docs", /\.mdx$/).sort();
const validRoutes = new Set<string>();
validRoutes.add("/");
validRoutes.add("/index");

for (const file of mdxFiles) {
  if (file === "docs/index.mdx") continue;
  // e.g. docs/01-he-than-kinh-dau-so/01-gian-nao-that.mdx
  // Blume strips 01- prefixes: /he-than-kinh-dau-so/gian-nao-that
  const parts = file
    .replace(/^docs\//, "")
    .replace(/\.mdx$/, "")
    .split("/");
  const cleanParts = parts.map((p) => p.replace(/^\d+-/, ""));
  const route = "/" + cleanParts.join("/");
  validRoutes.add(route);
  validRoutes.add(route + "/");
}

// 4. Validate MDX Files
for (const file of mdxFiles) {
  const content = fs.readFileSync(file, "utf-8");
  const lines = content.split("\n");
  const isHome = file === "docs/index.mdx";
  const artNum = isHome ? 0 : parseInt(path.basename(file).split("-")[0], 10);

  // A. Frontmatter check
  if (!content.startsWith("---")) {
    logError(`Missing YAML frontmatter in '${file}'`);
  } else {
    const fmEnd = content.indexOf("---", 3);
    if (fmEnd === -1) {
      logError(`Unclosed YAML frontmatter in '${file}'`);
    } else {
      const fm = content.slice(3, fmEnd);
      if (!fm.includes("title:")) {
        logError(`Frontmatter in '${file}' missing 'title' field`);
      }
    }
  }

  // B. Heading hierarchy check
  let prevHeaderLevel = 1; // H1 is the title in frontmatter
  lines.forEach((line, lineIdx) => {
    const match = line.match(/^(#{1,6})\s+(.*)$/);
    if (match) {
      const level = match[1].length;
      const text = match[2].trim();
      if (!text) {
        logError(`Empty heading at '${file}:${lineIdx + 1}'`);
      }
      if (level === 1 && !isHome) {
        logError(
          `Unexpected H1 heading at '${file}:${lineIdx + 1}'. Page H1 should come from frontmatter.`,
        );
      }
      if (level > prevHeaderLevel + 1) {
        logError(
          `Heading level skip from H${prevHeaderLevel} to H${level} at '${file}:${lineIdx + 1}' ("${text}")`,
        );
      }
      prevHeaderLevel = level;
    }
  });

  // C. Unescaped brackets check in narrative text
  lines.forEach((line, lineIdx) => {
    // Skip code blocks, JSX tags, markdown links, imports, comments
    if (
      line.trim().startsWith("<") &&
      (line.includes("Card") ||
        line.includes("Step") ||
        line.includes("Steps") ||
        line.includes("CardGroup") ||
        line.includes("div"))
    ) {
      return;
    }
    // Check for unescaped standalone < or > followed by digits or spaces (e.g. <10 mm)
    if (/<(?:\s*\d)/.test(line) && !line.includes("&lt;")) {
      logError(`Unescaped '<' symbol found at '${file}:${lineIdx + 1}': "${line.trim()}"`);
    }
  });

  // D. Image references & Image naming convention check
  const imgMatches = Array.from(content.matchAll(/!\[(.*?)\]\((.*?)\)/g));
  imgMatches.forEach((match, idx) => {
    const alt = match[1];
    const src = match[2];

    // Check target image file exists
    const mdxDir = path.dirname(file);
    const resolvedPath = path.normalize(path.join(mdxDir, src));

    if (!fs.existsSync(resolvedPath)) {
      logError(`Image reference broken in '${file}': '${src}' -> '${resolvedPath}' not found`);
    }

    // Check naming convention: img-{article_number}-{image_order}.ext or cover.png
    const imgFilename = path.basename(resolvedPath);
    if (isHome) {
      if (imgFilename !== "cover.png") {
        logError(`Home page image '${imgFilename}' should be named 'cover.png'`);
      }
    } else {
      const expectedPrefix = `img-${artNum}-${idx + 1}.`;
      if (!imgFilename.startsWith(expectedPrefix)) {
        logError(
          `Image '${imgFilename}' in '${file}' (image #${idx + 1}) does not match expected naming convention 'img-${artNum}-${idx + 1}.{ext}'`,
        );
      }
    }
  });

  // E. Internal links check
  const hrefMatches = Array.from(content.matchAll(/href=["'](.*?)["']|\[.*?\]\((.*?)\)/g));
  for (const m of hrefMatches) {
    const link = m[1] || m[2];
    if (!link) continue;
    if (
      link.startsWith("http://") ||
      link.startsWith("https://") ||
      link.startsWith("#") ||
      link.startsWith("mailto:")
    ) {
      continue;
    }
    // Check relative or absolute site route
    if (link.startsWith("..")) {
      // Relative file path (like image or relative mdx)
      const mdxDir = path.dirname(file);
      const resolved = path.normalize(path.join(mdxDir, link));
      if (!fs.existsSync(resolved)) {
        logError(`Broken relative link in '${file}': '${link}' -> '${resolved}' not found`);
      }
    } else if (link.startsWith("/")) {
      if (!validRoutes.has(link) && !validRoutes.has(link + "/")) {
        logError(`Broken internal route link in '${file}': '${link}'`);
      }
    }
  }
}

if (hasErrors) {
  console.error("\n❌ Content validation failed with errors.\n");
  process.exit(1);
} else {
  logSuccess(`All content validation checks passed! (${mdxFiles.length} MDX files validated)`);
}
