import React from 'react'
import { Calendar } from 'lucide-react'

function Taxday() {
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <Calendar size={32} style={{ color: '#2563eb' }} />
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', color: '#111827', margin: '0' }}>Taxday</h1>
      </div>
      <p style={{ fontSize: '18px', color: '#6b7280', marginBottom: '32px' }}>세무 일정 관리 시스템</p>
      
      <div style={{ padding: '24px', backgroundColor: '#f9fafb', borderRadius: '8px', textAlign: 'center' }}>
        <p style={{ fontSize: '16px', color: '#6b7280' }}>Taxday 기능을 구현 예정입니다.</p>
      </div>
    </>
  )
}

export default Taxday