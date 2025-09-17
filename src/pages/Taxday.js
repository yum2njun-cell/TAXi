import React, { useState, useEffect } from 'react';
import { Calendar, ChevronLeft, ChevronRight, Search, Trash2, Home } from 'lucide-react';

const Taxday = () => {
  const [currentDate] = useState(new Date());
  const [viewDate, setViewDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(null);
  const [events, setEvents] = useState({});
  const [showAddEvent, setShowAddEvent] = useState(false);
  const [newEvent, setNewEvent] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearch, setShowSearch] = useState(false);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth());

  // 한국 공휴일 계산
  const getKoreanHolidays = (year) => {
    const holidays = [];
    
    // 고정 공휴일
    holidays.push(new Date(year, 0, 1)); // 신정
    holidays.push(new Date(year, 2, 1)); // 삼일절
    holidays.push(new Date(year, 4, 5)); // 어린이날
    holidays.push(new Date(year, 5, 6)); // 현충일
    holidays.push(new Date(year, 7, 15)); // 광복절
    holidays.push(new Date(year, 9, 3)); // 개천절
    holidays.push(new Date(year, 9, 9)); // 한글날
    holidays.push(new Date(year, 11, 25)); // 성탄절
    
    // 음력 공휴일 (간단한 근사치 - 실제로는 더 정확한 계산 필요)
    const lunarHolidays = {
      2021: [
        new Date(2021, 1, 11), new Date(2021, 1, 12), new Date(2021, 1, 13), // 설날
        new Date(2021, 4, 19), // 석가탄신일
        new Date(2021, 8, 20), new Date(2021, 8, 21), new Date(2021, 8, 22) // 추석
      ],
      2022: [
        new Date(2022, 1, 1), new Date(2022, 1, 2), new Date(2022, 1, 3), // 설날
        new Date(2022, 4, 8), // 석가탄신일
        new Date(2022, 8, 9), new Date(2022, 8, 10), new Date(2022, 8, 11) // 추석
      ],
      2023: [
        new Date(2023, 0, 21), new Date(2023, 0, 22), new Date(2023, 0, 23), // 설날
        new Date(2023, 4, 27), // 석가탄신일
        new Date(2023, 8, 28), new Date(2023, 8, 29), new Date(2023, 8, 30) // 추석
      ],
      2024: [
        new Date(2024, 1, 9), new Date(2024, 1, 10), new Date(2024, 1, 11), // 설날
        new Date(2024, 4, 15), // 석가탄신일
        new Date(2024, 8, 16), new Date(2024, 8, 17), new Date(2024, 8, 18) // 추석
      ],
      2025: [
        new Date(2025, 0, 28), new Date(2025, 0, 29), new Date(2025, 0, 30), // 설날
        new Date(2025, 4, 5), // 석가탄신일
        new Date(2025, 9, 5), new Date(2025, 9, 6), new Date(2025, 9, 7) // 추석
      ],
      2026: [
        new Date(2026, 1, 16), new Date(2026, 1, 17), new Date(2026, 1, 18), // 설날
        new Date(2026, 4, 24), // 석가탄신일
        new Date(2026, 8, 25), new Date(2026, 8, 26), new Date(2026, 8, 27) // 추석
      ],
      2027: [
        new Date(2027, 1, 6), new Date(2027, 1, 7), new Date(2027, 1, 8), // 설날
        new Date(2027, 4, 13), // 석가탄신일
        new Date(2027, 9, 14), new Date(2027, 9, 15), new Date(2027, 9, 16) // 추석
      ]
    };
    
    if (lunarHolidays[year]) {
      holidays.push(...lunarHolidays[year]);
    }
    
    return holidays;
  };

  // 컴포넌트 초기화
  useEffect(() => {
    // 영업일 계산 (주말, 공휴일 제외)
    const getNextBusinessDay = (date) => {
      const holidays = getKoreanHolidays(date.getFullYear());
      let nextDay = new Date(date);
      
      while (true) {
        const dayOfWeek = nextDay.getDay();
        const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
        const isHoliday = holidays.some(holiday => 
          holiday.getTime() === nextDay.getTime()
        );
        
        if (!isWeekend && !isHoliday) {
          break;
        }
        
        nextDay.setDate(nextDay.getDate() + 1);
      }
      
      return nextDay;
    };

    // 기본 세무 일정 생성
    const generateDefaultEvents = () => {
      const defaultEvents = {};
      const years = [2021, 2022, 2023, 2024, 2025, 2026, 2027];
      
      years.forEach(year => {
        // 연간 고정 일정
        const yearlyEvents = [
          { date: new Date(year, 2, 31), title: '법인세', isTax: true },
          { date: new Date(year, 3, 30), title: '법인세 지방소득세분', isTax: true },
          { date: new Date(year, 7, 31), title: '법인세 중간예납', isTax: true },
          { date: new Date(year, 3, 25), title: '1기 예정 부가가치세', isTax: true },
          { date: new Date(year, 6, 25), title: '1기 확정 부가가치세', isTax: true },
          { date: new Date(year, 9, 25), title: '2기 예정 부가가치세', isTax: true },
          { date: new Date(year + 1, 0, 25), title: '2기 확정 부가가치세', isTax: true },
          { date: new Date(year, 6, 31), title: '주민세 사업소분', isTax: true },
          { date: new Date(year, 6, 31), title: '건축물, 주택1기분 재산세', isTax: true },
          { date: new Date(year, 8, 30), title: '토지, 주택2기분 재산세', isTax: true },
          { date: new Date(year, 11, 15), title: '1차분납 종합부동산세', isTax: true },
          { date: new Date(year, 5, 15), title: '2차분납 종합부동산세', isTax: true },
          { date: new Date(year, 7, 31), title: '상반기 증권거래세', isTax: true },
          { date: new Date(year + 1, 1, 28), title: '하반기 증권거래세', isTax: true },
          { date: new Date(year, 11, 31), title: '이전가격보고서', isTax: true },
          { date: new Date(year, 5, 30), title: '해외계좌신고', isTax: true },
          { date: new Date(year, 0, 31), title: '근로소득 간이지급명세서', isTax: true },
          { date: new Date(year, 6, 31), title: '근로소득 간이지급명세서', isTax: true },
          { date: new Date(year + 1, 1, 28), title: '기타소득, 국내원천득, 배당소득 지급명세서', isTax: true },
          { date: new Date(year + 1, 1, 28), title: '우리사주인출 및 과세명세서우리사주배당비과세 원천징수세액환급명세서', isTax: true },
          { date: new Date(year + 1, 2, 10), title: '사업소득, 근로소득, 퇴직소득 지급명세서', isTax: true },
          { date: new Date(year, 5, 30), title: '일감몰아주기 증여세', isTax: true }
        ];
        
        // 월별 반복 일정
        for (let month = 0; month < 12; month++) {
          const lastDay = new Date(year, month + 1, 0).getDate();
          
          // 매월 10일
          yearlyEvents.push(
            { date: new Date(year, month, 10), title: '원천징수 이행상황신고', isTax: true },
            { date: new Date(year, month, 10), title: '지방소득세(특별징수분)', isTax: true },
            { date: new Date(year, month, 10), title: '주민세 종업원분', isTax: true }
          );
          
          // 매월 말일
          yearlyEvents.push(
            { date: new Date(year, month, lastDay), title: '사업소득, 기타소득 간이지급명세서', isTax: true },
            { date: new Date(year, month, lastDay), title: '일용근로소득 지급명세서', isTax: true }
          );
        }
        
        // 이벤트 처리 및 영업일 계산
        yearlyEvents.forEach(event => {
          let actualDate = event.date;
          let isExtended = false;
          
          if (event.isTax) {
            const businessDay = getNextBusinessDay(event.date);
            if (businessDay.getTime() !== event.date.getTime()) {
              actualDate = businessDay;
              isExtended = true;
            }
          }
          
          const dateKey = `${actualDate.getFullYear()}-${actualDate.getMonth()}-${actualDate.getDate()}`;
          
          if (!defaultEvents[dateKey]) {
            defaultEvents[dateKey] = [];
          }
          
          const eventTitle = isExtended 
            ? `${event.title} (${actualDate.getMonth() + 1}월 ${actualDate.getDate()}일로 연장됨)`
            : event.title;
            
          defaultEvents[dateKey].push({
            id: Date.now() + Math.random(),
            title: eventTitle,
            isDefault: true,
            originalDate: event.date,
            actualDate: actualDate,
            isExtended: isExtended
          });
        });
      });
      
      return defaultEvents;
    };

    const savedEvents = localStorage.getItem('taxday-events');
    if (savedEvents) {
      setEvents(JSON.parse(savedEvents));
    } else {
      const defaultEvents = generateDefaultEvents();
      setEvents(defaultEvents);
      localStorage.setItem('taxday-events', JSON.stringify(defaultEvents));
    }
  }, []); // 빈 배열로 의존성 설정

  // 이벤트 저장
  const saveEvents = (newEvents) => {
    setEvents(newEvents);
    localStorage.setItem('taxday-events', JSON.stringify(newEvents));
  };

  // 달력 생성
  const generateCalendar = () => {
    const year = viewDate.getFullYear();
    const month = viewDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startDate = firstDay.getDay();
    
    const calendar = [];
    
    // 이전 달 날짜들
    for (let i = 0; i < startDate; i++) {
      calendar.push(null);
    }
    
    // 현재 달 날짜들
    for (let day = 1; day <= daysInMonth; day++) {
      calendar.push(day);
    }
    
    return calendar;
  };

  // 날짜별 이벤트 가져오기
  const getEventsForDate = (day) => {
    if (!day) return [];
    const dateKey = `${viewDate.getFullYear()}-${viewDate.getMonth()}-${day}`;
    return events[dateKey] || [];
  };

  // 이벤트 추가
  const addEvent = () => {
    if (!selectedDate || !newEvent.trim()) return;
    
    const dateKey = `${selectedDate.getFullYear()}-${selectedDate.getMonth()}-${selectedDate.getDate()}`;
    const newEvents = { ...events };
    
    if (!newEvents[dateKey]) {
      newEvents[dateKey] = [];
    }
    
    newEvents[dateKey].push({
      id: Date.now(),
      title: newEvent,
      isDefault: false
    });
    
    saveEvents(newEvents);
    setNewEvent('');
    setShowAddEvent(false);
  };

  // 이벤트 삭제
  const deleteEvent = (dateKey, eventId) => {
    const newEvents = { ...events };
    newEvents[dateKey] = newEvents[dateKey].filter(event => event.id !== eventId);
    
    if (newEvents[dateKey].length === 0) {
      delete newEvents[dateKey];
    }
    
    saveEvents(newEvents);
  };

  // 검색 기능
  const searchEvents = () => {
    if (!searchTerm.trim()) {
      setSearchResults([]);
      return;
    }
    
    const results = [];
    Object.entries(events).forEach(([dateKey, eventList]) => {
      eventList.forEach(event => {
        if (event.title.toLowerCase().includes(searchTerm.toLowerCase())) {
          const [year, month, day] = dateKey.split('-').map(Number);
          results.push({
            date: new Date(year, month, day),
            event: event,
            dateKey: dateKey
          });
        }
      });
    });
    
    results.sort((a, b) => a.date - b.date);
    setSearchResults(results);
  };

  // 연월 이동
  const goToDate = () => {
    setViewDate(new Date(selectedYear, selectedMonth, 1));
  };

  // 오늘로 이동
  const goToToday = () => {
    setViewDate(new Date());
  };

  const calendar = generateCalendar();
  const monthNames = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];
  const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      {/* 헤더 */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '20px',
        backgroundColor: 'white',
        color: '#1e3a8a',
        padding: '15px',
        borderRadius: '10px'
      }}>
        <h1 style={{ 
          margin: 0, 
          fontSize: '24px', 
          fontWeight: 'bold',
          fontFamily: 'Pacifico, cursive'
        }}>
          <Calendar style={{ display: 'inline', marginRight: '10px' }} />
          TAXDAY
        </h1>
        
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            onClick={goToToday}
            style={{
              padding: '8px 12px',
              backgroundColor: 'white',
              color: '#1e3a8a',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            <Home size={16} style={{ marginRight: '5px' }} />
            오늘
          </button>
          
          <button
            onClick={() => setShowSearch(!showSearch)}
            style={{
              padding: '8px 12px',
              backgroundColor: 'white',
              color: '#1e3a8a',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            <Search size={16} />
          </button>
        </div>
      </div>

      {/* 검색 및 날짜 이동 패널 */}
      {showSearch && (
        <div style={{
          backgroundColor: '#f8fafc',
          padding: '20px',
          borderRadius: '10px',
          marginBottom: '20px',
          border: '1px solid #e2e8f0'
        }}>
          <div style={{ display: 'flex', gap: '20px', alignItems: 'center', flexWrap: 'wrap' }}>
            {/* 검색 */}
            <div style={{ flex: 1, minWidth: '200px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                이벤트 검색
              </label>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="키워드를 입력하세요"
                  style={{
                    flex: 1,
                    padding: '8px',
                    border: '1px solid #d1d5db',
                    borderRadius: '5px'
                  }}
                />
                <button
                  onClick={searchEvents}
                  style={{
                    padding: '8px 15px',
                    backgroundColor: 'white',
                    color: '#1e3a8a',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer'
                  }}
                >
                  검색
                </button>
              </div>
            </div>
            
            {/* 날짜 이동 */}
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <label style={{ fontWeight: 'bold' }}>날짜 이동:</label>
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                style={{ padding: '5px', border: '1px solid #d1d5db', borderRadius: '5px' }}
              >
                {[2021, 2022, 2023, 2024, 2025, 2026, 2027].map(year => (
                  <option key={year} value={year}>{year}년</option>
                ))}
              </select>
              
              <select
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                style={{ padding: '5px', border: '1px solid #d1d5db', borderRadius: '5px' }}
              >
                {monthNames.map((month, index) => (
                  <option key={index} value={index}>{month}</option>
                ))}
              </select>
              
              <button
                onClick={goToDate}
                style={{
                  padding: '5px 10px',
                  backgroundColor: 'white',
                  color: '#1e3a8a',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer'
                }}
              >
                이동
              </button>
            </div>
          </div>
          
          {/* 검색 결과 */}
          {searchResults.length > 0 && (
            <div style={{ marginTop: '15px' }}>
              <h4>검색 결과:</h4>
              <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                {searchResults.map((result, index) => (
                  <div
                    key={index}
                    style={{
                      padding: '8px',
                      backgroundColor: 'white',
                      margin: '5px 0',
                      borderRadius: '5px',
                      border: '1px solid #e2e8f0',
                      cursor: 'pointer'
                    }}
                    onClick={() => {
                      setViewDate(new Date(result.date));
                      setShowSearch(false);
                    }}
                  >
                    <strong>{result.date.getFullYear()}년 {result.date.getMonth() + 1}월 {result.date.getDate()}일</strong>
                    <br />
                    {result.event.title}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 달력 네비게이션 */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '20px' 
      }}>
        <button
          onClick={() => setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() - 1))}
          style={{
            padding: '10px',
            backgroundColor: '#f3f4f6',
            border: '1px solid #d1d5db',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          <ChevronLeft size={20} />
        </button>
        
        <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 'bold' }}>
          {viewDate.getFullYear()}년 {monthNames[viewDate.getMonth()]}
        </h2>
        
        <button
          onClick={() => setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() + 1))}
          style={{
            padding: '10px',
            backgroundColor: '#f3f4f6',
            border: '1px solid #d1d5db',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          <ChevronRight size={20} />
        </button>
      </div>

      {/* 달력 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(7, 1fr)',
        gap: '1px',
        backgroundColor: '#e5e7eb',
        border: '1px solid #e5e7eb',
        borderRadius: '10px',
        overflow: 'hidden'
      }}>
        {/* 요일 헤더 */}
        {weekDays.map((day, index) => (
          <div
            key={day}
            style={{
              padding: '15px',
              backgroundColor: '#1e3a8a',
              color: 'white',
              textAlign: 'center',
              fontWeight: 'bold',
              fontSize: '14px'
            }}
          >
            {day}
          </div>
        ))}
        
        {/* 달력 날짜들 */}
        {calendar.map((day, index) => {
          const dayEvents = getEventsForDate(day);
          const isToday = day && 
            viewDate.getFullYear() === currentDate.getFullYear() &&
            viewDate.getMonth() === currentDate.getMonth() &&
            day === currentDate.getDate();
          
          return (
            <div
              key={index}
              style={{
                minHeight: '120px',
                backgroundColor: day ? 'white' : '#f9fafb',
                padding: '8px',
                cursor: day ? 'pointer' : 'default',
                border: isToday ? '2px solid #3b82f6' : 'none',
                position: 'relative'
              }}
              onClick={() => {
                if (day) {
                  setSelectedDate(new Date(viewDate.getFullYear(), viewDate.getMonth(), day));
                  setShowAddEvent(true);
                }
              }}
            >
              {day && (
                <>
                  <div style={{ 
                    fontWeight: 'bold', 
                    marginBottom: '5px',
                    color: isToday ? '#3b82f6' : '#374151'
                  }}>
                    {day}
                  </div>
                  
                  {/* 이벤트들 */}
                  {dayEvents.slice(0, 3).map((event, eventIndex) => (
                    <div
                      key={event.id}
                      style={{
                        fontSize: '10px',
                        padding: '2px 4px',
                        backgroundColor: event.isDefault ? '#fef3c7' : '#dbeafe',
                        color: event.isDefault ? '#92400e' : '#1e40af',
                        borderRadius: '3px',
                        marginBottom: '2px',
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        const dateKey = `${viewDate.getFullYear()}-${viewDate.getMonth()}-${day}`;
                        deleteEvent(dateKey, event.id);
                      }}
                    >
                      <span style={{ flexGrow: 1 }}>{event.title}</span>
                      <Trash2 size={12} style={{ marginLeft: '4px' }} />
                    </div>
                  ))}
                  
                  {dayEvents.length > 3 && (
                    <div style={{
                      fontSize: '10px',
                      color: '#6b7280',
                      textAlign: 'center',
                      marginTop: '2px'
                    }}>
                      +{dayEvents.length - 3}개 더
                    </div>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>

      {/* 이벤트 추가 모달 */}
      {showAddEvent && selectedDate && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '10px',
            minWidth: '400px'
          }}>
            <h3>
              {selectedDate.getFullYear()}년 {selectedDate.getMonth() + 1}월 {selectedDate.getDate()}일 일정 추가
            </h3>
            
            <input
              type="text"
              value={newEvent}
              onChange={(e) => setNewEvent(e.target.value)}
              placeholder="일정을 입력하세요"
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #d1d5db',
                borderRadius: '5px',
                marginBottom: '15px'
              }}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  addEvent();
                }
              }}
            />
            
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => {
                  setShowAddEvent(false);
                  setNewEvent('');
                }}
                style={{
                  padding: '8px 15px',
                  backgroundColor: '#6b7280',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer'
                }}
              >
                취소
              </button>
              
              <button
                onClick={addEvent}
                style={{
                  padding: '8px 15px',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer'
                }}
              >
                추가
              </button>
            </div>
            
            {/* 해당 날짜의 기존 이벤트들 표시 */}
            <div style={{ marginTop: '20px' }}>
              <h4>기존 일정:</h4>
              {getEventsForDate(selectedDate.getDate()).map((event) => (
                <div
                  key={event.id}
                  style={{
                    padding: '8px',
                    backgroundColor: event.isDefault ? '#fef3c7' : '#dbeafe',
                    color: event.isDefault ? '#92400e' : '#1e40af',
                    borderRadius: '5px',
                    marginBottom: '5px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <span>{event.title}</span>
                  <div style={{ display: 'flex', gap: '5px' }}>
                    {event.isDefault && (
                      <span style={{
                        fontSize: '10px',
                        backgroundColor: '#f59e0b',
                        color: 'white',
                        padding: '2px 6px',
                        borderRadius: '10px'
                      }}>
                        기본일정
                      </span>
                    )}
                    <button
                      onClick={() => {
                        const dateKey = `${selectedDate.getFullYear()}-${selectedDate.getMonth()}-${selectedDate.getDate()}`;
                        deleteEvent(dateKey, event.id);
                      }}
                      style={{
                        backgroundColor: '#ef4444',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        padding: '4px 8px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      삭제
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 범례 */}
      <div style={{
        marginTop: '20px',
        padding: '15px',
        backgroundColor: '#f8fafc',
        borderRadius: '10px',
        border: '1px solid #e2e8f0'
      }}>
        <h4 style={{ margin: '0 0 10px 0' }}>범례 및 안내</h4>
        <div style={{ marginBottom: '10px' }}>
          <p style={{ margin: '0 0 5px 0', fontSize: '14px', color: '#374151' }}>
            💡 <strong>기본 일정 수정 안내:</strong> 세법 개정이나 특별한 상황으로 기본 신고 기한이 변경된 경우, 
            기본 일정도 수정/삭제가 가능합니다.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '20px',
              height: '15px',
              backgroundColor: '#fef3c7',
              borderRadius: '3px',
              border: '1px solid #f59e0b'
            }}></div>
            <span style={{ fontSize: '14px' }}>기본 세무 일정 (수정/삭제 가능)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '20px',
              height: '15px',
              backgroundColor: '#dbeafe',
              borderRadius: '3px',
              border: '1px solid #3b82f6'
            }}></div>
            <span style={{ fontSize: '14px' }}>개인 일정</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '20px',
              height: '15px',
              border: '2px solid #3b82f6',
              borderRadius: '3px'
            }}></div>
            <span style={{ fontSize: '14px' }}>오늘</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Taxday;