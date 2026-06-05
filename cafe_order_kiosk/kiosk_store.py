from __future__ import annotations

from collections.abc import Iterable

from cafe_order_kiosk.models import MenuItem, Order, OrderItem, OrderStatus, Payment
from cafe_order_kiosk.utils import utc_now

# 메뉴 이름 4개 국어(ko,en,ch,ja)로 확장
DEFAULT_MENU: tuple[MenuItem, ...] = (
    MenuItem(id=1, name={"ko": "아메리카노", "en": "Americano", "ch": "美式咖啡", "ja": "アメリカーノ"}, price=3500, category="coffee"),
    MenuItem(id=2, name={"ko": "카페라떼", "en": "Latte", "ch": "拿铁咖啡", "ja": "カフェラテ"}, price=4000, category="coffee"),
    MenuItem(id=3, name={"ko": "카푸치노", "en": "Cappuccino", "ch": "卡布奇诺", "ja": "カプチーノ"}, price=4200, category="coffee"),
    MenuItem(id=4, name={"ko": "콜드브루", "en": "Cold Brew", "ch": "冷萃咖啡", "ja": "コールドブリュー"}, price=4500, category="coffee"),
    MenuItem(id=5, name={"ko": "말차라떼", "en": "Matcha Latte", "ch": "抹茶拿铁", "ja": "抹茶ラテ"}, price=4800, category="tea"),
    MenuItem(id=6, name={"ko": "캐모마일티", "en": "Chamomile Tea", "ch": "洋甘菊茶", "ja": "カモミールティー"}, price=3800, category="tea"),
    MenuItem(id=7, name={"ko": "레몬에이드", "en": "Lemonade", "ch": "柠檬水", "ja": "レモネード"}, price=4200, category="juice"),
    MenuItem(id=8, name={"ko": "버터 크로와상", "en": "Butter Croissant", "ch": "牛角面包", "ja": "クロワッサン"}, price=3500, category="bakery"),
    MenuItem(id=9, name={"ko": "블루베리 머핀", "en": "Blueberry Muffin", "ch": "蓝莓 maifen", "ja": "ブルーベリーマフィン"}, price=3200, category="bakery"),
    MenuItem(id=10, name={"ko": "치즈케이크", "en": "Cheesecake", "ch": "芝士蛋糕", "ja": "チーズケーキ"}, price=5200, category="dessert"),
)


class KioskStore:
    def __init__(self, menu_items: Iterable[MenuItem] | None = None) -> None:
        self._menu: dict[int, MenuItem] = {}
        for item in (menu_items or []):
            self._menu[item.id] = item
        self._orders: dict[int, Order] = {}
        self._next_order_id = 1

    @classmethod
    def with_default_menu(cls) -> KioskStore:
        return cls(menu_items=DEFAULT_MENU)

    def list_menu(self, only_available: bool = True) -> list[MenuItem]:
        items: Iterable[MenuItem] = self._menu.values()
        if only_available:
            items = [item for item in items if item.is_available]
        return sorted(items, key=lambda item: item.id)

    def get_menu_item(self, menu_item_id: int) -> MenuItem | None:
        return self._menu.get(menu_item_id)

    def create_order(self, note: str | None = None) -> Order:
        order_id = self._next_order_id
        self._next_order_id += 1

        order = Order(id=order_id, note=note)
        self._orders[order_id] = order
        return order

    def list_orders(self, status: OrderStatus | None = None) -> list[Order]:
        orders: Iterable[Order] = self._orders.values()
        if status is not None:
            orders = [order for order in orders if order.status == status]
        return sorted(orders, key=lambda order: order.id)

    def get_order(self, order_id: int) -> Order | None:
        return self._orders.get(order_id)

    def add_item(
        self,
        order_id: int,
        menu_item_id: int,
        quantity: int,
        options: list[str] | None = None,
    ) -> Order:
        order = self._require_order(order_id)
        if order.status is not OrderStatus.OPEN:
            raise ValueError("Order is not open")
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")

        menu_item = self._menu.get(menu_item_id)
        if menu_item is None:
            raise ValueError("Menu item not found")
        if not menu_item.is_available:
            raise ValueError("Menu item is not available")
        
        # 주문 목록에 담길 때 현재 설정된 언어 버전에 맞춰 출력
        item_name = menu_item.name["ko"] if isinstance(menu_item.name, dict) else menu_item.name

        order_item = OrderItem(
            menu_item_id=menu_item.id,
            name=menu_item.name,
            unit_price=menu_item.price,
            quantity=quantity,
            options=options or [],
        )
        order.items.append(order_item)
        return order

    def remove_item(self, order_id: int, line_index: int) -> Order:
        order = self._require_order(order_id)
        if order.status is not OrderStatus.OPEN:
            raise ValueError("Order is not open")
        if line_index < 1 or line_index > len(order.items):
            raise ValueError("Line item not found")

        order.items.pop(line_index - 1)
        return order

    def cancel_order(self, order_id: int) -> Order:
        order = self._require_order(order_id)
        if order.status is OrderStatus.CANCELED:
            return order
        if order.status is OrderStatus.PAID:
            raise ValueError("Paid order cannot be canceled")

        order.status = OrderStatus.CANCELED
        order.canceled_at = utc_now()
        return order

    def pay_order(self, order_id: int, method: str, amount: int) -> Order:
        order = self._require_order(order_id)
        if order.status is not OrderStatus.OPEN:
            raise ValueError("Order is not open")
        if not order.items:
            raise ValueError("Order has no items")
        if amount != order.total:
            raise ValueError("Payment amount does not match total")

        order.status = OrderStatus.PAID
        order.paid_at = utc_now()
        order.payment = Payment(method=method, amount=amount, paid_at=order.paid_at)
        return order

    def _require_order(self, order_id: int) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise ValueError("Order not found")
        return order
