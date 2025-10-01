"""
메뉴 구성 설정 파일
서브메뉴 추가 시 이 파일만 수정하면 됩니다.
"""

def get_menu_config():
    """메뉴 구성 반환"""
    return {
        "TAXiverse": {
            "TAXday": {
                "page": "pages/TAXday.py"
            },
            "TAXtory": {
                "page": "pages/taxiverse/02_TAXtory.py"
            },
            "TAXrary": {
                "page": "pages/taxiverse/04_TAXrary.py"
            },
            "TAXledge": {
                "page": "pages/taxiverse/05_TAXledge.py"
            },
            "TAXtok": {
                "page": "pages/TAXtok.py"
            },
        },
        "TAXk": {
            "법인세": {
                "boxed": True, 
                "submenu": {
                    "업무용승용차 관리": {
                        "page": "pages/corp_workingcar.py"
                    }
                }
            },
            "부가세": {
                "boxed": True, 
                "submenu": {
                    "외화획득명세서": {
                        "page": "pages/foreign_currency.py"
                    },
                    "법인카드 공제 확인": {
                        "page": "pages/card_deduction.py"
                    }
                }
            },
            "원천세": {
                "boxed": True, 
                "submenu": {
                    "이행상황신고서": {
                        "page": "pages/withholding_salary.py"
                    }
                }
            },
            "지방세": {
                "boxed": True, 
                "submenu": {
                    "재산세": {
                        "page": "pages/local_tax_property.py"
                    }
                }
            },
            "인지세": {
                "boxed": True, 
                "submenu": {
                    "인지세 관리": {
                        "page": "pages/stamp_management.py"
                    },
                }
            },
            "국제조세": {
                "boxed": True, 
                "submenu": {
                    "조세조약": {
                        "page": "pages/treaty_search.py"
                    }
                }
            }
        }
    }
    

# 서브메뉴 쉽게 추가하는 헬퍼 함수들
def add_submenu_item(tax_type: str, submenu_name: str, submenu_config: dict):
    """특정 세목에 서브메뉴 추가"""
    menu_config = get_menu_config()
    if tax_type in menu_config["TAXk"]:
        if "submenu" not in menu_config["TAXk"][tax_type]:
            menu_config["TAXk"][tax_type]["submenu"] = {}
        menu_config["TAXk"][tax_type]["submenu"][submenu_name] = submenu_config
    return menu_config

def add_taxiverse_item(item_name: str, item_config: dict):
    """TAXiverse에 새로운 기능 추가"""
    menu_config = get_menu_config()
    menu_config["TAXiverse"][item_name] = item_config
    return menu_config

# 사용 예시:
# 법인세에 새로운 서브메뉴 "특별세액공제" 추가
# add_submenu_item("법인세", "특별세액공제", {
