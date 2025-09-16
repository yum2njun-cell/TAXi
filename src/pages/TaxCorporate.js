import React from 'react'
import { FileText } from 'lucide-react'

function TaxCorporate() {
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <FileText size={32} style={{ color: '#ef4444' }} />
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', color: '#111827', margin: '0' }}>법인세 관리</h1>
      </div>
      <p style={{ fontSize: '18px', color: '#6b7280', marginBottom: '32px' }}>법인세 신고 및 관리 시스템</p>
      
      <div style={{ padding: '24px', backgroundColor: '#fef2f2', borderRadius: '8px', textAlign: 'center' }}>
        <p style={{ fontSize: '16px', color: '#6b7280' }}>법인세 관련 기능을 구현 예정입니다.</p>
      </div>
    </>
  )
}

export default TaxCorporate