from __future__ import annotations

from cafe_order_kiosk.kiosk_store import KioskStore
# from cafe_order_kiosk.utils import add_receipt

class AdminManager:
    def __init__(self) -> None:
        self.current_password: str = "1234"  # 초기 비밀번호
        self.is_admin_mode: bool = False

    def check_password(self, input_pw: str) -> bool:
        # 비밀번호를 검증 및 세션을 제어
        if input_pw == self.current_password:
            self.is_admin_mode = True
            return True
        return False

    def logout(self) -> None:
        self.is_admin_mode = False
        print("\n[안내] 관리자 모드가 종료되었습니다. 일반 화면으로 돌아갑니다.")

    def change_password(self) -> None:
        # 관리자 전용 기능 : 비밀번호 변경
        old_pw = input("현재 관리자 비밀번호를 입력하세요: ").strip()
        if old_pw != self.current_password:
            print("비밀번호가 일치하지 않습니다. 변경이 취소됩니다.")
            return

        new_pw = input("새로운 비밀번호를 입력하세요: ").strip()
        if not new_pw:
            print("빈 비밀번호는 사용할 수 없습니다.")
            return

        confirm_pw = input("새로운 비밀번호를 한번 더 입력하세요: ").strip()
        if new_pw != confirm_pw:
            print("새 비밀번호가 서로 일치하지 않습니다. 변경이 취소됩니다.")
            return

        self.current_password = new_pw
        print("관리자 비밀번호가 성공적으로 변경되었습니다!")

    def show_sales_summary(self, store: KioskStore) -> None:
        # 관리자 전용 기능 : 매출 조회
        # _orders 딕셔너리에서 결제 완료(paid)된 주문만 필터링
        paid_orders = [o for o in store._orders.values() if o.status == "paid"]

        if not paid_orders:
            print("\n" + "=" * 40)
            print(" 현재 결제 완료된 누적 매출 내역이 없습니다.")
            print("========================================")
            return

        total_sales = sum(o.total for o in paid_orders)
        menu_counts: dict[str, int] = {}

        for order in paid_orders:
            for item in order.items:
                menu_counts[item.name] = menu_counts.get(item.name, 0) + item.quantity

        print("\n" + "=" * 48)
        print(f"{'당일 영업 매출 통계 리포트':^40}")
        print("=" * 48)
        print(f" 총 결제 완료 건수 : {len(paid_orders)} 건")
        print(f" 총 누적 매출액   : {total_sales:,}원")
        print("-" * 48)
        print(" [메뉴별 총 판매 수량]")
        for menu_name, qty in menu_counts.items():
            print(f" - {menu_name:<18} : {qty}개")
        print("=" * 48)

    def reprint_receipt(self, store: KioskStore, order_id_str: str) -> None:
        print("\n[안내] 영수증 재발급 기능은 연동 준비 중입니다.")
        # 관리자 전용 기능 : 과거 영수증 재출력
        # if not order_id_str.isdigit():
        #     print("올바른 주문 번호(숫자)를 입력해주세요.")
        #     return

        # order_id = int(order_id_str)
        # order = store.get_order(order_id)

        # if order is None:
        #     print(f"주문 #{order_id} 내역을 시스템에서 찾을 수 없습니다.")
        #     return

        # print("\n" + "-" * 15 + " [영수증 재발급 마크] " + "-" * 15)
        # print(generate_receipt(order))
        # print("-" * 48)