import React, { useState, useRef } from 'react';
import { Upload, Download, Calculator, AlertCircle, CheckCircle, Trash2, Car, Building2, Receipt, FileText, TrendingUp } from 'lucide-react';
import * as XLSX from 'xlsx';  

const TaxCorporate = () => {
  const [activeSubmenu, setActiveSubmenu] = useState('vehicle'); // 기본값: 업무용승용차 관리
  const [vehicleData, setVehicleData] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const fileInputRef = useRef(null);

  // 법인세 서브메뉴 목록
  const submenus = [
    { id: 'vehicle', name: '업무용승용차 관리', icon: Car },
    { id: 'depreciation', name: '감가상각 관리', icon: TrendingUp },
    { id: 'expense', name: '손금처리 관리', icon: Receipt },
    { id: 'report', name: '법인세 신고서', icon: FileText },
    { id: 'calculation', name: '세액계산', icon: Calculator }
  ];

  // D11에서 "아" 뒤 4자리 숫자 추출
  const extractCarNumber = (d11Value) => {
      if (!d11Value) return '';
      
      const str = d11Value.toString();
      console.log('D11 원본 값:', str); // 디버깅용
      
      // "아" 뒤 4자리 숫자 패턴 매칭 (더 유연하게)
      const patterns = [
          /아(\d{4})/,           // "아1000" 형태
          /[가-힣]+(\d{4})/,     // 한글+4자리숫자 형태
          /(\d{4})$/             // 마지막 4자리 숫자
      ];
      
      for (const pattern of patterns) {
          const match = str.match(pattern);
          if (match) {
              console.log('추출된 차량번호 뒤4자리:', match[1]); // 디버깅용
              return match[1];
          }
      }
      
      return '';
  };


  // J10 날짜를 기준으로 해당 연도 월수 계산
  const calculateMonths = (dateValue) => {
      if (!dateValue) return '';
      
      const dateStr = dateValue.toString().trim();
      console.log('J10 원본 날짜 값:', dateStr); // 디버깅용
      
      let year = null, month = null;
      
      // 엑셀 시리얼 날짜 형식 처리 (43834 같은 숫자)
      if (/^\d+$/.test(dateStr) && parseInt(dateStr) > 1000) {
          // 엑셀 시리얼 날짜를 JavaScript Date로 변환
          const excelDate = parseInt(dateStr);
          // 엑셀 기준일: 1900년 1월 1일 (하지만 엑셀은 1900년을 윤년으로 잘못 계산하므로 -2)
          const jsDate = new Date((excelDate - 25569) * 86400 * 1000);
          
          year = jsDate.getFullYear();
          month = jsDate.getMonth() + 1; // getMonth()는 0부터 시작
          
          console.log(`엑셀 시리얼 날짜 ${excelDate} → ${year}.${month.toString().padStart(2, '0')}.${jsDate.getDate().toString().padStart(2, '0')}`);
          
      } else if (dateStr.length === 8 && /^\d{8}$/.test(dateStr)) {
          // YYYYMMDD 형태 (예: 20240210)
          year = parseInt(dateStr.substring(0, 4));
          month = parseInt(dateStr.substring(4, 6));
      } else if (dateStr.includes('-')) {
          // YYYY-MM-DD 형태
          const parts = dateStr.split('-');
          if (parts.length >= 2) {
              year = parseInt(parts[0]);
              month = parseInt(parts[1]);
          }
      } else if (dateStr.includes('/')) {
          // YYYY/MM/DD 또는 MM/DD/YYYY 형태
          const parts = dateStr.split('/');
          if (parts.length >= 2) {
              if (parts[0].length === 4) {
                  // YYYY/MM/DD
                  year = parseInt(parts[0]);
                  month = parseInt(parts[1]);
              } else {
                  // MM/DD/YYYY
                  year = parseInt(parts[2]);
                  month = parseInt(parts[0]);
              }
          }
      } else if (dateStr.includes('.')) {
          // YYYY.MM.DD 형태
          const parts = dateStr.split('.');
          if (parts.length >= 2) {
              year = parseInt(parts[0]);
              month = parseInt(parts[1]);
          }
      } else {
          console.log('인식되지 않은 날짜 형식:', dateStr);
          return '';
      }
      
      // 유효성 검사
      if (!year || !month || month < 1 || month > 12) {
          console.log('잘못된 날짜 값 - year:', year, 'month:', month);
          return '';
      }
      
      // 현재 연도 가져오기
      const currentYear = new Date().getFullYear();
      
      // 해당 월부터 12월까지의 개월수 계산
      let months;
      if (year === currentYear) {
          months = 12 - month + 1; // 해당 월부터 12월까지
      } else if (year < currentYear) {
          // 이전 년도면 전체 년도
          months = 12;
      } else {
          // 미래 년도면 0
          months = 0;
      }
      
      console.log(`날짜 파싱 결과 - 년도: ${year}, 월: ${month}, 계산된 월수: ${months}`);
      return months;
  };

  // 엑셀 파일에서 특정 셀 값 추출
  const extractCellValue = (worksheet, cellAddress) => {
    const cell = worksheet[cellAddress];
    return cell ? (cell.v || '') : '';
  };

  // 엑셀 파일 처리
  const processExcelFile = async (file) => {
      return new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = (e) => {
              try {
                  const data = new Uint8Array(e.target.result);
                  const workbook = XLSX.read(data, { type: 'array' });
                  const firstSheetName = workbook.SheetNames[0];
                  const worksheet = workbook.Sheets[firstSheetName];

                  // 필요한 셀 값들 추출
                  const a11 = extractCellValue(worksheet, 'A11');
                  const d11 = extractCellValue(worksheet, 'D11');
                  const j8 = extractCellValue(worksheet, 'J8');
                  const j10 = extractCellValue(worksheet, 'J10');
                  const n9 = extractCellValue(worksheet, 'N9');
                  const n11 = extractCellValue(worksheet, 'N11');
                  const n13 = extractCellValue(worksheet, 'N13');

                  // 날짜 포맷팅 함수 (여기에 정의!)
                  const formatExcelDate = (dateValue) => {
                      if (!dateValue) return '';
                      
                      const dateStr = dateValue.toString().trim();
                      
                      // 엑셀 시리얼 날짜 형식 처리
                      if (/^\d+$/.test(dateStr) && parseInt(dateStr) > 1000) {
                          const excelDate = parseInt(dateStr);
                          const jsDate = new Date((excelDate - 25569) * 86400 * 1000);
                          
                          const year = jsDate.getFullYear();
                          const month = (jsDate.getMonth() + 1).toString().padStart(2, '0');
                          const day = jsDate.getDate().toString().padStart(2, '0');
                          
                          return `${year}.${month}.${day}`;
                      }
                      
                      // 다른 형식은 그대로 반환
                      return dateStr;
                  };

                  const extractedData = {
                      fileName: file.name,
                      carNumberLast4: extractCarNumber(d11),
                      carNumber: d11,
                      carType: a11,
                      user: j8,
                      recordExists: '여',
                      startDate: formatExcelDate(j10), // ← 이제 함수 사용 가능
                      months: calculateMonths(j10),
                      totalDistance: n9,
                      businessDistance: n11,
                      businessRatio: n13
                  };

                  resolve(extractedData);
              } catch (error) {
                  reject(error);
              }
          };
          reader.onerror = () => reject(new Error('파일 읽기 실패'));
          reader.readAsArrayBuffer(file);
      });
  };

  // 다중 파일 업로드 처리
  const handleMultipleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setIsProcessing(true);
    setError('');
    setSuccess('');

    const processedData = [];
    const fileNames = [];

    try {
      for (const file of files) {
        // 파일 형식 검증
        if (!file.name.match(/\.(xlsx|xls)$/i)) {
          throw new Error(`${file.name}: 엑셀 파일만 업로드 가능합니다.`);
        }

        const data = await processExcelFile(file);
        processedData.push(data);
        fileNames.push(file.name);
      }

      setVehicleData(processedData);
      setUploadedFiles(fileNames);
      setSuccess(`${files.length}개 파일에서 데이터를 성공적으로 추출했습니다.`);

    } catch (err) {
      setError(`파일 처리 중 오류: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  // 결과를 엑셀로 다운로드
  const downloadExcel = () => {
    if (vehicleData.length === 0) {
      setError('다운로드할 데이터가 없습니다.');
      return;
    }

    // 테이블 헤더
    const headers = [
      '차량번호(뒤4자리)',
      '차량번호',
      '차종명',
      '사용자',
      '운행기록부 작성여부',
      '임차기간 시작일',
      '해당연도 보유 또는 임차기간월수',
      '총주행거리(km) 기말 계기판',
      '업무용 사용거리(km)',
      '업무사용비율'
    ];

    // 데이터 변환
    const excelData = [
      headers,
      ...vehicleData.map(item => [
        item.carNumberLast4,
        item.carNumber,
        item.carType,
        item.user,
        item.recordExists,
        item.startDate,
        item.months,
        item.totalDistance,
        item.businessDistance,
        item.businessRatio
      ])
    ];

    const ws = XLSX.utils.aoa_to_sheet(excelData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "업무용승용차관리");
    
    const today = new Date().toISOString().slice(0, 10);
    XLSX.writeFile(wb, `업무용승용차관리_${today}.xlsx`);
  };

  // 데이터 초기화
  const clearData = () => {
    setVehicleData([]);
    setUploadedFiles([]);
    setError('');
    setSuccess('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 서브메뉴 렌더링
  const renderSubmenuContent = () => {
    switch (activeSubmenu) {
      case 'vehicle':
        return (
          <div className="space-y-6">
            {/* 파일 업로드 섹션 */}
            <div style={{
              backgroundColor: '#f8fafc',
              padding: '24px',
              borderRadius: '8px',
              border: '2px dashed #fef2f2'
            }}>
              <div className="text-center">
                <Upload size={48} style={{ color: '#ef4444', margin: '0 auto 16px' }} />
                <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
                  업무용승용차 엑셀 파일 업로드
                </h3>
                <p style={{ color: '#fef2f2', marginBottom: '16px' }}>
                  여러 개의 엑셀 파일을 한 번에 선택하여 업로드하세요
                </p>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleMultipleFileUpload}
                  accept=".xlsx,.xls"
                  multiple
                  style={{ display: 'none' }}
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isProcessing}
                  style={{
                    backgroundColor: '#ef4444',
                    color: 'white',
                    padding: '12px 24px',
                    borderRadius: '6px',
                    border: 'none',
                    cursor: isProcessing ? 'not-allowed' : 'pointer',
                    opacity: isProcessing ? 0.6 : 1
                  }}
                >
                  {isProcessing ? '처리중...' : '파일 선택'}
                </button>
              </div>
            </div>

            {/* 상태 메시지 */}
            {error && (
              <div style={{
                backgroundColor: '#fee2e2',
                color: '#dc2626',
                padding: '12px',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <AlertCircle size={20} />
                {error}
              </div>
            )}

            {success && (
              <div style={{
                backgroundColor: '#dcfce7',
                color: '#16a34a',
                padding: '12px',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <CheckCircle size={20} />
                {success}
              </div>
            )}

            {/* 업로드된 파일 목록 */}
            {uploadedFiles.length > 0 && (
              <div style={{
                backgroundColor: '#f1f5f9',
                padding: '16px',
                borderRadius: '6px'
              }}>
                <h4 style={{ fontWeight: '600', marginBottom: '8px' }}>
                  업로드된 파일 ({uploadedFiles.length}개)
                </h4>
                <div style={{ fontSize: '14px', color: '#64748b' }}>
                  {uploadedFiles.slice(0, 5).map((fileName, index) => (
                    <div key={index}>• {fileName}</div>
                  ))}
                  {uploadedFiles.length > 5 && (
                    <div>... 외 {uploadedFiles.length - 5}개</div>
                  )}
                </div>
              </div>
            )}

            {/* 액션 버튼 */}
            {vehicleData.length > 0 && (
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                <button
                  onClick={downloadExcel}
                  style={{
                    backgroundColor: 'white',
                    color: '#1e3a8a',
                    padding: '10px 20px',
                    borderRadius: '6px',
                    border: '#059669',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  <Download size={16} />
                  엑셀 다운로드
                </button>
                <button
                  onClick={clearData}
                  style={{
                    backgroundColor: 'white',
                    color: '#1e3a8a',
                    padding: '10px 20px',
                    borderRadius: '6px',
                    border: '#dc2626',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  <Trash2 size={16} />
                  데이터 초기화
                </button>
              </div>
            )}

            {/* 데이터 테이블 */}
            {vehicleData.length > 0 && (
              <div style={{
                backgroundColor: 'white',
                borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                overflow: 'hidden'
              }}>
                <div style={{
                  backgroundColor: '#ef4444',
                  color: 'white',
                  padding: '16px',
                  fontWeight: '600'
                }}>
                  추출된 데이터 ({vehicleData.length}건)
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead style={{ backgroundColor: '#f8fafc' }}>
                      <tr>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontSize: '14px' }}>차량번호(뒤4자리)</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontSize: '14px' }}>차량번호</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontSize: '14px' }}>차종명</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontSize: '14px' }}>사용자</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontSize: '14px' }}>운행기록부</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontSize: '14px' }}>시작일</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontSize: '14px' }}>월수</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontSize: '14px' }}>총주행거리</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontSize: '14px' }}>업무거리</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontSize: '14px' }}>업무비율</th>
                      </tr>
                    </thead>
                    <tbody>
                      {vehicleData.map((item, index) => (
                        <tr key={index} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '12px', fontSize: '14px' }}>{item.carNumberLast4}</td>
                          <td style={{ padding: '12px', fontSize: '14px' }}>{item.carNumber}</td>
                          <td style={{ padding: '12px', fontSize: '14px' }}>{item.carType}</td>
                          <td style={{ padding: '12px', fontSize: '14px' }}>{item.user}</td>
                          <td style={{ padding: '12px', fontSize: '14px' }}>{item.recordExists}</td>
                          <td style={{ padding: '12px', fontSize: '14px' }}>{item.startDate}</td>
                          <td style={{ padding: '12px', fontSize: '14px' }}>{item.months}</td>
                          <td style={{ padding: '12px', fontSize: '14px' }}>{item.totalDistance}</td>
                          <td style={{ padding: '12px', fontSize: '14px' }}>{item.businessDistance}</td>
                          <td style={{ padding: '12px', fontSize: '14px' }}>{item.businessRatio}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        );

      case 'depreciation':
        return (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: '#64748b' }}>
            <TrendingUp size={48} style={{ margin: '0 auto 16px' }} />
            <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>감가상각 관리</h3>
            <p>감가상각 관리 기능이 곧 추가될 예정입니다.</p>
          </div>
        );

      case 'expense':
        return (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: '#64748b' }}>
            <Receipt size={48} style={{ margin: '0 auto 16px' }} />
            <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>손금처리 관리</h3>
            <p>손금처리 관리 기능이 곧 추가될 예정입니다.</p>
          </div>
        );

      case 'report':
        return (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: '#64748b' }}>
            <FileText size={48} style={{ margin: '0 auto 16px' }} />
            <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>법인세 신고서</h3>
            <p>법인세 신고서 관리 기능이 곧 추가될 예정입니다.</p>
          </div>
        );

      case 'calculation':
        return (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: '#64748b' }}>
            <Calculator size={48} style={{ margin: '0 auto 16px' }} />
            <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>세액계산</h3>
            <p>세액계산 기능이 곧 추가될 예정입니다.</p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* 페이지 헤더 */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <Building2 size={28} style={{ color: '#ef4444' }} />
          <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#ef4444', margin: 0 }}>
            법인세 관리
          </h1>
        </div>
        <p style={{ color: '#64748b', margin: 0 }}>
          법인세 관련 업무를 효율적으로 관리하세요
        </p>
      </div>

      {/* 서브메뉴 탭 */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{
          display: 'flex',
          borderBottom: '2px solid #fef2f2',
          overflowX: 'auto'
        }}>
          {submenus.map((menu) => {
            const Icon = menu.icon;
            return (
              <button
                key={menu.id}
                onClick={() => setActiveSubmenu(menu.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 24px',
                  border: 'none',
                  backgroundColor: 'transparent',
                  cursor: 'pointer',
                  borderBottom: activeSubmenu === menu.id ? '2px solid #ef4444' : '2px solid transparent',
                  color: activeSubmenu === menu.id ? '#ef4444' : '#64748b',
                  fontWeight: activeSubmenu === menu.id ? '600' : '400',
                  whiteSpace: 'nowrap'
                }}
              >
                <Icon size={16} />
                {menu.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* 서브메뉴 콘텐츠 */}
      {renderSubmenuContent()}
    </div>
  );
};

export default TaxCorporate;