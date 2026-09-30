import { defineCollection, z } from 'astro:content';

const posts = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    category: z.string(),
    source_name: z.string().optional(),
    source_url: z.string().optional(),
  }),
});

export const collections = { posts };
