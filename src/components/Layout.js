import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Calendar, FileText, Bell, Settings, Calculator, MapPin, Stamp, Globe, BarChart3, Clock, CheckCircle, AlertTriangle } from 'lucide-react'

function Layout({ children, onLogout }) {
  const navigate = useNavigate()
  const [leftSidebarCollapsed, setLeftSidebarCollapsed] = useState(false)
  const [rightSidebarCollapsed, setRightSidebarCollapsed] = useState(false)

  const taxCategories = [
    { id: 'corporate', name: '법인세', nameEn: 'Corporate Tax', icon: FileText, color: '#ef4444', bgColor: '#fef2f2' },
    { id: 'withholding', name: '원천세', nameEn: 'Withholding Tax', icon: Calculator, color: '#f97316', bgColor: '#fff7ed' },
    { id: 'vat', name: '부가세', nameEn: 'VAT', icon: BarChart3, color: '#eab308', bgColor: '#fefce8' },
    { id: 'local', name: '지방세', nameEn: 'Local Tax', icon: MapPin, color: '#22c55e', bgColor: '#f0fdf4' },
    { id: 'stamp', name: '인지세', nameEn: 'Stamp Tax', icon: Stamp, color: '#06b6d4', bgColor: '#ecfeff' },
    { id: 'international', name: '국제조세', nameEn: 'International Tax', icon: Globe, color: '#8b5cf6', bgColor: '#faf5ff' }
  ]

  const menuItems = [
    { id: 'taxday', name: 'Taxday', icon: Calendar },
    { id: 'taxtory', name: 'Taxtory', icon: FileText },
    { id: 'axtory', name: 'AXtory', icon: BarChart3 },
    { id: 'taxledge', name: 'Taxledge', icon: Settings },
    { id: 'taxrary', name: 'Taxrary', icon: Bell }
  ]

  const externalLinks = [
    { name: '홈택스', url: 'https://www.hometax.go.kr', icon: Globe },
    { name: '위택스', url: 'https://www.wetax.go.kr', icon: MapPin },
    { name: '국세법령정보시스템', url: 'https://taxlaw.nts.go.kr/', icon: FileText }
  ]

  const [selectedTaxCategory, setSelectedTaxCategory] = useState(taxCategories[0])
  const [showTaxDropdown, setShowTaxDropdown] = useState(false)

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
    },
    { 
      id: 4,
      title: '지방세 신고',
      category: 'local',
      dueDate: '2025-01-31',
      status: 'pending',
      description: '2024년 하반기 지방세 신고'
    }
  ]

  const taxManagers = {
    corporate: '김회계',
    vat: '이부가',
    withholding: '박원천',
    local: '최지방',
    stamp: '정인지',
    international: '한국제'
  }

  const calculateDaysFromToday = (dateString) => {
    const today = new Date()
    const targetDate = new Date(dateString)
    const diffTime = targetDate - today
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  const handleLogout = () => {
    if (onLogout) {
      onLogout()
    }
    navigate('/login')
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb', display: 'flex' }}>
      {/* 왼쪽 사이드바 */}
      <div style={{ 
        width: leftSidebarCollapsed ? '40px' : '320px', 
        backgroundColor: 'white', 
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', 
        borderRight: '1px solid #e5e7eb',
        transition: 'width 0.3s ease'
      }}>
        {/* 헤더 */}
        <div style={{ padding: '24px', borderBottom: '1px solid #e5e7eb' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: leftSidebarCollapsed ? 'center' : 'space-between' }}>
            {!leftSidebarCollapsed && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div 
                  onClick={() => navigate('/dashboard')}
                  style={{ 
                    fontFamily: 'Pacifico, cursive', 
                    fontSize: '24px', 
                    fontWeight: 'bold', 
                    color: '#1e3a8a',
                    cursor: 'pointer',
                    transition: 'color 0.2s ease'
                  }}
                  onMouseEnter={(e) => e.target.style.color = '#2563eb'}
                  onMouseLeave={(e) => e.target.style.color = '#1e3a8a'}
                >
                  TAXi
                </div>
                <button
                    onClick={handleLogout}
                    style={{
                    backgroundColor: 'white',
                    color: '#6b7280',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    border: '1px solid #d1d5db',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: '500'
                    }}
                >
                    로그아웃
                </button>
                </div>
            )}
            <button
                onClick={() => setLeftSidebarCollapsed(!leftSidebarCollapsed)}
                style={{
                backgroundColor: 'white',
                color: '#6b7280',
                padding: '6px',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                cursor: 'pointer',
                fontSize: '14px'
                }}
            >
                {leftSidebarCollapsed ? '>' : '<'}
            </button>
          </div>
        </div>

        {/* 메뉴 */}
        {!leftSidebarCollapsed && (
          <div style={{ padding: '16px' }}>
            {/* 세목 선택 드롭다운 */}
            <div style={{ marginBottom: '24px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: '500', color: '#6b7280', marginBottom: '12px', margin: '0 0 12px 0' }}>세목 선택</h3>
              <div style={{ position: 'relative' }}>
                <button
                  onClick={() => setShowTaxDropdown(!showTaxDropdown)}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '12px',
                    padding: '12px 16px',
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    backgroundColor: 'white',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ padding: '4px', borderRadius: '4px', backgroundColor: selectedTaxCategory.bgColor }}>
                      <selectedTaxCategory.icon size={16} style={{ color: selectedTaxCategory.color }} />
                    </div>
                    <div style={{ textAlign: 'left' }}>
                      <div style={{ fontWeight: '500', color: '#111827' }}>{selectedTaxCategory.name}</div>
                      <div style={{ fontSize: '12px', color: '#6b7280' }}>{selectedTaxCategory.nameEn}</div>
                    </div>
                  </div>
                  <div style={{ transform: showTaxDropdown ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>▼</div>
                </button>
                
                {showTaxDropdown && (
                  <div style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    right: 0,
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    zIndex: 10,
                    marginTop: '4px'
                  }}>
                    {taxCategories.map((category) => (
                      <button
                        key={category.id}
                        onClick={() => {
                          setSelectedTaxCategory(category)
                          setShowTaxDropdown(false)
                          navigate(`/tax/${category.id}`) // 이 줄 추가
                        }}
                        style={{
                          width: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          padding: '12px 16px',
                          border: 'none',
                          backgroundColor: selectedTaxCategory.id === category.id ? category.bgColor : 'transparent',
                          color: selectedTaxCategory.id === category.id ? category.color : '#6b7280',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          borderRadius: '6px',
                          margin: '2px'
                        }}
                      >
                        <div style={{ padding: '4px', borderRadius: '4px', backgroundColor: category.bgColor }}>
                          <category.icon size={16} style={{ color: category.color }} />
                        </div>
                        <div style={{ textAlign: 'left' }}>
                          <div style={{ fontWeight: '500' }}>{category.name}</div>
                          <div style={{ fontSize: '12px', opacity: 0.7 }}>{category.nameEn}</div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* 메뉴 항목 */}
            <div style={{ marginBottom: '24px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: '500', color: '#6b7280', marginBottom: '12px', margin: '0 0 12px 0' }}>메뉴</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {menuItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => navigate(`/${item.id}`)}
                    style={{
                      width: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px 16px',
                      borderRadius: '8px',
                      border: 'none',
                      backgroundColor: 'transparent',
                      color: '#6b7280',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                  >
                    <item.icon size={20} />
                    <span style={{ fontWeight: '500' }}>{item.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* 기타 항목 */}
            <div>
              <h3 style={{ fontSize: '14px', fontWeight: '500', color: '#6b7280', marginBottom: '12px', margin: '0 0 12px 0' }}>기타</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {externalLinks.map((link, index) => (
                  <button
                    key={index}
                    onClick={() => window.open(link.url, '_blank')}
                    style={{
                      width: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px 16px',
                      borderRadius: '8px',
                      border: 'none',
                      backgroundColor: 'transparent',
                      color: '#6b7280',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                  >
                    <link.icon size={20} />
                    <span style={{ fontWeight: '500' }}>{link.name}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 메인 컨텐츠 */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <div style={{ display: 'flex', height: '100vh' }}>
          {/* 가운데 메인 영역 - children으로 받음 */}
          <div style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
            {children}
          </div>

          {/* 오른쪽 사이드바 */}
          <div style={{ 
            width: rightSidebarCollapsed ? '40px' : '320px', 
            backgroundColor: 'white', 
            borderLeft: '1px solid #e5e7eb', 
            padding: rightSidebarCollapsed ? '12px' : '24px', 
            overflowY: 'auto',
            transition: 'width 0.3s ease'
          }}>
            {/* 토글 버튼 */}
            <div style={{ marginBottom: '24px', textAlign: 'left' }}>
              <button
                onClick={() => setRightSidebarCollapsed(!rightSidebarCollapsed)}
                style={{
                  backgroundColor: 'white',
                  color: '#6b7280',
                  padding: '6px',
                  borderRadius: '6px',
                  border: '1px solid #d1d5db',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                {rightSidebarCollapsed ? '<' : '>'}
              </button>
            </div>

            {/* 알림 및 최근 처리내역 - 접혔을 때 숨김 */}
            {!rightSidebarCollapsed && (
              <>
                {/* 알림 섹션 */}
                <div style={{ marginBottom: '32px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                    <h3 style={{ fontWeight: '600', color: '#111827', margin: '0' }}>알림</h3>
                    <Bell style={{ color: '#9ca3af' }} size={20} />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    
                    {/* 첫 번째 알림 */}
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px', borderRadius: '8px', backgroundColor: '#f9fafb' }}>
                      <div style={{ padding: '4px', borderRadius: '50%', backgroundColor: '#dbeafe' }}>
                        <Clock style={{ color: '#2563eb' }} size={12} />
                      </div>
                      <div style={{ flex: 1 }}>
                        <p style={{ fontSize: '14px', fontWeight: '500', color: '#111827', margin: '0 0 4px 0' }}>담당자별 이번 주 일정</p>
                        {(() => {
                          const weeklySchedules = taxSchedules.filter(schedule => {
                            const days = calculateDaysFromToday(schedule.dueDate)
                            return days >= 0 && days <= 7
                          })
                          
                          if (weeklySchedules.length === 0) {
                            return <p style={{ fontSize: '12px', color: '#6b7280', margin: '0' }}>오늘의 일정은 없습니다.</p>
                          }
                          
                          return weeklySchedules.map(schedule => (
                            <p key={schedule.id} style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 2px 0' }}>
                              {taxManagers[schedule.category]}: {schedule.title} (D-{calculateDaysFromToday(schedule.dueDate)})
                            </p>
                          ))
                        })()}
                        <p style={{ fontSize: '12px', color: '#9ca3af', margin: '4px 0 0 0' }}>방금 전</p>
                      </div>
                    </div>

                    {/* 두 번째 알림: 가장 급한 일정 */}
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px', borderRadius: '8px', backgroundColor: '#f9fafb' }}>
                      <div style={{ padding: '4px', borderRadius: '50%', backgroundColor: '#fef3c7' }}>
                        <AlertTriangle style={{ color: '#d97706' }} size={12} />
                      </div>
                      <div style={{ flex: 1 }}>
                        <p style={{ fontSize: '14px', fontWeight: '500', color: '#111827', margin: '0 0 4px 0' }}>긴급 일정 알림</p>
                        {(() => {
                          const upcomingSchedule = taxSchedules
                            .filter(schedule => calculateDaysFromToday(schedule.dueDate) >= 0)
                            .sort((a, b) => calculateDaysFromToday(a.dueDate) - calculateDaysFromToday(b.dueDate))[0]
                          
                          if (upcomingSchedule) {
                            const daysLeft = calculateDaysFromToday(upcomingSchedule.dueDate)
                            return (
                              <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 4px 0' }}>
                                {upcomingSchedule.title}이 {daysLeft === 0 ? '오늘' : `${daysLeft}일 후`} 마감입니다.
                              </p>
                            )
                          } else {
                            return <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 4px 0' }}>예정된 급한 일정이 없습니다.</p>
                          }
                        })()}
                        <p style={{ fontSize: '12px', color: '#9ca3af', margin: '0' }}>1시간 전</p>
                      </div>
                    </div>

                    {/* 세 번째 알림 */}
                    {(() => {
                      const recentPastSchedule = taxSchedules
                        .filter(schedule => calculateDaysFromToday(schedule.dueDate) < 0)
                        .sort((a, b) => calculateDaysFromToday(b.dueDate) - calculateDaysFromToday(a.dueDate))[0]
                      
                      if (recentPastSchedule) {
                        const daysPast = Math.abs(calculateDaysFromToday(recentPastSchedule.dueDate))
                        return (
                          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px', borderRadius: '8px', backgroundColor: '#f9fafb' }}>
                            <div style={{ padding: '4px', borderRadius: '50%', backgroundColor: '#d1fae5' }}>
                              <CheckCircle style={{ color: '#10b981' }} size={12} />
                            </div>
                            <div style={{ flex: 1 }}>
                              <p style={{ fontSize: '14px', fontWeight: '500', color: '#111827', margin: '0 0 4px 0' }}>최근 완료</p>
                              <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 4px 0' }}>
                                {recentPastSchedule.title}이 {daysPast}일 전에 완료되었습니다.
                              </p>
                              <p style={{ fontSize: '12px', color: '#9ca3af', margin: '0' }}>{daysPast}일 전</p>
                            </div>
                          </div>
                        )
                      }
                      return null
                    })()}
                  </div>
                </div>

                {/* 최근 처리내역 */}
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                    <h3 style={{ fontWeight: '600', color: '#111827', margin: '0' }}>최근 처리내역</h3>
                    <button style={{ color: '#2563eb', fontSize: '14px', background: 'none', border: 'none', cursor: 'pointer' }}>더보기</button>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {[
                      { 
                        id: 1,
                        title: '부가세 계산서 처리', 
                        page: '/taxtory',
                        amount: '처리 건수: 15건', 
                        date: '2025.01.15 14:30',
                        status: 'completed'
                      },
                      { 
                        id: 2,
                        title: '원천세 신고서 작성', 
                        page: '/taxday',
                        amount: '신고금액: 850,000원', 
                        date: '2025.01.14 16:45',
                        status: 'completed'
                      },
                      { 
                        id: 3,
                        title: '법인세 자료 분석', 
                        page: '/axtory',
                        amount: '분석 완료: 12월 데이터', 
                        date: '2025.01.13 11:20',
                        status: 'completed'
                      }
                    ].map((activity) => (
                      <button
                        key={activity.id}
                        onClick={() => navigate(activity.page)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '12px',
                          borderRadius: '8px',
                          border: '1px solid #f3f4f6',
                          backgroundColor: 'white',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          textAlign: 'left'
                        }}
                      >
                        <div style={{ flex: 1 }}>
                          <p style={{ fontSize: '14px', fontWeight: '500', color: '#111827', margin: '0 0 4px 0' }}>{activity.title}</p>
                          <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 4px 0' }}>{activity.amount}</p>
                          <p style={{ fontSize: '12px', color: '#9ca3af', margin: '0' }}>{activity.date}</p>
                        </div>
                        <div style={{
                          padding: '4px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          backgroundColor: '#d1fae5',
                          color: '#047857'
                        }}>
                          완료
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Layout