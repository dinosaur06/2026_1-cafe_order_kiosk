from __future__ import annotations

import shlex
from dataclasses import dataclass

from cafe_order_kiosk.models import OrderStatus
from cafe_order_kiosk.kiosk_store import KioskStore
from cafe_order_kiosk.utils import format_money

# 4개 국어 안내 딕셔너리 추가
MULTILINGUAL_MSGS = {
    # 1. 시스템 안내 메시지
    "title": { "ko": "카페 주문 키오스크", "en": "Cafe Order Kiosk", "ch": "咖啡订餐自助机", "ja": "カフェ注文キオスク" },
    "welcome": {
        "ko": "명령어 목록은 '도움말'을 입력하세요. 가격은 원 단위 정수입니다.",
        "en": "Type 'help' to see available commands. Prices are in KRW.",
        "ch": "输入 '帮助' 查看命令列表。 价格单位为韩元。",
        "ja": "コマンド一覧は 'ヘルプ' と入力してください。価格はウォン単位です。"
    },
    "unknown": {
        "ko": "알 수 없는 명령입니다. '도움말'을 입력하세요.",
        "en": "Unknown command. Type 'help'.",
        "ch": "未知命令。请输入 '帮助'。",
        "ja": "不明なコマンドです。'ヘルプ' と入力してください。"
    },
    "lang_select": {
        "ko": "변경할 언어 번호를 입력하세요 (1: 한국어, 2: English, 3: 中文, 4: 日本語): ",
        "en": "Select language number (1: 한국어, 2: English, 3: 中文, 4: 日本語): ",
        "ch": "请输入语言编号 (1: 한국어, 2: English, 3: 中文, 4: 日本語): ",
        "ja": "言語の番号を入力してください (1: 한국어, 2: English, 3: 中文, 4: 日本語): "
    },
    "lang_changed": { "ko": "한국어로 변경되었습니다.", "en": "Language changed to English.", "ch": "语言已更改为中文。", "ja": "言語が日本語に変更されました。" },
    "menu_header": { "ko": "메뉴:", "en": "Menu:", "ch": "菜单:", "ja": "メニュー:" },
    "exit_msg": { "ko": "종료합니다.", "en": "Exiting system.", "ch": "正在退出程序。", "ja": "終了します。" },
    
    # 2. 메인 명령어 매핑 (현재 언어에 맞는 단어만 매칭됨)
    "cmd_help": { "ko": "도움말", "en": "help", "ch": "帮助", "ja": "ヘルプ" },
    "cmd_menu": { "ko": "메뉴", "en": "menu", "ch": "菜单", "ja": "メニュー" },
    "cmd_order": { "ko": "주문", "en": "order", "ch": "订单", "ja": "注文" },
    "cmd_orders": { "ko": "주문목록", "en": "orders", "ch": "订单列表", "ja": "注文一覧" },
    "cmd_pay": { "ko": "결제", "en": "pay", "ch": "支付", "ja": "決済" },
    "cmd_lang": { "ko": "언어변경", "en": "lang", "ch": "语言", "ja": "言語" },

    # 3. 주문(order) 하위 서브 명령어 매핑
    "sub_new": { "ko": "생성", "en": "new", "ch": "创建", "ja": "作成" },
    "sub_select": { "ko": "선택", "en": "select", "ch": "选择", "ja": "選択" },
    "sub_add": { "ko": "추가", "en": "add", "ch": "添加", "ja": "追加" },
    "sub_remove": { "ko": "삭제", "en": "remove", "ch": "删除", "ja": "削除" },
    "sub_show": { "ko": "조회", "en": "show", "ch": "查看", "ja": "確認" },
    "sub_cancel": { "ko": "취소", "en": "cancel", "ch": "取消", "ja": "取消" },

    # 4. 출력 및 에러 메시지 데이터들
    "order_cmd_error": {
        "ko": "주문 명령어: 생성, 선택, 추가, 삭제, 조회, 취소",
        "en": "Order commands: new, select, add, remove, show, cancel",
        "ch": "订单命令: 创建, 选择, 添加, 删除, 查看, 取消",
        "ja": "注文コマンド: 作成, 選択, 追加, 削除, 確認, 取消"
    },
    "order_created": { "ko": "주문 #{id}가 생성되었습니다.", "en": "Order #{id} has been created.", "ch": "订单 #{id} 已创建。", "ja": "注文 #{id} が作成されました。" },
    "order_not_found": { "ko": "주문을 찾을 수 없습니다.", "en": "Order not found.", "ch": "找不到订单。", "ja": "注文が見つかりません。" },
    "order_selected": { "ko": "주문 #{id}를 선택했습니다.", "en": "Selected Order #{id}.", "ch": "已选择订单 #{id}。", "ja": "注文 #{id} を選択しました。" },
    "no_order_selected": {
        "ko": "선택된 주문이 없습니다. 먼저 '주문 생성'을 사용하세요.",
        "en": "No order selected. Please create or select an order first.",
        "ch": "未选择订单。请先创建订单。",
        "ja": "選択された注文がありません。まず注文を作成してください。"
    },
    "order_add_usage": { "ko": "사용법: 주문 추가 <메뉴_id> <수량> [옵션]", "en": "Usage: order add <menu_id> <qty> [options]", "ch": "用法: 订单 添加 <menu_id> <数量> [选项]", "ja": "使い方: 注文 追加 <menu_id> <数量> [オプション]" },
    "item_added": { "ko": "항목이 추가되었습니다.", "en": "Item added.", "ch": "项目已添加。", "ja": "商品が追加されました。" },
    "item_removed": { "ko": "항목이 삭제되었습니다.", "en": "Item removed.", "ch": "项目已删除。", "ja": "商品が削除されました。" },
    "order_canceled": { "ko": "주문 #{id}가 취소되었습니다.", "en": "Order #{id} canceled.", "ch": "订单 #{id} 已取消。", "ja": "注文 #{id} がキャンセルされました。" },
    "orders_list_usage": { "ko": "사용법: 주문목록 목록 [진행중|결제완료|취소]", "en": "Usage: orders list [open|paid|canceled]", "ch": "用法: 订单列表 列表 [open|paid|canceled]", "ja": "使い方: 注文一覧 リスト [open|paid|canceled]" },
    "no_orders": { "ko": "주문이 없습니다.", "en": "No orders found.", "ch": "没有订单。", "ja": "注文がありません。" },
    "pay_usage": { "ko": "사용법: 결제 <방법> [금액]", "en": "Usage: pay <method> [amount]", "ch": "用法: 支付 <方式> [金额]", "ja": "使い方: 決済 <方法> [金額]" },
    "pay_success": { "ko": "주문 #{id} 결제 완료 ({method}).", "en": "Order #{id} Payment complete ({method}).", "ch": "订单 #{id} 支付成功 ({method})。", "ja": "注文 #{id} の決済가 완료되었습니다 ({method})。" },
    "empty": { "ko": "  (비어 있음)", "en": "  (Empty)", "ch": "  (空)", "ja": "  (空)" },
    "total": { "ko": "합계", "en": "Total", "ch": "总计", "ja": "合計" },
    "note": { "ko": "메모", "en": "Note", "ch": "备注", "ja": "メモ" },
    "status_open": { "ko": "진행중", "en": "OPEN", "ch": "进行中", "ja": "進行中" },
    "status_paid": { "ko": "결제완료", "en": "PAID", "ch": "已支付", "ja": "決済完了" },
    "status_canceled": { "ko": "취소", "en": "CANCELED", "ch": "已取消", "ja": "キャンセル" },
    "missing_arg": { "ko": "필수 값이 없습니다: {name}", "en": "Missing required value: {name}", "ch": "缺少必需的值: {name}", "ja": "必須の値がありません: {name}" },
    "invalid_arg": { "ko": "잘못된 값: {name}", "en": "Invalid value for {name}", "ch": "无效的值: {name}", "ja": "無効な値: {name}" },
    "menu_item_not_found": { "ko": "존재하지 않는 메뉴 번호입니다.", "en": "Menu item not found.", "ch": "该菜单编号不存在。", "ja": "存在しないメニュー番号です。" }
}

@dataclass
class CLIState:
    current_order_id: int | None = None
    current_lang: str = "ko"    # 기본값 : 한국어

def run_cli() -> int:
    store = KioskStore.with_default_menu()
    state = CLIState()

    print(MULTILINGUAL_MSGS["title"][state.current_lang])
    print(MULTILINGUAL_MSGS["welcome"][state.current_lang])

    while True:
        try:
            prompt = f"kiosk({state.current_lang})> "
            raw = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue

        tokens = shlex.split(raw)
        command, args = tokens[0], tokens[1:]
        lang = state.current_lang

        if command in {"종료", "끝", "quit", "exit", "退出", "終了"}:
            break
        
        elif command == MULTILINGUAL_MSGS["cmd_help"][lang] or command == "help":
            print_help(lang)
        elif command == MULTILINGUAL_MSGS["cmd_menu"][lang]:
            handle_menu(store, lang)
        elif command == MULTILINGUAL_MSGS["cmd_order"][lang]:
            handle_order(store, state, args)
        elif command == MULTILINGUAL_MSGS["cmd_orders"][lang]:
            handle_orders(store, lang, args)
        elif command == MULTILINGUAL_MSGS["cmd_pay"][lang]:
            handle_pay(store, state, args)
        elif command == MULTILINGUAL_MSGS["cmd_lang"][lang] or command == "lang":
            handle_change_language(state)
        else:
            print(MULTILINGUAL_MSGS["unknown"][lang])

    print(MULTILINGUAL_MSGS["exit_msg"][state.current_lang])
    return 0

# 언어 상태 스위치 인터페이스
def handle_change_language(state: CLIState) -> None:
    print(MULTILINGUAL_MSGS["lang_select"][state.current_lang])
    choice = input("> ").strip()
    if choice == "1":
        state.current_lang = "ko"
    elif choice == "2":
        state.current_lang = "en"
    elif choice == "3":
        state.current_lang = "ch"
    elif choice == "4":
        state.current_lang = "ja"
    else:
        print(MULTILINGUAL_MSGS["unknown"][state.current_lang])
        return
    print(MULTILINGUAL_MSGS["lang_changed"][state.current_lang])


def print_help(lang: str) -> None:
    if lang == "ko":
        print("명령어:")
        print("\t메뉴\n\t주문 생성 [메모]\n\t주문 선택 <주문_id>\n\t주문 추가 <메뉴_id> <수량> [옵션]\n\t주문 삭제 <라인번호>\n\t주문 조회\n\t주문 취소\n\t주문목록 목록 [진행중|결제완료|취소]\n\t결제 <방법> [금액]\n\t언어변경\n\t도움말\n\t종료")
    elif lang == "ch":
        print("可用命令:")
        print("\t菜单\n\t订单 创建 [备注]\n\t订单 选择 <订单_id>\n\t订单 添加 <菜单_id> <数量> [选项]\n\t订单 删除 <行号>\n\t订单 查看\n\t订单 取消\n\t订单列表 列表\n\t支付 <方式> [金额]\n\t语言\n\t帮助\n\t退出")
    elif lang == "ja":
        print("利用可能なコマンド:")
        print("\tメニュー\n\t注文 作成 [メモ]\n\t注文 選択 <注文_id>\n\t注文 追加 <メニュー_id> <数量> [オプション]\n\t注文 削除 <ライン番号>\n\t注文 確認\n\t注文 取消\n\t注文一覧 リスト\n\t決済 <方法> [金額]\n\t言語\n\tヘルプ\n\t終了")
    else:
        print("Available Commands:")
        print("\tmenu\n\torder new [note]\n\torder select <order_id>\n\torder add <menu_id> <qty> [options]\n\torder remove <line_idx>\n\torder show\n\torder cancel\n\torders list [open|paid|canceled]\n\tpay <method> [amount]\n\tlang\n\thelp\n\texit")


def handle_menu(store: KioskStore, lang: str) -> None:
    print(MULTILINGUAL_MSGS["menu_header"][lang])
    for item in store.list_menu():
        description = f" - {item.description}" if item.description else ""

        # item.name이 딕셔너리 구조면 현재 국가 언어로 출력, 일반 문자열이면 그대로 출력
        if isinstance(item.name, dict):
            menu_name = item.name.get(lang, item.name.get("ko", "No Name"))
        else:
            menu_name = item.name

        print(f"\t{item.id}. {menu_name} ({item.category}) - {format_money(item.price)}{description}")


def handle_order(store: KioskStore, state: CLIState, args: list[str]) -> None:
    lang = state.current_lang
    if not args:
        print(MULTILINGUAL_MSGS["order_cmd_error"][lang])
        return
    action, tail = args[0], args[1:]

    if action == MULTILINGUAL_MSGS["sub_new"][lang]:
        note = " ".join(tail).strip() if tail else None
        order = store.create_order(note=note)
        state.current_order_id = order.id
        print(MULTILINGUAL_MSGS["order_created"][lang].format(id=order.id))
    
    elif action == MULTILINGUAL_MSGS["sub_selected" if "sub_selected" in MULTILINGUAL_MSGS else "sub_select"][lang]:
        order_id = parse_int_arg(tail, "order_id", lang)
        if order_id is None:
            return
        order = store.get_order(order_id)
        if order is None:
            print(MULTILINGUAL_MSGS["order_not_found"][lang])
            return
        state.current_order_id = order.id
        print(MULTILINGUAL_MSGS["order_selected"][lang].format(id=order.id))

    elif action == MULTILINGUAL_MSGS["sub_add"][lang]:
        if state.current_order_id is None:
            print(MULTILINGUAL_MSGS["no_order_selected"][lang])
            return
        if len(tail) < 2:
            print(MULTILINGUAL_MSGS["order_add_usage"][lang])
            return
        menu_id = parse_int_arg(tail[:1], "menu_id", lang)
        quantity = parse_int_arg(tail[1:2], "qty", lang)
        if menu_id is None or quantity is None:
            return

        options_text = " ".join(tail[2:]).strip()
        options = [opt.strip() for opt in options_text.split(",") if opt.strip()] if options_text else []
        try:
            store.add_item(state.current_order_id, menu_id, quantity, options)
        except ValueError as exc:
            # kiosk_store에서 넘어온 에러 문자열이 "Menu item not found"라면 다국어 메시지 출력
            if str(exc) == "Menu item not found":
                print(MULTILINGUAL_MSGS["menu_item_not_found"][lang])
            else:
                print(str(exc))
            return
        print(MULTILINGUAL_MSGS["item_added"][lang])

    elif action == MULTILINGUAL_MSGS["sub_remove"][lang]:
        if state.current_order_id is None:
            print(MULTILINGUAL_MSGS["no_order_selected"][lang])
            return
        line_index = parse_int_arg(tail, "line_index", lang)
        if line_index is None:
            return
        try:
            store.remove_item(state.current_order_id, line_index)
        except ValueError as exc:
            print(str(exc))
            return
        print(MULTILINGUAL_MSGS["item_removed"][lang])

    elif action == MULTILINGUAL_MSGS["sub_show"][lang]:
        if state.current_order_id is None:
            print(MULTILINGUAL_MSGS["no_order_selected"][lang])
            return
        order = store.get_order(state.current_order_id)
        if order is None:
            print(MULTILINGUAL_MSGS["order_not_found"][lang])
            return
        print_order(order, lang)

    elif action == MULTILINGUAL_MSGS["sub_cancel"][lang]:
        if state.current_order_id is None:
            print(MULTILINGUAL_MSGS["no_order_selected"][lang])
            return
        try:
            order = store.cancel_order(state.current_order_id)
        except ValueError as exc:
            print(str(exc))
            return
        print(MULTILINGUAL_MSGS["order_canceled"][lang].format(id=order.id))
    else:
        print(MULTILINGUAL_MSGS["unknown"][lang])


def handle_orders(store: KioskStore, lang: str, args: list[str]) -> None:
    list_keywords = {"list", "목록", "列表", "リスト"}
    if not args or args[0] not in list_keywords:
        print(MULTILINGUAL_MSGS["orders_list_usage"][lang])
        return

    status = None
    if len(args) > 1:
        status = parse_status(args[1], lang)
        if status is None:
            return

    orders = store.list_orders(status)
    if not orders:
        print(MULTILINGUAL_MSGS["no_orders"][lang])
        return

    for order in orders:
        print(f"  #{order.id} {format_status(order.status, lang)} - {format_money(order.total)}")


def handle_pay(store: KioskStore, state: CLIState, args: list[str]) -> None:
    lang = state.current_lang
    if state.current_order_id is None:
        print(MULTILINGUAL_MSGS["no_order_selected"][lang])
        return
    if not args:
        print(MULTILINGUAL_MSGS["pay_usage"][lang])
        return

    method = args[0]
    amount = None
    if len(args) > 1:
        amount = parse_int_arg(args[1:2], "amount", lang)
        if amount is None:
            return

    order = store.get_order(state.current_order_id)
    if order is None:
        print(MULTILINGUAL_MSGS["order_not_found"][lang])
        return
    if amount is None:
        amount = order.total

    try:
        store.pay_order(order.id, method, amount)
    except ValueError as exc:
        print(str(exc))
        return

    print(MULTILINGUAL_MSGS["pay_success"][lang].format(id=order.id, method=method))

def print_order(order: Order, lang: str = "ko") -> None:
    status_str = format_status(order.status, lang)
    print(f"Order #{order.id} ({status_str})")
    
    if order.note:
        print(f"{MULTILINGUAL_MSGS['note'][lang]}: {order.note}")
    if not order.items:
        print(MULTILINGUAL_MSGS["empty"][lang])
        return

    for idx, item in enumerate(order.items, start=1):
        options = f" [{', '.join(item.options)}]" if item.options else ""
        
        if isinstance(item.name, dict):
            display_name = item.name.get(lang, item.name.get("ko", "No Name"))        
        else:
            display_name = item.name
        
        print(f"  {idx}. {display_name}{options} x{item.quantity} - {format_money(item.line_total)}")
        
    print(f"{MULTILINGUAL_MSGS['total'][lang]}: {format_money(order.total)}")

def parse_int_arg(args: list[str], name: str, lang: str) -> int | None:
    if not args:
        print(MULTILINGUAL_MSGS["missing_arg"][lang].format(name=name))
        return None
    try:
        return int(args[0])
    except ValueError:
        print(MULTILINGUAL_MSGS["invalid_arg"][lang].format(name=name))        
        return None


def parse_status(raw: str, lang: str) -> OrderStatus | None:
    normalized = raw.lower()
    status_map = {
        "open": OrderStatus.OPEN, "paid": OrderStatus.PAID, "canceled": OrderStatus.CANCELED,
        "진행중": OrderStatus.OPEN, "결제완료": OrderStatus.PAID, "취소": OrderStatus.CANCELED,
        "进行中": OrderStatus.OPEN, "已支付": OrderStatus.PAID, "已取消": OrderStatus.CANCELED,
        "進行中": OrderStatus.OPEN, "決済完了": OrderStatus.PAID, "キャンセル": OrderStatus.CANCELED    }
    status = status_map.get(normalized)
    if status is None:
        if lang == "ko": print("잘못된 상태입니다. 진행중, 결제완료, 취소 중에서 선택하세요.")
        elif lang == "ch": print("无效的状态。请从 进行中, 已支付, 已取消 中选择。")
        elif lang == "ja": print("無効なステータスです。進行中、決済完了、キャンセルから選択してください。")
        else: print("Invalid status. Choose from open, paid, canceled.")    
    return status
    
def format_status(status: OrderStatus, lang: str) -> str:
    key = f"status_{status.value}"
    return MULTILINGUAL_MSGS.get(key, {}).get(lang, status.value)