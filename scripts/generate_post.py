import os
import sys
import time
import json
import requests
import hashlib
from datetime import datetime
import random
import re

# GitHub Actions Secret에서 Gemini API 키 가져오기
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set.")
    sys.exit(1)

# 모델명: GitHub 변수(GEMINI_MODEL)가 비어 있어도 기본값이 적용되도록 `or` 사용
GEMINI_MODEL = os.environ.get('GEMINI_MODEL') or 'gemini-3.5-flash'
# 기본 모델이 404(종료)일 때 순서대로 시도할 대체 모델
FALLBACK_MODELS = ['gemini-3.1-flash-lite']


def endpoint_for(model):
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


# 워드프레스와 동일한 카테고리 구성 (slug와 name 일치)
CATEGORY_CONFIGS = {
    'cert': {
        'name': '국가기술 및 전문자격증',
        'query': '국가기술자격증 OR 산업기사 OR 기사시험 OR 전문자격증',
        'longtail': [
            {'title': '2026년 산업안전기사 시험 일정 및 합격 전략', 'desc': '안전 분야 취업 필수 자격증, 시험 일정과 효율적인 학습 전략'},
            {'title': '전기기사 실기 합격 노하우와 시험 준비물 총정리', 'desc': '전기 분야 최고 인기 자격증, 실기 시험 대비 핵심 노하우'},
            {'title': '손해평가사 1차 2차 시험 과목 및 난이도 분석', 'desc': '고소득 전문직 유망 자격증, 시험 과목별 난이도와 합격 전략'},
            {'title': '요양보호사 자격증 취득 절차와 국비지원 교육 안내', 'desc': '고령화 시대 필수 자격증, 취득 과정과 국비지원 훈련 정보'},
            {'title': '건축기사 필기 실기 합격률 분석 및 효율적인 공부법', 'desc': '건축 분야 취업 필수 자격증, 최근 합격률 추이와 공부 방법'},
            {'title': '소방설비기사(전기/기계) 시험 과목 및 독학 가이드', 'desc': '소방 분야 전문 자격증, 필기/실기 과목과 독학 노하우'},
            {'title': '정보처리기사 2026년 시험 개편 사항 및 출제 경향', 'desc': 'IT 분야 기본 자격증, 최신 시험 개편 내용과 출제 방향'},
            {'title': '지게차운전기능사 시험 일정 및 합격률, 취득 비용', 'desc': '건설 현장 필수 자격증, 취득 절차와 소요 비용 상세 안내'},
            {'title': '공인중개사 시험 과목별 공부 전략과 합격 후 진로', 'desc': '부동산 분야 전문 자격증, 과목별 전략과 취업/창업 정보'},
            {'title': '사회복지사 1급 시험 과목 및 단기 합격 노하우', 'desc': '복지 분야 전문 자격증, 시험 과목과 단기간 합격 노하우'}
        ]
    },
    'hrd': {
        'name': '국비지원 내일배움카드',
        'query': '내일배움카드 OR 국비지원 OR K-디지털트레이닝 OR 훈련수당',
        'longtail': [
            {'title': '2026년 내일배움카드 발급 방법과 자격 조건 총정리', 'desc': '국비지원 훈련 필수 카드, 신청 절차와 발급 대상 상세 안내'},
            {'title': 'K-디지털 트레이닝 추천 과정 및 수강생 후기', 'desc': '취업률 높은 인기 K-디지털 훈련 과정과 실제 수강생 리뷰'},
            {'title': '국민취업지원제도 1유형 2유형 훈련수당 지급 기준', 'desc': '구직촉진수당과 훈련참여수당을 받는 조건과 지급액'},
            {'title': '내일배움카드 자부담금 비율과 면제 대상 총정리', 'desc': '국비지원 훈련 시 본인이 내야 하는 금액과 면제 조건 상세 안내'},
            {'title': '직업훈련포털 HRD-Net 활용법과 인기 강좌 찾기', 'desc': '국비지원 훈련 정보 통합 플랫폼, 강좌 검색 및 수강 신청 노하우'},
            {'title': 'IT 국비지원 부트캠프 추천 순위 및 취업률 비교', 'desc': 'IT 분야 취업을 위한 국비지원 부트캠프 과정과 취업 성과'},
            {'title': '실업급여 수급 중 내일배움카드 훈련 참여 방법', 'desc': '실업급여를 받으면서 국비지원 훈련을 받을 수 있는 조건과 절차'},
            {'title': '청년내일채움공제 가입 조건 및 만기 수령액', 'desc': '중소기업 청년의 목돈 마련을 위한 정부 지원금과 자격 요건'},
            {'title': '퇴사 후 내일배움카드 신청 시 유의사항 및 절차', 'desc': '퇴사 후 국비지원 훈련을 받기 위한 준비물과 신청 절차'},
            {'title': '주부·경력단절여성 내일배움카드 추천 직종 및 지원', 'desc': '재취업을 희망하는 주부와 경력단절여성을 위한 국비지원 직업 훈련'}
        ]
    },
    'exam': {
        'name': '공무원·공기업 채용 시험',
        'query': '공무원시험 OR 공기업채용 OR 공무원 가산점 OR NCS',
        'longtail': [
            {'title': '2026년 국가직 9급 공무원 시험 일정 및 경쟁률', 'desc': '공무원 채용 시험 일정과 직렬별 경쟁률 상세 분석'},
            {'title': '공기업 NCS 필기 시험 과목 및 공부 방법', 'desc': '공기업 채용 필수 NCS 시험, 필기 과목별 출제 경향과 대비 전략'},
            {'title': '공무원 시험 가산점 종류와 적용 기준 총정리', 'desc': '공무원 채용 시 가산점을 받을 수 있는 자격증과 비율'},
            {'title': '2026년 공기업 통합 채용 일정 및 선발 인원', 'desc': '주요 공기업 통합 채용 일정과 전년 대비 선발 인원 변화'},
            {'title': '지방직 공무원 시험 경쟁률 및 합격선 분석', 'desc': '지방직 공무원 채용 시험, 지역별 경쟁률과 합격 커트라인'},
            {'title': '공무원 면접 시험 준비 전략과 질문 유형', 'desc': '공무원 채용 면접 시험, 실전 대비 전략과 자주 나오는 질문'},
            {'title': '군무원 채용 시험 일정 및 과목, 경쟁률 분석', 'desc': '군무원 채용 시험, 직렬별 일정과 과목, 경쟁률 상세 안내'},
            {'title': '공기업 채용 전형별 평가 요소 및 합격 전략', 'desc': '공기업 채용 전형별 특징과 합격률을 높이는 전략'},
            {'title': '2026년 경찰공무원 채용 시험 과목 및 준비 전략', 'desc': '경찰공무원 채용 시험, 과목 개편 내용과 효율적인 준비 방법'},
            {'title': '소방공무원 채용 시험 일정 및 체력 시험 가이드', 'desc': '소방공무원 채용 시험, 일정과 필기/체력 시험 대비 노하우'}
        ]
    }
}

# 기존에 발행된 글들의 해시를 저장하는 파일 경로
PUBLISHED_HASHES_FILE = 'scripts/published_hashes.json'
# 마크다운 파일이 저장될 폴더
POSTS_DIR = 'src/content/posts'


def yq(value, limit=None):
    """YAML 프런트매터용 안전한 문자열 (JSON 문자열은 유효한 YAML 큰따옴표 문자열)"""
    text = ' '.join(str(value).split())
    if limit and len(text) > limit:
        text = text[:limit - 1] + '…'
    return json.dumps(text, ensure_ascii=False)


def get_published_hashes():
    """기존 발행된 글들의 해시 목록을 불러옵니다."""
    if os.path.exists(PUBLISHED_HASHES_FILE):
        with open(PUBLISHED_HASHES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_published_hashes(hashes):
    """발행된 글의 해시 목록을 저장합니다."""
    with open(PUBLISHED_HASHES_FILE, 'w', encoding='utf-8') as f:
        json.dump(hashes, f, ensure_ascii=False, indent=2)


def clean_feed_text(text):
    """RSS 피드 텍스트에서 HTML 태그를 제거하고 공백을 정리합니다."""
    # 간단한 태그 제거 (정규식 사용 안 함)
    clean_text = text.replace('<p>', '').replace('</p>', '') \
                     .replace('<b>', '').replace('</b>', '') \
                     .replace('<a>', '').replace('</a>', '')
    return clean_text.strip()


def get_news_from_rss(query, published_hashes):
    """구글 뉴스 RSS에서 새로운 뉴스 아이템을 가져옵니다."""
    feed_url = f'https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=ko&gl=KR&ceid=KR:ko'
    try:
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()  # HTTP 에러 발생 시 예외 처리

        # 간단한 XML 파싱 (외부 라이브러리 사용 안 함)
        items = []
        for line in response.text.split('<item>')[1:]:  # <item> 태그 단위로 분리
            title_match = line.find('<title>')
            link_match = line.find('<link>')
            description_match = line.find('<description>')

            if title_match != -1 and link_match != -1 and description_match != -1:
                title_end = line.find('</title>', title_match)
                link_end = line.find('</link>', link_match)
                desc_end = line.find('</description>', description_match)

                title = clean_feed_text(line[title_match + len('<title>'):title_end])
                link = clean_feed_text(line[link_match + len('<link>'):link_end])
                description = clean_feed_text(line[description_match + len('<description>'):desc_end])

                # 중복 뉴스 제목 제거 (예: "- 뉴스1", "- 연합뉴스")
                title = title.split(' - ')[0].strip()

                if link:
                    item_hash = hashlib.md5(link.encode('utf-8')).hexdigest()
                    if item_hash not in published_hashes:
                        items.append({'title': title, 'desc': description, 'url_hash': item_hash})
                        return items[0]  # 첫 번째 새로운 아이템만 반환

    except requests.exceptions.RequestException as e:
        print(f"RSS fetch error: {e}")
    return None


def generate_post_content(target_title, target_desc, category_cfg, persona):
    """Gemini API를 사용하여 글 내용을 생성합니다. (재시도 + 대체 모델 폴백)"""
    prompt = f"""당신은 [{category_cfg['name']}] 분야 전문 [{persona['role']}]입니다.
핵심 주제: [제목] {target_title} / [요약] {target_desc}
집필 스타일: {persona['tone']}

[💡 구글 Helpful Content & YMYL 팩트체크 절대 준수 지침]
- 🚨 [근거 없는 구체화 금지]: 제공된 정보는 위 '제목'과 '요약'뿐입니다. 여기에 없는 구체적 수치·날짜·금액·기관의 결정·절차 단계·심의 과정을 절대 지어내지 마세요. 확실하지 않은 내용은 '정확한 내용은 공식 공고에서 확인이 필요합니다'로 쓰고, 일반적으로 알려진 제도 개념·확인 방법·주의사항 중심으로 작성하세요.
- 🚨 [일정·금액 표기]: 2026년 시험 일정, 지원 금액, 경쟁률 등 구체 수치는 확실한 경우에만 쓰고, 아니면 해당 공식 기관에서 확인하라고 안내하세요. 표(table)도 확실한 항목만 채우세요.
- 🚨 [수치 날조 및 과장 절대 금지]: 공인되지 않은 임의의 금리, 비현실적인 환급액을 날조하지 마세요. 뉴스 및 제도상 확인 가능한 객관적 사실만 서술하세요.
- 🚨 [가짜 경험담 금지]: '김 모 씨', '현장에서 만나본 사례' 등 실재하지 않는 가상의 사용자 인터뷰를 절대 지어내지 마세요.
- 🚨 [제목 작성 규칙]: 제목 첫머리에 '모르면 있는', '모르면 잃는', '즉시 확인' 같은 특정 어구를 도배하지 마세요. '2026 총정리', '신청 자격 가이드', '놓치면 손해 보는', '실제 환급액 기준', '지원 요건 핵심 요약' 등 자연스럽게 작성하세요. (45자 내외)
- 🚨 [체크리스트 작성]: `editor_note` 항목에는 가짜 1인칭 후기 대신, 독자가 신청 전 반드시 점검해야 할 '실무 행정 필수 체크리스트 3~4문장'을 객관적으로 작성하세요.

가이드라인:
1. english_slug: 검색 친화적인 3~5개 영단어 하이픈 조합
2. title: 위 규칙을 적용한 매력적이고 자연스러운 제목
3. keywords: 핵심 명사 2~3개 쉼표 구분
4. faqs: 자주 묻는 질문 2가지 [{{'q': '질문', 'a': '답변'}}]
5. official_source: 관련 정부/공공기관 명칭과 누리집 주소 객체 (예: {{'name': '한국산업인력공단 큐넷', 'url': 'https://www.q-net.or.kr'}})
6. editor_note: 실무 행정 체크리스트 및 필수 주의사항 3~4문장
6-1. meta_description: 검색 결과에 노출될 글 요약 1문장 (80~130자, 따옴표·줄바꿈 없이, 본문 핵심을 구체적으로)
7. content_markdown: (HTML이 아닌 Markdown 형식으로 본문 작성)
   - 도입부: <div style='background:#f8f9fa; padding:15px; border-left:4px solid #003366; margin-bottom:20px;'>핵심 3줄 요약 박스</div>
   - 본문 중간: 대상자별 지원 금액, 소득 기준이 담긴 깔끔한 <table> 태그 표 필수 포함
   - h2 태그 3개 이상, 분량 1,800자 이상

반드시 유효한 순수 JSON 형식으로만 응답하세요. 키: english_slug, title, keywords, faqs, official_source, editor_note, meta_description, content_markdown
"""
    headers = {'Content-Type': 'application/json', 'x-goog-api-key': GEMINI_API_KEY}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.3}
    }

    models = [GEMINI_MODEL] + [m for m in FALLBACK_MODELS if m != GEMINI_MODEL]

    for model in models:
        for attempt in range(1, 4):
            try:
                response = requests.post(
                    endpoint_for(model), headers=headers,
                    data=json.dumps(data), timeout=90
                )

                # 404: 모델이 종료/변경됨 → 재시도 없이 다음 모델로
                if response.status_code == 404:
                    print(f"⚠️ 모델 사용 불가(404): {model} → 다음 모델로 전환합니다.")
                    break

                # 429/5xx: 일시적 오류 → 대기 후 재시도
                if response.status_code in (429, 500, 502, 503, 504):
                    wait = 15 * attempt
                    print(f"⚠️ {model} 일시 오류({response.status_code}), {wait}초 후 재시도 ({attempt}/3)")
                    time.sleep(wait)
                    continue

                response.raise_for_status()

                raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                clean_json = raw_text.replace('```json', '').replace('```', '').strip()
                result = json.loads(clean_json)
                print(f"✅ 글 생성 성공 (모델: {model})")
                return result

            except Exception as e:
                print(f"Gemini API error ({model}, 시도 {attempt}/3): {e}")
                time.sleep(5 * attempt)

    return None


def main():
    published_hashes = get_published_hashes()

    # 카테고리 순환 로직 (가장 오래된 발행 카테고리 선택)
    category_slugs = list(CATEGORY_CONFIGS.keys())
    # 글 수가 가장 적은 카테고리를 우선 선택 (동률이면 랜덤) → 카테고리 균형 유지
    counts = {slug: 0 for slug in category_slugs}
    if os.path.isdir(POSTS_DIR):
        for fname in os.listdir(POSTS_DIR):
            if not fname.endswith('.md'):
                continue
            with open(os.path.join(POSTS_DIR, fname), 'r', encoding='utf-8') as pf:
                m = re.search(r'^category:\s*["\']?(\w+)["\']?', pf.read(), re.M)
            if m and m.group(1) in counts:
                counts[m.group(1)] += 1
    min_count = min(counts.values())
    chosen_slug = random.choice([k for k, v in counts.items() if v == min_count])
    category_cfg = CATEGORY_CONFIGS[chosen_slug]

    print(f"⏰ 선택된 카테고리: {category_cfg['name']}")

    target_item = None

    # 1차: 구글 뉴스 RSS에서 새 글감 탐색
    target_item = get_news_from_rss(category_cfg['query'], published_hashes)

    # 2차: RSS 실패 시 롱테일 글감 탐색
    if not target_item:
        for lt_item in category_cfg['longtail']:
            lt_hash = hashlib.md5(f"longtail_{lt_item['title']}".encode('utf-8')).hexdigest()
            if lt_hash not in published_hashes:
                target_item = {'title': lt_item['title'], 'desc': lt_item['desc'], 'url_hash': lt_hash}
                break

    # 3차: 모든 글감 고갈 시 동적 AI 주제 생성
    if not target_item:
        dynamic_seed = datetime.now().strftime('%Y년 %m월 ') + category_cfg['name'] + ' 실시간 개정안 핵심 가이드'
        target_item = {
            'title': dynamic_seed,
            'desc': f"대중들이 가장 많이 궁금해하는 {category_cfg['name']} 분야의 최신 개정 사항과 실질적인 혜택 신청 기준.",
            'url_hash': hashlib.md5(f"dynamic_{dynamic_seed}_{datetime.now().strftime('%Y%m%d_%H%M%S')}".encode('utf-8')).hexdigest()
        }

    if not target_item:
        print("❌ 모든 글감 소진 및 새로운 글감 생성 실패.")
        sys.exit(1)

    print(f"🔍 확정된 글감: {target_item['title']}")

    personas = [
        {'role': '1:1 맞춤 금융 상담관', 'tone': '독자와 1:1 상담하듯 신뢰감 있고 친절하며 객관적인 어조를 사용하세요.'},
        {'role': '공공정책 수석 행정 분석가', 'tone': '공식 지침을 명확하고 체계적인 순서도로 정리하는 어투로 서술하세요.'},
        {'role': '실전 재테크 칼럼니스트', 'tone': '실제 혜택 대상자의 실질적인 조건 비교를 중심으로 팩트 위주로 서술하세요.'}
    ]
    selected_persona = random.choice(personas)

    # Gemini API 호출하여 글 내용 생성
    ai_response_data = generate_post_content(target_item['title'], target_item['desc'], category_cfg, selected_persona)

    if not ai_response_data:
        print("❌ AI 글 생성 실패. 워크플로우를 실패 처리합니다.")
        sys.exit(1)

    # 필수 필드 검증
    for key in ('title', 'content_markdown'):
        if not ai_response_data.get(key):
            print(f"❌ AI 응답에 '{key}' 없음. 워크플로우를 실패 처리합니다.")
            sys.exit(1)

    # 파일명(slug) 정리 + 중복 방지
    file_slug = str(ai_response_data.get('english_slug', '')).lower().replace(' ', '-')
    file_slug = re.sub(r'[^a-z0-9-]', '', file_slug).strip('-')[:50]
    if not file_slug:
        file_slug = 'post-' + datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = f"{POSTS_DIR}/{file_slug}.md"
    if os.path.exists(filename):
        file_slug = f"{file_slug}-{datetime.now().strftime('%Y%m%d%H%M')}"
        filename = f"{POSTS_DIR}/{file_slug}.md"

    # 🔥 [중복 발행 방지] 최종 해시 검증
    if target_item['url_hash'] in published_hashes:
        print(f"⚠️ 이미 발행된 해시입니다. 발행을 건너뜁니다: {target_item['title']}")
        return

    source = ai_response_data.get('official_source') or {}
    source_name = source.get('name', '')
    source_url = source.get('url', '')

    # f-string 안에 백슬래시를 쓰면 Python 3.11에서 SyntaxError → 값은 미리 계산
    fm_title = yq(ai_response_data['title'])
    fm_desc = yq(ai_response_data.get('meta_description') or ai_response_data.get('editor_note') or target_item['desc'], limit=160)
    fm_source_name = yq(source_name)
    fm_source_url = yq(source_url)
    today = datetime.now().strftime('%Y-%m-%d')

    # FAQ를 본문 끝에 추가 (체류시간·검색 유입 보강)
    faq_md = ''
    valid_faqs = [f for f in (ai_response_data.get('faqs') or [])
                  if isinstance(f, dict) and f.get('q') and f.get('a')]
    if valid_faqs:
        faq_md = '\n\n## 자주 묻는 질문\n\n' + '\n\n'.join(
            f"**Q. {' '.join(str(f['q']).split())}**\n\nA. {' '.join(str(f['a']).split())}" for f in valid_faqs
        )

    markdown_content = (
        "---\n"
        f"title: {fm_title}\n"
        f"description: {fm_desc}\n"
        f"pubDate: {today}\n"
        f"category: \"{chosen_slug}\"\n"
        f"source_name: {fm_source_name}\n"
        f"source_url: {fm_source_url}\n"
        "---\n\n"
        f"{ai_response_data['content_markdown']}{faq_md}\n"
    )
    # 디렉토리 생성 (없는 경우)
    os.makedirs(POSTS_DIR, exist_ok=True)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    published_hashes.append(target_item['url_hash'])
    save_published_hashes(published_hashes)

    print(f"🎉 글 발행 성공: {filename}")


if __name__ == "__main__":
    main()
