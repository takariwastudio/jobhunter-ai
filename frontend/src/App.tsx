import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import Layout from './components/layout/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import UploadCV from './pages/UploadCV'
import Dashboard from './pages/Dashboard'
import JobSearch from './pages/JobSearch'

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public auth pages — no Layout wrapper */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* App pages with Layout */}
        <Route path="/" element={<Layout><Home /></Layout>} />
        <Route
          path="/upload"
          element={
            <Layout>
              <ProtectedRoute>
                <UploadCV />
              </ProtectedRoute>
            </Layout>
          }
        />
        <Route
          path="/dashboard/:cvId"
          element={
            <Layout>
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            </Layout>
          }
        />
        <Route
          path="/jobs"
          element={
            <Layout>
              <ProtectedRoute>
                <JobSearch />
              </ProtectedRoute>
            </Layout>
          }
        />
      </Routes>
    </AuthProvider>
  )
}

export default App
