import React from 'react'
import { Settings } from 'lucide-react'

function Taxledge() {
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <Settings size={32} style={{ color: '#2563eb' }} />
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', color: '#111827', margin: '0' }}>Taxledge</h1>
      </div>
      <p style={{ fontSize: '18px', color: '#6b7280', marginBottom: '32px' }}>세무 지식 창고</p>
      
      <div style={{ padding: '24px', backgroundColor: '#f9fafb', borderRadius: '8px', textAlign: 'center' }}>
        <p style={{ fontSize: '16px', color: '#6b7280' }}>Taxledge 기능을 구현 예정입니다.</p>
      </div>
    </>
  )
}

export default Taxledge