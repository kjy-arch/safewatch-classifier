# SafeWatch Classifier — 프로젝트 스펙

> SafeWatch의 수동 분석 모듈. 엑셀로 업로드된 텍스트를 AI가 분석하여 거짓 척도와 연관 부서를 분류하고 결과를 엑셀로 다운로드한다.

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 프로젝트명 | SafeWatch Classifier |
| 목적 | 언론·SNS·커뮤니티·유튜브 텍스트의 거짓 가능성 및 연관 부서 자동 분류 |
| 포지션 | SafeWatch의 수동 분석 모듈 (나중에 SafeWatch 안으로 통합) |
| 운영 환경 | 외부망 전용 |

---

## 2. 기술 스택

| 영역 | 기술 |
|------|------|
| 백엔드 | Python 3.11 / FastAPI |
| 프론트엔드 | React (Lovable로 생성) |
| DB | Supabase (기존 SafeWatch 프로젝트에 테이블 추가) |
| AI | Gemini 2.0 Flash API |
| RAG 문서 | PDF + 웹페이지 URL |
| 배포 | 추후 결정 |

---

## 3. 분석 출처 유형

- 언론 기사 (뉴스)
- SNS (트위터, 페이스북, 인스타그램 등)
- 커뮤니티 (디시인사이드, 클리앙, 에펨코리아 등)
- 유튜브 댓글

---

## 4. 핵심 기능

### 4-1. 엑셀 업로드 및 분석
- `.xlsx` 파일 업로드 (100~200행)
- 행별로 Gemini API 호출하여 분석
- 출처 유형에 따라 프롬프트 분기

### 4-2. 분석 결과 항목
| 필드 | 설명 |
|------|------|
| `false_score` | 거짓 가능성 수치 (0~100) |
| `false_level` | 거짓 척도 레이블 (낮음 / 중간 / 높음) |
| `false_reason` | 판단 이유 한 줄 요약 |
| `department` | 연관 부서명 |
| `source_type` | 출처 유형 (언론/SNS/커뮤니티/유튜브) |

### 4-3. 판단 기준 (혼합 방식)
- 기본: Gemini AI 자체 판단
- 공식 문서(PDF, 웹 URL)가 있을 때: RAG로 우선 참조

### 4-4. 결과 엑셀 다운로드
- 원본 데이터 + 분석 결과 컬럼 추가하여 `.xlsx` 다운로드

### 4-5. 관리자 화면 (부서 키워드 관리)
- 부서명 추가 / 수정 / 삭제
- 부서별 키워드 목록 관리 (코드 수정 없이 UI에서 직접)

### 4-6. 분기 보고 (3개월 주기)
- 기간별 분석 결과 집계
- 거짓 척도 분포, 부서별 통계

---

## 5. 사용 흐름

```
담당자 → 엑셀 업로드 → AI 분석 → 결과 확인
    → 각 부서에 배포 (부서별 담당자가 진실 여부 확인)
    → 3개월마다 간부 보고 (집계 리포트)
```

---

## 6. DB 테이블 구조 (Supabase)

### articles (분석 결과)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | uuid | PK |
| original_text | text | 원문 텍스트 |
| source_type | text | 출처 유형 |
| source_url | text | 원문 URL (있을 경우) |
| false_score | int | 거짓 수치 0~100 |
| false_level | text | 낮음/중간/높음 |
| false_reason | text | 판단 이유 |
| department_id | uuid | 연관 부서 FK |
| batch_id | uuid | 업로드 배치 FK |
| created_at | timestamp | 생성일시 |

### departments (부서 목록)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | uuid | PK |
| name | text | 부서명 |
| keywords | text[] | 매칭 키워드 목록 |
| created_at | timestamp | 생성일시 |

### batches (업로드 배치)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | uuid | PK |
| file_name | text | 업로드 파일명 |
| total_rows | int | 총 행 수 |
| analyzed_rows | int | 분석 완료 행 수 |
| created_at | timestamp | 생성일시 |

### official_docs (RAG용 공식 문서)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | uuid | PK |
| title | text | 문서 제목 |
| doc_type | text | pdf / url |
| content | text | 추출된 텍스트 |
| source | text | 파일 경로 또는 URL |
| created_at | timestamp | 생성일시 |

---

## 7. API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/upload` | 엑셀 파일 업로드 및 분석 시작 |
| GET | `/api/batches` | 업로드 배치 목록 조회 |
| GET | `/api/batches/{id}` | 특정 배치 분석 결과 조회 |
| GET | `/api/batches/{id}/download` | 결과 엑셀 다운로드 |
| GET | `/api/departments` | 부서 목록 조회 |
| POST | `/api/departments` | 부서 추가 |
| PUT | `/api/departments/{id}` | 부서 수정 |
| DELETE | `/api/departments/{id}` | 부서 삭제 |
| POST | `/api/docs` | 공식 문서 업로드 (RAG용) |
| GET | `/api/docs` | 공식 문서 목록 조회 |

---

## 8. 폴더 구조

```
safewatch-classifier/
├── SPEC.md
├── README.md
├── backend/
│   └── app/
│       ├── api/          # FastAPI 라우터
│       ├── core/         # 설정, DB 연결
│       ├── models/       # Pydantic 모델
│       ├── services/     # 비즈니스 로직 (AI, 엑셀, RAG)
│       └── utils/        # 공통 유틸
├── frontend/             # React (Lovable 생성)
└── docs/                 # 공식 문서 보관
```

---

## 9. 개발 단계

| 단계 | 내용 | 상태 |
|------|------|------|
| 1 | 폴더 구조 + SPEC.md | ✅ 완료 |
| 2 | Supabase 테이블 생성 | ⬜ 대기 |
| 3 | FastAPI 기본 세팅 | ⬜ 대기 |
| 4 | 엑셀 업로드 + 파싱 | ⬜ 대기 |
| 5 | Gemini API 분석 연동 | ⬜ 대기 |
| 6 | RAG 공식 문서 연동 | ⬜ 대기 |
| 7 | 결과 엑셀 다운로드 | ⬜ 대기 |
| 8 | 프론트엔드 (Lovable) | ⬜ 대기 |
| 9 | 관리자 화면 | ⬜ 대기 |
| 10 | 분기 보고 기능 | ⬜ 대기 |
