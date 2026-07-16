import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import Hub from './pages/Hub'
import OptimizeImages from './pages/OptimizeImages'
import OptimizeVideos from './pages/OptimizeVideos'
import SignImages from './pages/SignImages'
import SmoothImages from './pages/SmoothImages'
import Security from './pages/Security'
import Login from './pages/Login'
import Register from './pages/Register'
import Account from './pages/Account'
import RequireStaff from './components/RequireStaff'
import AdminLayout from './pages/admin/AdminLayout'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminUsers from './pages/admin/AdminUsers'
import AdminUserForm from './pages/admin/AdminUserForm'
import AdminJobs from './pages/admin/AdminJobs'
import { AuthProvider } from './context/AuthContext'
import { captureAttribution } from './utils/attribution'

import { Analytics } from '@vercel/analytics/react'

// L'espace admin a sa propre barre (AdminLayout) : pas de nav publique
// (marketing, CTA optimiseur...) à l'intérieur de /admin.
function PublicNavbar() {
  const location = useLocation()
  if (location.pathname.startsWith('/admin')) return null
  return <Navbar />
}

function App() {
  useEffect(() => {
    captureAttribution()
  }, [])

  return (
    <AuthProvider>
      <BrowserRouter>
        <PublicNavbar />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/app" element={<Hub />} />
          <Route path="/app/images" element={<OptimizeImages />} />
          <Route path="/app/videos" element={<OptimizeVideos />} />
          <Route path="/app/sign" element={<SignImages />} />
          <Route path="/app/smooth" element={<SmoothImages />} />
          <Route path="/security" element={<Security />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/account" element={<Account />} />

          <Route path="/admin" element={<RequireStaff><AdminLayout /></RequireStaff>}>
            <Route index element={<AdminDashboard />} />
            <Route path="users" element={<AdminUsers />} />
            <Route path="users/new" element={<AdminUserForm />} />
            <Route path="users/:id" element={<AdminUserForm />} />
            <Route path="jobs" element={<AdminJobs />} />
          </Route>
        </Routes>
        <Analytics />
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
