import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://edublog.setterbro.com',
  integrations: [
    sitemap({
      // sitemap 내부에서 에러가 나지 않도록 기본 필터 옵션 추가
      filter: (page) => page !== 'https://edublog.setterbro.com/404',
    }),
  ],
});
