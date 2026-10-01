import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import fs from "node:fs";
import path from "node:path";

const SITE_URL = process.env.SITE_URL || "https://edublog.setterbro.com";

// 글이 하나도 없는 카테고리 페이지는 사이트맵에서 제외 (빈 페이지 색인 방지)
function emptyCategories() {
  const dir = path.resolve("src/content/posts");
  const counts = { cert: 0, hrd: 0, exam: 0 };
  try {
    for (const f of fs.readdirSync(dir)) {
      if (!f.endsWith(".md")) continue;
      const m = fs.readFileSync(path.join(dir, f), "utf8").match(/^category:\s*["\x27]?(\w+)["\x27]?/m);
      if (m && m[1] in counts) counts[m[1]]++;
    }
  } catch (e) {}
  return Object.keys(counts).filter((k) => counts[k] === 0);
}
const EMPTY = emptyCategories();

export default defineConfig({
  site: SITE_URL,
  integrations: [
    sitemap({
      filter: (page) => !EMPTY.some((c) => page.includes(`/category/${c}/`)),
    }),
  ],
});
