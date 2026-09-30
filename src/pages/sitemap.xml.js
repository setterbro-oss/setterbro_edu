import { getCollection } from 'astro:content';

export async function GET(context) {
  const posts = await getCollection('posts');
  const staticPages = ['', 'about', 'privacy', 'terms'];

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${staticPages.map((page) => `
    <url>
      <loc>${context.site}${page}</loc>
    </url>
  `).join('')}
  ${posts.map((post) => `
    <url>
      <loc>${context.site}posts/${post.slug}/</loc>
    </url>
  `).join('')}
</urlset>`;

  return new Response(sitemap, {
    headers: {
      'Content-Type': 'application/xml'
    }
  });
}
