import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Home from './pages/Home'
import UploadCV from './pages/UploadCV'
import Dashboard from './pages/Dashboard'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/upload" element={<UploadCV />} />
        <Route path="/dashboard/:cvId" element={<Dashboard />} />
      </Routes>
    </Layout>
  )
}

export default App
