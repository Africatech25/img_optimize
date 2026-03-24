import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import Optimizer from './pages/Optimizer'
import Security from './pages/Security'

import { Analytics } from '@vercel/analytics/react'

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<Optimizer />} />
        <Route path="/security" element={<Security />} />
      </Routes>
      <Analytics />
    </BrowserRouter>
  )
}

export default App
