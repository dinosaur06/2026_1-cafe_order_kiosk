from __future__ import annotations

from datetime import datetime, timezone

import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cafe_order_kiosk.models import Order


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_money(amount: int) -> str:
    return f"{amount:,}원"

# 문자열이 터미널에서 차지하는 실제 칸 수를 계산 (한글 2칸, 영문/숫자 1칸)
def get_display_width(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in s)

# 한글/영문 너비를 고려하여 지정한 전체 너비에 맞게 우측에 공백을 채우기
def pad_right_multibyte(s: str, width: int) -> str:
    cur_w = get_display_width(s)
    return s + " " * max(0, width - cur_w)

# 영수증 생성 함수 추가
def generate_receipt(order: Order) -> str:
    lines = []
    lines.append("=" * 48)
    lines.append(f"{'☕ 영 수 증 (RECEIPT)':^41}")
    lines.append("=" * 48)
    lines.append(f" 주문 번호 : {order.id}")
    
    time_info = order.paid_at if order.paid_at else order.created_at
    lines.append(f" 결제 일시 : {time_info.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if order.note:
        lines.append(f" 메모     : {order.note}")
        
    lines.append("-" * 48)
    # 헤더 정렬 (메뉴명 영역을 22칸으로 잡음)
    lines.append(f" {'메뉴명':<19} | {'수량':^3} | {'금액':>10}")
    lines.append("-" * 48)
    
    for item in order.items:
        # 메뉴명(예: 'Americano', 'Matcha Latte') 뒤에 옵션이 있다면 결합
        item_display_name = item.name
        if item.options:
            item_display_name += f" [{', '.join(item.options)}]"
            
        # 영문 메뉴명과 한글 특수문자가 섞여도 정렬이 깨지지 않도록 처리
        padded_name = pad_right_multibyte(item_display_name, 22)
        formatted_price = format_money(item.line_total)
        
        lines.append(f" {padded_name} | {item.quantity:^5} | {formatted_price:>12}")
        
    lines.append("-" * 48)
    
    if order.payment:
        lines.append(f" 결제 수단 : {order.payment.method}")
        
    lines.append(f" 총 결제액 : {format_money(order.total):>32}")
    lines.append("=" * 48)
    lines.append(f"{'이용해 주셔서 감사합니다!':^45}")
    lines.append("=" * 48)
    
    return "\n".join(lines)