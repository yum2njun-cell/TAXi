import React from 'react'
import { BarChart3 } from 'lucide-react'

function AXtory() {
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <BarChart3 size={32} style={{ color: '#2563eb' }} />
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', color: '#111827', margin: '0' }}>Axtory</h1>
      </div>
      <p style={{ fontSize: '18px', color: '#6b7280', marginBottom: '32px' }}>AX 납부 실적</p>
      
      <div style={{ padding: '24px', backgroundColor: '#f9fafb', borderRadius: '8px', textAlign: 'center' }}>
        <p style={{ fontSize: '16px', color: '#6b7280' }}>AXtory 기능을 구현 예정입니다.</p>
      </div>
    </>
  )
}

export default AXtory