import React from 'react'
import { Calculator } from 'lucide-react'

function TaxWithholding() {
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <Calculator size={32} style={{ color: '#f97316' }} />
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', color: '#111827', margin: '0' }}>원천세 관리</h1>
      </div>
      <p style={{ fontSize: '18px', color: '#6b7280', marginBottom: '32px' }}>원천세 신고 및 관리 시스템</p>
      
      <div style={{ padding: '24px', backgroundColor: '#fff7ed', borderRadius: '8px', textAlign: 'center' }}>
        <p style={{ fontSize: '16px', color: '#6b7280' }}>원천세 관련 기능을 구현 예정입니다.</p>
      </div>
    </>
  )
}

export default TaxWithholding