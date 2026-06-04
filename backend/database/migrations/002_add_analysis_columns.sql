-- 의도 분석, 내용 분석 컬럼 추가
ALTER TABLE articles ADD COLUMN IF NOT EXISTS intent_type TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS content_type TEXT;
