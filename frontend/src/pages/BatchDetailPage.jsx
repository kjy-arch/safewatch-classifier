import { useState, useEffect } from 'react'
import { getBatch, downloadUrl } from '../api'

const LEVEL_STYLE = {
  높음: 'bg-red-100 text-red-700',
  중간: 'bg-yellow-100 text-yellow-700',
  낮음: 'bg-green-100 text-green-700',
}

const INTENT_STYLE = {
  '악의적 유포': 'bg-red-50 text-red-600',
  '단순 오해':   'bg-orange-50 text-orange-600',
  '풍자/비판':   'bg-purple-50 text-purple-600',
  '사실 보도':   'bg-green-50 text-green-600',
  '불명확':      'bg-gray-100 text-gray-500',
}

const CONTENT_STYLE = {
  '사실관계 오류': 'bg-red-50 text-red-600',
  '과장/왜곡':    'bg-orange-50 text-orange-600',
  '출처 불명':    'bg-yellow-50 text-yellow-600',
  '맥락 누락':    'bg-blue-50 text-blue-600',
  '문제없음':     'bg-green-50 text-green-600',
}

export default function BatchDetailPage({ batchId, onBack }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [batchId])

  async function load() {
    setLoading(true)
    const result = await getBatch(batchId)
    setData(result)
    setLoading(false)
    if (result.batch.analyzed_rows < result.batch.total_rows) {
      setTimeout(() => load(), 5000)
    }
  }

  if (loading) return <p className="text-center text-gray-400 py-16">불러오는 중...</p>
  if (!data) return null

  const { batch, articles } = data
  const done = batch.analyzed_rows === batch.total_rows

  // 의도 유형 집계
  const intentCounts = articles.reduce((acc, a) => {
    if (a.intent_type) acc[a.intent_type] = (acc[a.intent_type] || 0) + 1
    return acc
  }, {})

  return (
    <div>
      {/* 상단 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <button onClick={onBack} className="text-blue-500 hover:underline text-sm mb-1">← 목록으로</button>
          <h2 className="text-2xl font-bold text-gray-800">{batch.file_name}</h2>
          <p className="text-gray-400 text-sm mt-0.5">
            {new Date(batch.created_at).toLocaleString('ko-KR')} · 총 {batch.total_rows}행
          </p>
        </div>
        <div className="flex gap-2 items-center">
          {!done && (
            <span className="text-yellow-600 text-sm animate-pulse">
              ⏳ 분석 중... ({batch.analyzed_rows}/{batch.total_rows})
            </span>
          )}
          {done && (
            <a href={downloadUrl(batchId)} download
              className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition">
              📥 엑셀 다운로드
            </a>
          )}
          <button onClick={load}
            className="px-3 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm hover:bg-gray-200 transition">
            🔄 새로고침
          </button>
        </div>
      </div>

      {/* 통계 카드 */}
      {done && (
        <div className="grid grid-cols-2 gap-4 mb-6">
          {/* 거짓 척도 */}
          <div className="bg-white rounded-xl shadow p-4">
            <p className="text-xs font-medium text-gray-400 mb-3">거짓 척도 분포</p>
            <div className="flex gap-3">
              {['높음', '중간', '낮음'].map(level => {
                const count = articles.filter(a => a.false_level === level).length
                return (
                  <div key={level} className={`flex-1 rounded-lg p-3 text-center ${LEVEL_STYLE[level]}`}>
                    <p className="text-2xl font-bold">{count}</p>
                    <p className="text-xs font-medium mt-0.5">{level}</p>
                  </div>
                )
              })}
            </div>
          </div>
          {/* 의도 유형 */}
          <div className="bg-white rounded-xl shadow p-4">
            <p className="text-xs font-medium text-gray-400 mb-3">의도 유형 분포</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(intentCounts).map(([type, count]) => (
                <span key={type} className={`px-2 py-1 rounded-full text-xs font-medium ${INTENT_STYLE[type] || 'bg-gray-100 text-gray-500'}`}>
                  {type} {count}건
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 결과 테이블 */}
      <div className="bg-white rounded-xl shadow overflow-x-auto">
        <table className="w-full text-sm min-w-[900px]">
          <thead className="bg-gray-50 text-gray-500 border-b">
            <tr>
              <th className="px-4 py-3 text-left">원문</th>
              <th className="px-4 py-3 text-center">출처</th>
              <th className="px-4 py-3 text-center">거짓점수</th>
              <th className="px-4 py-3 text-center">척도</th>
              <th className="px-4 py-3 text-center">의도 유형</th>
              <th className="px-4 py-3 text-center">내용 유형</th>
              <th className="px-4 py-3 text-left">판단 이유</th>
            </tr>
          </thead>
          <tbody>
            {articles.map(a => (
              <tr key={a.id} className="border-b last:border-0 hover:bg-gray-50">
                <td className="px-4 py-3 text-gray-700 max-w-[240px]">
                  <p className="line-clamp-2 text-xs">{a.original_text}</p>
                  {a.source_url && (
                    <a href={a.source_url} target="_blank" rel="noreferrer"
                      className="text-blue-400 text-xs hover:underline">링크 →</a>
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">{a.source_type}</span>
                </td>
                <td className="px-4 py-3 text-center font-bold text-gray-700">{a.false_score ?? '—'}</td>
                <td className="px-4 py-3 text-center">
                  {a.false_level
                    ? <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${LEVEL_STYLE[a.false_level]}`}>{a.false_level}</span>
                    : '—'}
                </td>
                <td className="px-4 py-3 text-center">
                  {a.intent_type
                    ? <span className={`px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap ${INTENT_STYLE[a.intent_type] || 'bg-gray-100 text-gray-500'}`}>{a.intent_type}</span>
                    : '—'}
                </td>
                <td className="px-4 py-3 text-center">
                  {a.content_type
                    ? <span className={`px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap ${CONTENT_STYLE[a.content_type] || 'bg-gray-100 text-gray-500'}`}>{a.content_type}</span>
                    : '—'}
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">{a.false_reason ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
