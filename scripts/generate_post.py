import os
import sys
import time
import json
import requests
import hashlib
from datetime import datetime
import random
import re
import html
import xml.etree.ElementTree as ET

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
# 발행된 글(원본 뉴스 제목 + 생성 제목) 목록 → 같은 주제 중복 발행 방지
PUBLISHED_TITLES_FILE = 'scripts/published_titles.json'
# 마크다운 파일이 저장될 폴더
POSTS_DIR = 'src/content/posts'

# 제목 유사도 임계값 (0~1). 이 값 이상이면 같은 주제로 보고 건너뜀
SIMILARITY_THRESHOLD = 0.6
# 중복 발견 시 다른 글감으로 재시도할 최대 횟수
MAX_TOPIC_ATTEMPTS = 4

# 유사도 계산 시 무시할 흔한 단어
TITLE_STOPWORDS = {
    '및', '안내', '가이드', '요약', '핵심', '총정리', '방법', '비교', '제도', '도입',
    '정리', '분석', '2026', '2026년', '대한', '위한', '최신', '완벽', '실시간'
}


def yq(value, limit=None):
    """YAML 프런트매터용 안전한 문자열 (JSON 문자열은 유효한 YAML 큰따옴표 문자열)"""
    text = ' '.join(str(value).split())
    if limit and len(text) > limit:
        text = text[:limit - 1] + '…'
    return json.dumps(text, ensure_ascii=False)


def load_json_list(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []
    return []


def save_json_list(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_published_hashes():
    """기존 발행된 글들의 해시 목록을 불러옵니다."""
    return load_json_list(PUBLISHED_HASHES_FILE)


def save_published_hashes(hashes):
    """발행된 글의 해시 목록을 저장합니다."""
    save_json_list(PUBLISHED_HASHES_FILE, hashes)


# ───────────── 중복 주제 감지 (제목 유사도) ─────────────
def _bigrams(title):
    text = re.sub(r'[^0-9a-zA-Z가-힣\s]', ' ', str(title).lower())
    words = [w for w in text.split() if w not in TITLE_STOPWORDS]
    joined = ''.join(words)
    return {joined[i:i + 2] for i in range(len(joined) - 1)}


def title_similarity(a, b):
    """두 제목의 유사도(0~1). 글자 2-gram 겹침 비율(작은 쪽 기준)."""
    set_a, set_b = _bigrams(a), _bigrams(b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / min(len(set_a), len(set_b))


def load_existing_titles():
    """이미 발행된 모든 제목 수집: published_titles.json + 현재 posts 폴더의 title"""
    titles = [t for t in load_json_list(PUBLISHED_TITLES_FILE) if isinstance(t, str)]
    if os.path.isdir(POSTS_DIR):
        for fname in os.listdir(POSTS_DIR):
            if not fname.endswith('.md'):
                continue
            with open(os.path.join(POSTS_DIR, fname), 'r', encoding='utf-8') as pf:
                m = re.search(r'^title:\s*(.+)$', pf.read(), re.M)
            if m:
                titles.append(m.group(1).strip().strip('"\''))
    return list(dict.fromkeys(titles))  # 순서 유지 + 중복 제거


def find_similar_title(title, existing_titles):
    """기존 제목 중 임계값 이상 유사한 것이 있으면 (제목, 점수) 반환"""
    best = (None, 0.0)
    for old in existing_titles:
        score = title_similarity(title, old)
        if score > best[1]:
            best = (old, score)
    if best[1] >= SIMILARITY_THRESHOLD:
        return best
    return None


def remember_topic(published_hashes, existing_titles, url_hash, *titles):
    """해시와 제목을 기록하고 즉시 저장 (다음 시도/다음 실행에서 재사용 방지)"""
    if url_hash not in published_hashes:
        published_hashes.append(url_hash)
    for t in titles:
        if t and t not in existing_titles:
            existing_titles.append(t)
    save_published_hashes(published_hashes)
    save_json_list(PUBLISHED_TITLES_FILE, existing_titles)


# ───────────── RSS ─────────────
def get_news_candidates(query, published_hashes, existing_titles, limit=10):
    """구글 뉴스 RSS에서 '링크도 제목도 처음 보는' 새 뉴스 후보 목록을 가져옵니다."""
    feed_url = f'https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=ko&gl=KR&ceid=KR:ko'
    candidates = []
    try:
        response = requests.get(feed_url, timeout=15)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        for item in root.iter('item'):
            raw_title = (item.findtext('title') or '').strip()
            link = (item.findtext('link') or '').strip()
            raw_desc = item.findtext('description') or ''
            if not raw_title or not link:
                continue

            # 언론사 꼬리표 제거 (예: "제목 - 연합뉴스")
            title = html.unescape(raw_title).rsplit(' - ', 1)[0].strip()
            desc = re.sub(r'<[^>]+>', ' ', html.unescape(raw_desc))
            desc = ' '.join(desc.split()) or title

            item_hash = hashlib.md5(link.encode('utf-8')).hexdigest()
            if item_hash in published_hashes:
                continue
            # 🔥 링크가 달라도 같은 사건(다른 언론사 기사)이면 제외
            if find_similar_title(title, existing_titles):
                continue
            # 이번 후보들끼리도 중복 제거
            if any(title_similarity(title, c['title']) >= SIMILARITY_THRESHOLD for c in candidates):
                continue

            candidates.append({'title': title, 'desc': desc, 'url_hash': item_hash})
            if len(candidates) >= limit:
                break

    except Exception as e:
        print(f"RSS fetch error: {e}")
    return candidates


def get_longtail_candidates(category_cfg, published_hashes, existing_titles):
    """롱테일 글감 중 아직 안 쓴 것들"""
    result = []
    for lt_item in category_cfg['longtail']:
        lt_hash = hashlib.md5(f"longtail_{lt_item['title']}".encode('utf-8')).hexdigest()
        if lt_hash in published_hashes:
            continue
        if find_similar_title(lt_item['title'], existing_titles):
            continue
        result.append({'title': lt_item['title'], 'desc': lt_item['desc'], 'url_hash': lt_hash})
    return result


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


def build_markdown(ai, target_item, chosen_slug):
    source = ai.get('official_source') or {}
    fm_title = yq(ai['title'])
    fm_desc = yq(ai.get('meta_description') or ai.get('editor_note') or target_item['desc'], limit=160)
    fm_source_name = yq(source.get('name', ''))
    fm_source_url = yq(source.get('url', ''))
    today = datetime.now().strftime('%Y-%m-%d')

    faq_md = ''
    valid_faqs = [f for f in (ai.get('faqs') or [])
                  if isinstance(f, dict) and f.get('q') and f.get('a')]
    if valid_faqs:
        faq_md = '\n\n## 자주 묻는 질문\n\n' + '\n\n'.join(
            f"**Q. {' '.join(str(f['q']).split())}**\n\nA. {' '.join(str(f['a']).split())}" for f in valid_faqs
        )

    return (
        "---\n"
        f"title: {fm_title}\n"
        f"description: {fm_desc}\n"
        f"pubDate: {today}\n"
        f"category: \"{chosen_slug}\"\n"
        f"source_name: {fm_source_name}\n"
        f"source_url: {fm_source_url}\n"
        "---\n\n"
        f"{ai['content_markdown']}{faq_md}\n"
    )


def main():
    published_hashes = get_published_hashes()
    existing_titles = load_existing_titles()

    # 글 수가 가장 적은 카테고리를 우선 선택 (동률이면 랜덤) → 카테고리 균형 유지
    category_slugs = list(CATEGORY_CONFIGS.keys())
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

    # 글감 후보: 1차 RSS 뉴스 → 2차 롱테일 (모두 중복 필터 통과분만)
    candidates = get_news_candidates(category_cfg['query'], published_hashes, existing_titles)
    candidates += get_longtail_candidates(category_cfg, published_hashes, existing_titles)

    # 3차: 모든 글감 고갈 시 동적 주제 (월 단위로 고정 → 같은 달 중복 방지)
    if not candidates:
        dynamic_seed = datetime.now().strftime('%Y년 %m월 ') + category_cfg['name'] + ' 실시간 개정안 핵심 가이드'
        dyn_hash = hashlib.md5(f"dynamic_{dynamic_seed}".encode('utf-8')).hexdigest()
        if dyn_hash not in published_hashes and not find_similar_title(dynamic_seed, existing_titles):
            candidates.append({
                'title': dynamic_seed,
                'desc': f"대중들이 가장 많이 궁금해하는 {category_cfg['name']} 분야의 최신 개정 사항과 실질적인 혜택 신청 기준.",
                'url_hash': dyn_hash
            })

    if not candidates:
        print("ℹ️ 새로 발행할 글감이 없습니다(모두 중복). 이번 실행은 발행 없이 종료합니다.")
        return

    personas = [
        {'role': '1:1 맞춤 금융 상담관', 'tone': '독자와 1:1 상담하듯 신뢰감 있고 친절하며 객관적인 어조를 사용하세요.'},
        {'role': '공공정책 수석 행정 분석가', 'tone': '공식 지침을 명확하고 체계적인 순서도로 정리하는 어투로 서술하세요.'},
        {'role': '실전 재테크 칼럼니스트', 'tone': '실제 혜택 대상자의 실질적인 조건 비교를 중심으로 팩트 위주로 서술하세요.'}
    ]

    for attempt, target_item in enumerate(candidates[:MAX_TOPIC_ATTEMPTS], start=1):
        print(f"🔍 글감 ({attempt}/{MAX_TOPIC_ATTEMPTS}): {target_item['title']}")

        ai = generate_post_content(target_item['title'], target_item['desc'], category_cfg, random.choice(personas))
        if not ai:
            print("❌ AI 글 생성 실패. 워크플로우를 실패 처리합니다.")
            sys.exit(1)

        for key in ('title', 'content_markdown'):
            if not ai.get(key):
                print(f"❌ AI 응답에 '{key}' 없음. 워크플로우를 실패 처리합니다.")
                sys.exit(1)

        # 🔥 [중복 발행 방지] 생성된 제목도 기존 글과 비교
        dup = find_similar_title(ai['title'], existing_titles)
        if dup:
            print(f"⚠️ 기존 글과 유사({dup[1]:.2f}): '{dup[0]}' → 이 글감은 건너뛰고 다음 글감을 시도합니다.")
            remember_topic(published_hashes, existing_titles, target_item['url_hash'], target_item['title'])
            continue

        # 파일명(slug) 정리 + 중복 방지
        file_slug = str(ai.get('english_slug', '')).lower().replace(' ', '-')
        file_slug = re.sub(r'[^a-z0-9-]', '', file_slug).strip('-')[:50]
        if not file_slug:
            file_slug = 'post-' + datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = f"{POSTS_DIR}/{file_slug}.md"
        if os.path.exists(filename):
            file_slug = f"{file_slug}-{datetime.now().strftime('%Y%m%d%H%M')}"
            filename = f"{POSTS_DIR}/{file_slug}.md"

        os.makedirs(POSTS_DIR, exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(build_markdown(ai, target_item, chosen_slug))

        remember_topic(published_hashes, existing_titles, target_item['url_hash'],
                       target_item['title'], ai['title'])
        print(f"🎉 글 발행 성공: {filename}")
        return

    print("ℹ️ 시도한 글감이 모두 기존 글과 중복되어 이번 실행은 발행 없이 종료합니다.")


if __name__ == "__main__":
    main()
