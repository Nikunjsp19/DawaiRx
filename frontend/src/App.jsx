import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Dashboard from './pages/Dashboard'
import ReportDetail from './pages/ReportDetail'
import Login from './pages/Login'
import Admin from './pages/Admin'
import NewReport from './pages/NewReport'
import Settings from './pages/Settings'

function ProtectedRoute({ children }) {
  const { token } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/runs/:runId" element={<ProtectedRoute><ReportDetail /></ProtectedRoute>} />
        <Route path="/new-report" element={<ProtectedRoute><NewReport /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute><Admin /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
