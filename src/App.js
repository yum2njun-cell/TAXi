import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Taxday from './pages/Taxday'
import Taxtory from './pages/Taxtory'
import AXtory from './pages/AXtory'
import Taxledge from './pages/Taxledge'
import Taxrary from './pages/Taxrary'
import TaxCorporate from './pages/TaxCorporate'
import TaxWithholding from './pages/TaxWithholding'
import TaxVat from './pages/TaxVat'
import TaxLocal from './pages/TaxLocal'
import TaxStamp from './pages/TaxStamp'
import TaxInternational from './pages/TaxInternational'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  useEffect(() => {
    const savedLoginState = localStorage.getItem('isLoggedIn')
    if (savedLoginState === 'true') {
      setIsLoggedIn(true)
    }
  }, [])

  const handleLogin = () => {
    setIsLoggedIn(true)
    localStorage.setItem('isLoggedIn', 'true')
  }

  const handleLogout = () => {
    setIsLoggedIn(false)
    localStorage.removeItem('isLoggedIn')
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          {/* 기본 경로 */}
          <Route 
            path="/" 
            element={isLoggedIn ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />} 
          />
          
          {/* 로그인 페이지 (레이아웃 없음) */}
          <Route 
            path="/login" 
            element={
              isLoggedIn ? 
                <Navigate to="/dashboard" replace /> : 
                <Login onLogin={handleLogin} />
            } 
          />
          
          {/* 레이아웃이 필요한 모든 페이지들 */}
          <Route 
            path="/dashboard" 
            element={
              isLoggedIn ? 
                <Layout onLogout={handleLogout}>
                  <Dashboard />
                </Layout> : 
                <Navigate to="/login" replace />
            } 
          />
          
          <Route 
            path="/taxday" 
            element={
              isLoggedIn ? 
                <Layout onLogout={handleLogout}>
                  <Taxday />
                </Layout> : 
                <Navigate to="/login" replace />
            } 
          />
          
          <Route 
            path="/taxtory" 
            element={
              isLoggedIn ? 
                <Layout onLogout={handleLogout}>
                  <Taxtory />
                </Layout> : 
                <Navigate to="/login" replace />
            } 
          />
          
          <Route 
            path="/axtory" 
            element={
              isLoggedIn ? 
                <Layout onLogout={handleLogout}>
                  <AXtory />
                </Layout> : 
                <Navigate to="/login" replace />
            } 
          />
          
          <Route 
            path="/taxledge" 
            element={
              isLoggedIn ? 
                <Layout onLogout={handleLogout}>
                  <Taxledge />
                </Layout> : 
                <Navigate to="/login" replace />
            } 
          />
          
          <Route 
            path="/taxrary" 
            element={
              isLoggedIn ? 
                <Layout onLogout={handleLogout}>
                  <Taxrary />
                </Layout> : 
                <Navigate to="/login" replace />
            } 
          />

          {/* 세목별 페이지들 */}
          <Route 
            path="/tax/corporate" 
            element={
              isLoggedIn ? 
                <Layout onLogout={handleLogout}>
                  <TaxCorporate />
                </Layout> : 
                <Navigate to="/login" replace />
            } 
          />
          <Route 
            path="/tax/withholding" 
            element={
              isLoggedIn ? 
                <Layout onLogout={handleLogout}>
                  <TaxWithholding />
                </Layout> : 
                <Navigate to="/login" replace />
            } 
          />
          <Route 
            path="/tax/vat" 
            element={
              isLoggedIn ? 
                <Layout onLogout={handleLogout}>
                  <TaxVat />
                </Layout> : 
                <Navigate to="/login" replace />
            } 
          />
          <Route 
            path="/tax/local" 
            element={
              isLoggedIn ? 
                <Layout onLogout={handleLogout}>
                  <TaxLocal />
                </Layout> : 
                <Navigate to="/login" replace />
            } 
          />
          <Route 
            path="/tax/stamp" 
            element={
              isLoggedIn ? 
                <Layout onLogout={handleLogout}>
                  <TaxStamp />
                </Layout> : 
                <Navigate to="/login" replace />
            } 
          />
          <Route 
            path="/tax/international" 
            element={
              isLoggedIn ? 
                <Layout onLogout={handleLogout}>
                  <TaxInternational />
                </Layout> : 
                <Navigate to="/login" replace />
            } 
          />
          {/* 404 페이지 */}
          <Route 
            path="*" 
            element={<Navigate to="/" replace />} 
          />
        </Routes>
      </div>
    </Router>
  )
}

export default App