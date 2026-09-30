import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context) {
  // 'posts' 또는 본인의 블로그 컨텐츠 컬렉션 이름을 적어주세요 (보통 posts 또는 blog)
  const posts = await getCollection('posts'); 
  return rss({
    title: '나의 자동화 교육 블로그',
    description: '자격증 및 국비지원 정보 제공 블로그',
    site: context.site,
    items: posts.map((post) => ({
      title: post.data.title,
      pubDate: post.data.pubDate,
      description: post.data.description,
      link: `/posts/${post.slug}/`,
    })),
  });
}
