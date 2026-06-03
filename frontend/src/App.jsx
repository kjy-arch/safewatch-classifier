import { useState } from 'react'
import UploadPage from './pages/UploadPage'
import BatchListPage from './pages/BatchListPage'
import BatchDetailPage from './pages/BatchDetailPage'
import AdminPage from './pages/AdminPage'

const NAV = [
  { id: 'upload', label: '분석하기' },
  { id: 'batches', label: '결과 목록' },
  { id: 'admin', label: '관리자' },
]

export default function App() {
  const [page, setPage] = useState('upload')
  const [selectedBatchId, setSelectedBatchId] = useState(null)

  function goToBatch(id) {
    setSelectedBatchId(id)
    setPage('batch-detail')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-blue-700 text-white shadow">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">SafeWatch Classifier</h1>
            <p className="text-blue-200 text-xs">언론·SNS 허위정보 자동 분류 시스템</p>
          </div>
          <nav className="flex gap-2">
            {NAV.map(n => (
              <button
                key={n.id}
                onClick={() => setPage(n.id)}
                className={`px-4 py-1.5 rounded text-sm font-medium transition ${
                  page === n.id ? 'bg-white text-blue-700' : 'text-blue-100 hover:bg-blue-600'
                }`}
              >
                {n.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {page === 'upload' && <UploadPage onComplete={goToBatch} />}
        {page === 'batches' && <BatchListPage onSelect={goToBatch} />}
        {page === 'batch-detail' && (
          <BatchDetailPage batchId={selectedBatchId} onBack={() => setPage('batches')} />
        )}
        {page === 'admin' && <AdminPage />}
      </main>
    </div>
  )
}
