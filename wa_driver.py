import re
from contextlib import contextmanager

from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeoutError


@contextmanager
def get_wa_page(user_id: str, main_page: bool = True):
    with sync_playwright() as p:
        context = p.webkit.launch_persistent_context(
            user_data_dir=f"wa_sessions/{user_id}/wa_session",
            headless=True
        )
        page = context.new_page()

        if main_page:
            # Открываем WhatsApp Web
            page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

        yield page


def is_login(page: Page):
    try:
        page.wait_for_selector("canvas", timeout=10*1000)
    except PWTimeoutError:
        return True

    return False

def save_qr_code(page: Page, user_id: str):
    page.wait_for_selector("canvas", timeout=30*1000)
    page.screenshot(path=f"wa_sessions/{user_id}/qr.jpg")
    return False


def get_qr_code(page: Page, user_id: str):
    save_qr_code(page, user_id)
    return open(f"wa_sessions/{user_id}/qr.jpg", "rb")


def wait_until_login(page: Page):
    search_field = page.wait_for_selector("div[contenteditable='true'][data-tab='3']", timeout=30 * 1000)
    if not search_field:
        raise TimeoutError("Waiting for search field timeout")


def send_group_msg(page: Page, group_name: str, text: str):
    # Поиск группы
    page.click("div[contenteditable='true'][data-tab='3']")
    page.keyboard.type(group_name)
    page.keyboard.press("Enter")

    # Поле ввода
    page.wait_for_selector("div[contenteditable='true'][data-tab='10']")
    page.keyboard.type(text)
    page.keyboard.press("Enter")
    try:
        page.wait_for_selector("span[data-icon='msg-time']", state="detached", timeout=10*1000)
    except PWTimeoutError:
        raise TimeoutError("Waiting for sending msg in group timeout")

    page.wait_for_timeout(3*1000)



def serialize_phone(phone: str):
    """Приводим номер телефона к формату: 79991234567"""
    all_digits = re.findall(r'\d+', phone)
    if all_digits[0] == 8:
        all_digits[0] = 7

    return "".join(all_digits)


def send_personal_msg(page: Page, phone: str, text: str):
    phone = serialize_phone(phone)
    page.goto(
        "https://web.whatsapp.com/send"
        f"?phone={phone}"  # Формат: 79991234567
        f"&text={text}",
        wait_until="domcontentloaded",
    )
    page.wait_for_selector("div[contenteditable='true'][data-tab='10']")
    page.keyboard.press("Enter")
    try:
        page.wait_for_selector("span[data-icon='msg-time']", state="detached", timeout=10*1000)
    except PWTimeoutError:
        raise TimeoutError("Waiting for sending msg in personal timeout")

    page.wait_for_timeout(3*1000)
