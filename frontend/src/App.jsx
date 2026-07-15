import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import Hub from './pages/Hub'
import OptimizeImages from './pages/OptimizeImages'
import OptimizeVideos from './pages/OptimizeVideos'
import SignImages from './pages/SignImages'
import SmoothImages from './pages/SmoothImages'
import Security from './pages/Security'

import { Analytics } from '@vercel/analytics/react'

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<Hub />} />
        <Route path="/app/images" element={<OptimizeImages />} />
        <Route path="/app/videos" element={<OptimizeVideos />} />
        <Route path="/app/sign" element={<SignImages />} />
        <Route path="/app/smooth" element={<SmoothImages />} />
        <Route path="/security" element={<Security />} />
      </Routes>
      <Analytics />
    </BrowserRouter>
  )
}

export default App
