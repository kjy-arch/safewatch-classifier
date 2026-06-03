-- SafeWatch Classifier 초기 테이블 생성
-- Supabase 대시보드 > SQL Editor에서 실행하세요.

-- 1. 업로드 배치 (batches)
CREATE TABLE IF NOT EXISTS batches (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name   TEXT NOT NULL,
    total_rows  INT NOT NULL DEFAULT 0,
    analyzed_rows INT NOT NULL DEFAULT 0,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 부서 목록 (departments)
CREATE TABLE IF NOT EXISTS departments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL UNIQUE,
    keywords    TEXT[] NOT NULL DEFAULT '{}',
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 분석 결과 (articles)
CREATE TABLE IF NOT EXISTS articles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_text   TEXT NOT NULL,
    source_type     TEXT NOT NULL CHECK (source_type IN ('언론', 'SNS', '커뮤니티', '유튜브')),
    source_url      TEXT,
    false_score     INT CHECK (false_score BETWEEN 0 AND 100),
    false_level     TEXT CHECK (false_level IN ('낮음', '중간', '높음')),
    false_reason    TEXT,
    department_id   UUID REFERENCES departments(id) ON DELETE SET NULL,
    batch_id        UUID REFERENCES batches(id) ON DELETE CASCADE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. RAG용 공식 문서 (official_docs)
CREATE TABLE IF NOT EXISTS official_docs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       TEXT NOT NULL,
    doc_type    TEXT NOT NULL CHECK (doc_type IN ('pdf', 'url')),
    content     TEXT NOT NULL,
    source      TEXT NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_articles_batch_id    ON articles(batch_id);
CREATE INDEX IF NOT EXISTS idx_articles_department_id ON articles(department_id);
CREATE INDEX IF NOT EXISTS idx_articles_created_at  ON articles(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_batches_created_at   ON batches(created_at DESC);

-- 기본 부서 데이터 삽입 (수정 가능)
INSERT INTO departments (name, keywords) VALUES
    ('병역판정과',    ARRAY['신체검사', '병역판정', '현역', '보충역', '전문연구요원']),
    ('사회복무과',    ARRAY['사회복무', '공익근무', '대체복무', '사회복무요원']),
    ('입영동원과',    ARRAY['입영', '현역입영', '동원훈련', '예비군']),
    ('병역면탈수사과', ARRAY['병역면탈', '위조', '허위', '비리', '부정']),
    ('홍보과',        ARRAY['홍보', '캠페인', '보도자료', '언론'])
ON CONFLICT (name) DO NOTHING;
