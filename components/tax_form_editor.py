"""
세금 데이터 수동 수정 컴포넌트
자동 추출된 데이터를 수정할 수 있는 폼
"""

import streamlit as st
from typing import Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)


def show_tax_editor(record: Dict[str, Any], 
                   on_save: Callable[[str, Dict[str, Any]], bool],
                   key_prefix: str = "") -> bool:
    """
    세금 데이터 수정 폼
    
    Args:
        record: 수정할 기록
        on_save: 저장 콜백 함수 (record_id, updated_data) -> bool
        key_prefix: 위젯 키 접두사
        
    Returns:
        저장 성공 여부
    """
    
    record_id = record.get('id', '')
    
    with st.expander("✏️ 데이터 수정", expanded=False):
        st.markdown("##### 세액 정보 수정")
        st.caption("자동 추출된 값이 정확하지 않은 경우 수정할 수 있습니다.")
        
        # 현재 값 표시
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📋 현재 값**")
            st.info(f"""
            - 원천세: {record.get('withholding_tax', 0):,.0f}원
            - 지방소득세: {record.get('local_income_tax', 0):,.0f}원
            - 주민세(종업원분): {record.get('resident_tax', 0):,.0f}원
            - **합계: {record.get('total_amount', 0):,.0f}원**
            """)
        
        with col2:
            st.markdown("**✏️ 수정**")
            
            # 수정 폼
            with st.form(key=f"{key_prefix}_edit_form_{record_id}"):
                withholding_tax = st.number_input(
                    "원천세 (원)",
                    min_value=0,
                    value=int(record.get('withholding_tax', 0)),
                    step=1000,
                    format="%d",
                    key=f"{key_prefix}_wt_{record_id}"
                )
                
                local_income_tax = st.number_input(
                    "지방소득세(특별징수분) (원)",
                    min_value=0,
                    value=int(record.get('local_income_tax', 0)),
                    step=1000,
                    format="%d",
                    key=f"{key_prefix}_lit_{record_id}"
                )
                
                resident_tax = st.number_input(
                    "주민세(종업원분) (원)",
                    min_value=0,
                    value=int(record.get('resident_tax', 0)),
                    step=1000,
                    format="%d",
                    key=f"{key_prefix}_rt_{record_id}"
                )
                
                # 합계 미리보기
                new_total = withholding_tax + local_income_tax + resident_tax
                st.markdown(f"**새 합계: {new_total:,.0f}원**")
                
                # 변경 사항 확인
                has_changes = (
                    withholding_tax != record.get('withholding_tax', 0) or
                    local_income_tax != record.get('local_income_tax', 0) or
                    resident_tax != record.get('resident_tax', 0)
                )
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    submit = st.form_submit_button(
                        "💾 저장",
                        type="primary",
                        disabled=not has_changes,
                        use_container_width=True
                    )
                
                with col_btn2:
                    cancel = st.form_submit_button(
                        "취소",
                        use_container_width=True
                    )
                
                if submit and has_changes:
                    # 수정된 데이터
                    updated_data = {
                        'withholding_tax': float(withholding_tax),
                        'local_income_tax': float(local_income_tax),
                        'resident_tax': float(resident_tax),
                        'total_amount': float(new_total)
                    }
                    
                    # 저장 콜백 호출
                    success = on_save(record_id, updated_data)
                    
                    if success:
                        st.success("✅ 수정사항이 저장되었습니다!")
                        logger.info(f"기록 수정 완료: {record_id}")
                        return True
                    else:
                        st.error("❌ 저장에 실패했습니다.")
                        return False
                
                if cancel:
                    st.info("수정을 취소했습니다.")
                    return False
        
        # 처리 오류 표시
        if record.get('processing_errors'):
            st.warning("⚠️ 파일 처리 중 발생한 경고:")
            for error in record['processing_errors']:
                st.caption(f"- {error}")
    
    return False


def show_inline_tax_editor(record: Dict[str, Any], 
                           on_save: Callable[[str, Dict[str, Any]], bool],
                           key_prefix: str = "") -> bool:
    """
    인라인 세금 데이터 수정 (간단 버전)
    
    Args:
        record: 수정할 기록
        on_save: 저장 콜백 함수
        key_prefix: 위젯 키 접두사
        
    Returns:
        저장 성공 여부
    """
    
    record_id = record.get('id', '')
    
    st.markdown("##### 세액 정보")
    
    col1, col2, col3, col4 = st.columns([3, 3, 3, 1])
    
    with col1:
        withholding_tax = st.number_input(
            "원천세",
            min_value=0,
            value=int(record.get('withholding_tax', 0)),
            step=1000,
            format="%d",
            key=f"{key_prefix}_inline_wt_{record_id}"
        )
    
    with col2:
        local_income_tax = st.number_input(
            "지방소득세",
            min_value=0,
            value=int(record.get('local_income_tax', 0)),
            step=1000,
            format="%d",
            key=f"{key_prefix}_inline_lit_{record_id}"
        )
    
    with col3:
        resident_tax = st.number_input(
            "주민세",
            min_value=0,
            value=int(record.get('resident_tax', 0)),
            step=1000,
            format="%d",
            key=f"{key_prefix}_inline_rt_{record_id}"
        )
    
    with col4:
        st.markdown("&nbsp;")  # 공간 조정
        save_btn = st.button("💾", key=f"{key_prefix}_inline_save_{record_id}", 
                            help="변경사항 저장")
    
    # 합계 표시
    new_total = withholding_tax + local_income_tax + resident_tax
    st.markdown(f"**합계: {new_total:,.0f}원**")
    
    if save_btn:
        # 변경 사항 확인
        has_changes = (
            withholding_tax != record.get('withholding_tax', 0) or
            local_income_tax != record.get('local_income_tax', 0) or
            resident_tax != record.get('resident_tax', 0)
        )
        
        if has_changes:
            updated_data = {
                'withholding_tax': float(withholding_tax),
                'local_income_tax': float(local_income_tax),
                'resident_tax': float(resident_tax),
                'total_amount': float(new_total)
            }
            
            success = on_save(record_id, updated_data)
            
            if success:
                st.success("✅ 저장 완료!")
                return True
            else:
                st.error("❌ 저장 실패")
                return False
        else:
            st.info("변경사항이 없습니다.")
    
    return False


def show_batch_editor(records: list, 
                     on_save_all: Callable[[list], bool],
                     key_prefix: str = "batch") -> bool:
    """
    여러 기록을 한번에 수정하는 배치 에디터
    
    Args:
        records: 수정할 기록 리스트
        on_save_all: 전체 저장 콜백 함수
        key_prefix: 위젯 키 접두사
        
    Returns:
        저장 성공 여부
    """
    
    if not records:
        st.info("수정할 데이터가 없습니다.")
        return False
    
    st.markdown("### 📝 일괄 수정")
    st.caption(f"총 {len(records)}개의 기록을 수정합니다.")
    
    with st.form(key=f"{key_prefix}_batch_form"):
        edited_records = []
        
        for i, record in enumerate(records):
            st.markdown(f"#### {record['year']}년 {record['month']}월")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                wt = st.number_input(
                    "원천세",
                    min_value=0,
                    value=int(record.get('withholding_tax', 0)),
                    step=1000,
                    key=f"{key_prefix}_batch_wt_{i}"
                )
            
            with col2:
                lit = st.number_input(
                    "지방소득세",
                    min_value=0,
                    value=int(record.get('local_income_tax', 0)),
                    step=1000,
                    key=f"{key_prefix}_batch_lit_{i}"
                )
            
            with col3:
                rt = st.number_input(
                    "주민세",
                    min_value=0,
                    value=int(record.get('resident_tax', 0)),
                    step=1000,
                    key=f"{key_prefix}_batch_rt_{i}"
                )
            
            total = wt + lit + rt
            st.caption(f"합계: {total:,.0f}원")
            
            edited_record = record.copy()
            edited_record['withholding_tax'] = float(wt)
            edited_record['local_income_tax'] = float(lit)
            edited_record['resident_tax'] = float(rt)
            edited_record['total_amount'] = float(total)
            
            edited_records.append(edited_record)
            
            if i < len(records) - 1:
                st.divider()
        
        st.markdown("---")
        
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            submit = st.form_submit_button(
                "💾 전체 저장",
                type="primary",
                use_container_width=True
            )
        
        with col_cancel:
            cancel = st.form_submit_button(
                "취소",
                use_container_width=True
            )
        
        if submit:
            success = on_save_all(edited_records)
            
            if success:
                st.success(f"✅ {len(edited_records)}개의 기록이 저장되었습니다!")
                return True
            else:
                st.error("❌ 저장에 실패했습니다.")
                return False
        
        if cancel:
            st.info("일괄 수정을 취소했습니다.")
            return False
    
    return False
