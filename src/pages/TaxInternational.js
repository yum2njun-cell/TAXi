import React from 'react'
import { Globe } from 'lucide-react'

function TaxInternational() {
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <Globe size={32} style={{ color: '#8b5cf6' }} />
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', color: '#111827', margin: '0' }}>국제조세 관리</h1>
      </div>
      <p style={{ fontSize: '18px', color: '#6b7280', marginBottom: '32px' }}>국제조세 신고 및 관리 시스템</p>
      
      <div style={{ padding: '24px', backgroundColor: '#faf5ff', borderRadius: '8px', textAlign: 'center' }}>
        <p style={{ fontSize: '16px', color: '#6b7280' }}>국제조세 관련 기능을 구현 예정입니다.</p>
      </div>
    </>
  )
}

export default TaxInternational