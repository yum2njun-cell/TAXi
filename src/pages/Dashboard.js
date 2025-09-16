import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Calendar, FileText, Calculator, BarChart3, MapPin, Stamp, Globe } from 'lucide-react'

function Dashboard() {
  const navigate = useNavigate()

  const getCurrentDate = () => {
    const today = new Date()
    const year = today.getFullYear()
    const month = today.getMonth() + 1
    const date = today.getDate()
    return `${year}년 ${month}월 ${date}일`
  }

  const calculateDaysFromToday = (dateString) => {
    const today = new Date()
    const targetDate = new Date(dateString)
    const diffTime = targetDate - today
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  const taxSchedules = [
    { 
      id: 1,
      title: '법인세 신고',
      category: 'corporate',
      dueDate: '2025-03-31',
      status: 'pending',
      description: '2024년 4분기 법인세 신고'
    },
    { 
      id: 2,
      title: '부가세 신고',
      category: 'vat',
      dueDate: '2025-01-25',
      status: 'pending',
      description: '2024년 12월분 부가세 신고'
    },
    { 
      id: 3,
      title: '원천세 신고',
      category: 'withholding',
      dueDate: '2025-01-10',
      status: 'completed',
      description: '2024년 12월분 원천세 신고'
    }
  ]

  return (
    <>
      {/* 헤더 */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontFamily: 'Pacifico, cursive', fontSize: '32px', fontWeight: 'bold', color: '#1e3a8a', margin: '0 0 8px 0' }}>TAXi</div>
        <p style={{ color: '#6b7280', margin: '0 0 24px 0' }}>세금의 길 위에서, 가장 스마트한 드라이버</p>
        
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', color: '#111827', margin: '0 0 8px 0' }}>{getCurrentDate()}</h1>
        <p style={{ color: '#6b7280', margin: '0' }}>이번 달 신고 일정을 확인하세요</p>
      </div>

      {/* 이번 달 세무일정 */}
      <div style={{ backgroundColor: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', marginBottom: '24px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '16px', margin: '0 0 16px 0' }}>이번 달 세무일정</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {taxSchedules.map((schedule) => {
            const daysFromToday = calculateDaysFromToday(schedule.dueDate)
            let statusText, statusColor, bgColor
            
            if (daysFromToday > 0) {
              statusText = `D-${daysFromToday}`
              statusColor = '#2563eb'
              bgColor = '#dbeafe'
            } else if (daysFromToday === 0) {
              statusText = 'D-day'
              statusColor = '#dc2626'
              bgColor = '#fee2e2'
            } else {
              statusText = `D+${Math.abs(daysFromToday)}`
              statusColor = '#10b981'
              bgColor = '#d1fae5'
            }
            
            return (
              <div key={schedule.id} style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                padding: '16px', 
                border: '1px solid #e5e7eb', 
                borderRadius: '8px' 
              }}>
                <div>
                  <h4 style={{ fontSize: '16px', fontWeight: '500', color: '#111827', margin: '0 0 4px 0' }}>{schedule.title}</h4>
                  <p style={{ fontSize: '14px', color: '#6b7280', margin: '0 0 4px 0' }}>{schedule.description}</p>
                  <p style={{ fontSize: '12px', color: '#9ca3af', margin: '0' }}>마감: {schedule.dueDate}</p>
                </div>
                <div style={{ 
                  padding: '4px 8px', 
                  borderRadius: '12px', 
                  backgroundColor: bgColor,
                  color: statusColor,
                  fontSize: '12px',
                  fontWeight: '500'
                }}>
                  {statusText}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* 세무 Task */}
      <div style={{ backgroundColor: 'white', borderRadius: '12px', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', marginTop: '24px' }}>
        <div style={{ padding: '24px', borderBottom: '1px solid #e5e7eb' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', margin: '0' }}>세무 Task</h3>
        </div>
        
        {/* 세목 선택 버튼들 */}
        <div style={{ padding: '16px 24px', borderBottom: '1px solid #e5e7eb' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { id: 'corporate', name: '법인세', nameEn: 'Corporate Tax', icon: FileText, color: '#ef4444', bgColor: '#fef2f2' },
              { id: 'withholding', name: '원천세', nameEn: 'Withholding Tax', icon: Calculator, color: '#f97316', bgColor: '#fff7ed' },
              { id: 'vat', name: '부가세', nameEn: 'VAT', icon: BarChart3, color: '#eab308', bgColor: '#fefce8' },
              { id: 'local', name: '지방세', nameEn: 'Local Tax', icon: MapPin, color: '#22c55e', bgColor: '#f0fdf4' },
              { id: 'stamp', name: '인지세', nameEn: 'Stamp Tax', icon: Stamp, color: '#06b6d4', bgColor: '#ecfeff' },
              { id: 'international', name: '국제조세', nameEn: 'International Tax', icon: Globe, color: '#8b5cf6', bgColor: '#faf5ff' }
            ].map((category) => (
              <button
                key={category.id}
                onClick={() => navigate(`/tax/${category.id}`)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb',
                  backgroundColor: 'white',
                  color: '#6b7280',
                  cursor: 'pointer',
                  fontSize: '14px',
                  transition: 'all 0.2s'
                }}
              >
                <category.icon size={16} style={{ color: category.color }} />
                <span>{category.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 선택된 세목의 태스크 */}
        <div style={{ padding: '24px' }}>
          <div style={{ textAlign: 'center', padding: '32px', backgroundColor: '#f9fafb', borderRadius: '8px' }}>
            <Calendar size={48} style={{ color: '#2563eb', marginBottom: '16px' }} />
            <h4 style={{ fontSize: '18px', fontWeight: '500', color: '#111827', marginBottom: '8px', margin: '0 0 8px 0' }}>세무 업무 관리</h4>
            <p style={{ color: '#6b7280', margin: '0' }}>원하는 세목을 선택하여 관련 업무를 처리할 수 있습니다.</p>
          </div>
        </div>
      </div>
    </>
  )
}

export default Dashboard