import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'

function Login(props) {
  const navigate = useNavigate()
  const [employeeId, setEmployeeId] = useState('')  
  const [password, setPassword] = useState('')     

  const handleLogin = async (e) => {
    e.preventDefault()
    console.log('로그인 시도 - 사번:', employeeId)
    props.onLogin()
    navigate('/dashboard')
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #dbeafe 0%, #c7d2fe 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px'
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '40px',
        borderRadius: '16px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        width: '100%',
        maxWidth: '400px'
      }}>
        {/* 로고 */}
        <div style={{ textAlign: 'center', marginBottom: '8px' }}>
          <h1 style={{ 
            fontFamily: 'Pacifico, cursive', 
            fontSize: '50px',
            color: '#1e3a8a',
            margin: '0 0 12px 0'
          }}>
            TAXi
          </h1>
        </div>
        
        {/* 슬로건 */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <p style={{ 
            fontSize: '18px',
            color: '#374151',
            margin: '0'
          }}>
            세금의 길 위에서, 가장 스마트한 드라이버
          </p>
        </div>

        {/* 로그인 폼 */}
        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{ 
              display: 'block',
              color: '#374151',
              fontSize: '14px',
              fontWeight: '600',
              marginBottom: '8px'
            }}>
              사번
            </label>
            <input
              type="text"
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              placeholder="사번을 입력하세요"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                outline: 'none',
                fontSize: '16px',
                boxSizing: 'border-box'
              }}
              required
            />
          </div>
          
          <div style={{ marginBottom: '24px' }}>
            <label style={{ 
              display: 'block',
              color: '#374151',
              fontSize: '14px',
              fontWeight: '600',
              marginBottom: '8px'
            }}>
              비밀번호
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="비밀번호를 입력하세요"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                outline: 'none',
                fontSize: '16px',
                boxSizing: 'border-box'
              }}
              required
            />
          </div>
          
          <button
            type="submit"
            style={{
              width: '100%',
              backgroundColor: '#2563eb',
              color: 'white',
              padding: '12px 16px',
              borderRadius: '8px',
              border: 'none',
              fontSize: '18px',
              fontWeight: '500',
              cursor: 'pointer'
            }}
          >
            로그인
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login