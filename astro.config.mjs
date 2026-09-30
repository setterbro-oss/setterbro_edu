import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

const SITE_URL = process.env.SITE_URL || 'https://edublog.setterbro.com';

export default defineConfig({
  site: SITE_URL,
  integrations: [sitemap()],
});
