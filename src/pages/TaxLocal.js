import React from 'react'
import { MapPin } from 'lucide-react'

function TaxLocal() {
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <MapPin size={32} style={{ color: '#22c55e' }} />
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', color: '#111827', margin: '0' }}>지방세 관리</h1>
      </div>
      <p style={{ fontSize: '18px', color: '#6b7280', marginBottom: '32px' }}>지방세 신고 및 관리 시스템</p>
      
      <div style={{ padding: '24px', backgroundColor: '#f0fdf4', borderRadius: '8px', textAlign: 'center' }}>
        <p style={{ fontSize: '16px', color: '#6b7280' }}>지방세 관련 기능을 구현 예정입니다.</p>
      </div>
    </>
  )
}

export default TaxLocal