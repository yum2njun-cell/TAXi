import React from 'react'
import { FileText } from 'lucide-react'

function Taxtory() {
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <FileText size={32} style={{ color: '#2563eb' }} />
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', color: '#111827', margin: '0' }}>Taxtory</h1>
      </div>
      <p style={{ fontSize: '18px', color: '#6b7280', marginBottom: '32px' }}>SK 납부 실적</p>
      
      <div style={{ padding: '24px', backgroundColor: '#f9fafb', borderRadius: '8px', textAlign: 'center' }}>
        <p style={{ fontSize: '16px', color: '#6b7280' }}>Taxtory 기능을 구현 예정입니다.</p>
      </div>
    </>
  )
}

export default Taxtory