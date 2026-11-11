"""Selenium UI tests (Microsoft Edge, headless). Screenshots are saved to 07_Screenshots."""
import os
import re
import socket
import threading
import time

import httpx
import pytest
import uvicorn

pytestmark = pytest.mark.ui
selenium = pytest.importorskip("selenium")
from selenium import webdriver  # noqa: E402
from selenium.common.exceptions import StaleElementReferenceException  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402
from selenium.webdriver.edge.options import Options  # noqa: E402
from selenium.webdriver.support import expected_conditions as EC  # noqa: E402
from selenium.webdriver.support.ui import Select, WebDriverWait  # noqa: E402

from app.main import app  # noqa: E402

SHOTS = os.path.join(os.path.dirname(__file__), "..", "07_Screenshots")


@pytest.fixture(scope="module")
def base_url(tmp_path_factory):
    os.environ["WATER_DB"] = str(tmp_path_factory.mktemp("ui") / "ui.db")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.1)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    t.join(timeout=5)


@pytest.fixture()
def driver(base_url):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1100,900")
    d = webdriver.Edge(options=opts)
    d.implicitly_wait(2)
    d.get(base_url)
    yield d
    d.quit()


def shot(d, name):
    os.makedirs(SHOTS, exist_ok=True)
    d.save_screenshot(os.path.join(SHOTS, name + ".png"))


def text_of(d, elem_id, contains=None, timeout=8):
    w = WebDriverWait(d, timeout)
    if contains:
        w.until(EC.text_to_be_present_in_element((By.ID, elem_id), contains))
    return d.find_element(By.ID, elem_id).text


def fill(d, elem_id, value):
    e = d.find_element(By.ID, elem_id)
    e.clear()
    e.send_keys(str(value))


def login(d, user, password):
    fill(d, "l-user", user)
    fill(d, "l-pass", password)
    d.find_element(By.ID, "login-btn").click()


def wait_visible(d, elem_id, timeout=8):
    return WebDriverWait(d, timeout).until(EC.visibility_of_element_located((By.ID, elem_id)))


def login_as_admin(d):
    login(d, "admin", "admin123")
    wait_visible(d, "app")


def open_page(d, name):
    item = d.find_element(By.ID, "nav-" + name)
    if "active" in item.get_attribute("class"):      # already the landing page: don't trigger a second render
        time.sleep(0.8)
        return
    item.click()


def logout(d):
    d.find_element(By.ID, "logout-btn").click()
    wait_visible(d, "auth-screen")


def test_TC_UI01_invalid_login_shows_error(driver):
    login(driver, "admin", "wrong-password")
    assert "Invalid username or password" in text_of(driver, "auth-msg", "Invalid")
    shot(driver, "UI01_login_screen_error")


def ensure_customer(base_url, username, password="secret1"):
    """Create a customer through the API (ignore 'already exists')."""
    httpx.post(base_url + "/api/auth/register",
               json={"username": username, "password": password, "full_name": "Test Customer"})


def login_as_customer(d, base_url, username="tester"):
    ensure_customer(base_url, username)
    login(d, username, "secret1")
    wait_visible(d, "app")


def test_TC_UI02_bill_estimator(driver, base_url):
    login_as_customer(driver, base_url)
    open_page(driver, "estimator")
    fill(driver, "c-units", 25)
    driver.find_element(By.ID, "calc-btn").click()
    assert "Total: \u20b9240.00" in text_of(driver, "calc-out", "Total")
    shot(driver, "UI02_bill_estimator")


def test_TC_UI03_estimator_negative_units_rejected(driver, base_url):
    login_as_customer(driver, base_url)
    open_page(driver, "estimator")
    fill(driver, "c-units", -5)
    driver.find_element(By.ID, "calc-btn").click()
    assert "greater than or equal to 0" in text_of(driver, "calc-out", "greater")
    shot(driver, "UI03_negative_units")


def test_TC_UI04_admin_login_shows_admin_menu(driver):
    login_as_admin(driver)
    assert driver.find_element(By.ID, "who").text == "System Administrator"
    assert driver.find_element(By.ID, "role-label").text.lower() == "admin"
    menu = [b.text for b in driver.find_elements(By.CSS_SELECTOR, "#nav .nav-item")]
    assert [m.title() for m in menu] == ["Dashboard", "Customers", "Readings", "Bills", "Payments", "Feedback"]
    shot(driver, "UI04_admin_customers")


def choose(d, elem_id, value=None, index=None):
    """Pick a <select> option; retry if the page re-renders (and the element goes stale) mid-click."""
    for _ in range(6):
        try:
            sel = Select(d.find_element(By.ID, elem_id))
            sel.select_by_value(value) if value is not None else sel.select_by_index(index)
            return
        except StaleElementReferenceException:
            time.sleep(0.4)
    raise AssertionError(f"could not select an option in #{elem_id}")


def add_reading_ui(d, meter, value):
    """Open the Add reading popup for one meter, enter a reading and save it."""
    for _ in range(6):
        try:
            WebDriverWait(d, 8).until(EC.element_to_be_clickable((By.CSS_SELECTOR, f".add-reading-btn[data-meter='{meter}']"))).click()
            break
        except StaleElementReferenceException:
            time.sleep(0.4)
    wait_visible(d, "rd-modal")
    fill(d, "m-read", value)
    d.find_element(By.ID, "read-btn").click()
    WebDriverWait(d, 8).until(EC.invisibility_of_element_located((By.ID, "rd-modal")))
    text_of(d, "toast", "Reading saved")
    time.sleep(0.6)                                    # the table re-renders after saving


def test_TC_UI05_end_to_end_billing_and_payment(driver):
    # 1. customer registers from the Create account tab
    driver.find_element(By.ID, "tab-register").click()
    fill(driver, "r-name", "Ravi Kumar")
    fill(driver, "r-user", "ravi")
    fill(driver, "r-pass", "secret1")
    driver.find_element(By.ID, "register-btn").click()
    cust_id = re.search(r"customer id is: (\d+)", text_of(driver, "reg-msg", "customer id")).group(1)
    # 2. admin creates a connection, records two readings and generates the bill
    driver.find_element(By.ID, "tab-login").click()
    login_as_admin(driver)
    open_page(driver, "customers")
    WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.ID, "new-conn-btn"))).click()
    wait_visible(driver, "conn-modal")
    choose(driver, "a-cust", value=cust_id)
    fill(driver, "a-meter", "UIMTR1")
    fill(driver, "a-addr", "7 River View")
    shot(driver, "UI05_new_connection_popup")
    driver.find_element(By.ID, "conn-btn").click()
    WebDriverWait(driver, 8).until(EC.invisibility_of_element_located((By.ID, "conn-modal")))
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "customer-rows"), "UIMTR1"))
    open_page(driver, "readings")
    add_reading_ui(driver, "UIMTR1", 50)
    add_reading_ui(driver, "UIMTR1", 75)
    WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".gen-btn[data-meter='UIMTR1']"))).click()
    assert "\u20b9240.00" in text_of(driver, "toast", "generated")
    shot(driver, "UI05a_bill_generated")
    # 3. customer signs in, sees the unpaid bill and pays it
    logout(driver)
    login(driver, "ravi", "secret1")
    wait_visible(driver, "app")
    open_page(driver, "bills")
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "bill-rows"), "Unpaid"))
    shot(driver, "UI05b_customer_bills")
    driver.find_element(By.CSS_SELECTOR, "#bill-rows .pay-btn").click()
    wait_visible(driver, "pay-modal")
    assert "\u20b9240.00" in driver.find_element(By.ID, "pay-total").text
    shot(driver, "UI05c_payment_dialog")
    driver.find_element(By.ID, "confirm-ok").click()
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#bill-rows .status"), "Paid"))
    shot(driver, "UI05d_bill_paid")


def test_TC_UI06_logout_returns_to_login_and_session_is_gone(driver):
    login_as_admin(driver)
    logout(driver)
    driver.refresh()
    wait_visible(driver, "auth-screen")
    assert not driver.find_element(By.ID, "app").is_displayed()


def test_TC_UI07_customer_does_not_see_admin_menu(driver, base_url):
    login_as_customer(driver, base_url)
    assert driver.find_elements(By.ID, "nav-customers") == []
    assert driver.find_elements(By.ID, "nav-readings") == []
    menu = [b.text for b in driver.find_elements(By.CSS_SELECTOR, "#nav .nav-item")]
    assert [m.capitalize() for m in menu] == ["Dashboard", "My bills", "Payments", "Feedback", "Estimate"]
    shot(driver, "UI07_customer_menu")


# ---------------- payments, complaints, profile, lock-out ----------------
def api_admin_headers(base_url):
    token = httpx.post(base_url + "/api/auth/login", json={"username": "admin", "password": "admin123"}).json()["token"]
    return {"Authorization": "Bearer " + token}


def make_billed_customer(base_url, username, meter):
    """Customer with one unpaid bill of Rs 240 (25 kL), created through the API."""
    h = api_admin_headers(base_url)
    cid = httpx.post(base_url + "/api/auth/register",
                     json={"username": username, "password": "secret1", "full_name": "Billed " + username}).json()["id"]
    conn = httpx.post(base_url + "/api/connections", headers=h, json={
        "customer_id": cid, "meter_no": meter, "type": "DOMESTIC", "address": "1 Test Street"}).json()["id"]
    for value in (10, 35):
        httpx.post(base_url + "/api/readings", headers=h, json={"connection_id": conn, "reading": value})
    httpx.post(base_url + "/api/bills/generate", headers=h, json={"connection_id": conn})


def test_TC_UI08_payment_creates_a_receipt(driver, base_url):
    make_billed_customer(base_url, "payer", "PAYMTR1")
    login(driver, "payer", "secret1")
    wait_visible(driver, "app")
    open_page(driver, "bills")
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "bill-rows"), "Unpaid"))
    driver.find_element(By.CSS_SELECTOR, "#bill-rows .pay-btn").click()
    wait_visible(driver, "pay-modal")
    Select(driver.find_element(By.ID, "pay-method")).select_by_value("CARD")
    driver.find_element(By.ID, "confirm-ok").click()
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#bill-rows .status"), "Paid"))
    open_page(driver, "payments")
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "pay-rows"), "RCP-"))
    assert "Card" in driver.find_element(By.ID, "pay-rows").text
    driver.find_element(By.CSS_SELECTOR, "#pay-rows .receipt-btn").click()
    wait_visible(driver, "receipt-modal")
    assert "\u20b9240.00" in text_of(driver, "receipt-total", "240")
    assert "PAYMTR1" in driver.find_element(By.ID, "receipt-body").text
    shot(driver, "UI08_receipt")


def test_TC_UI09_complaint_raised_by_customer_and_updated_by_admin(driver, base_url):
    ensure_customer(base_url, "complainer")
    login(driver, "complainer", "secret1")
    wait_visible(driver, "app")
    open_page(driver, "complaints")
    WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.ID, "new-complaint-btn"))).click()
    wait_visible(driver, "cp-modal")
    Select(driver.find_element(By.ID, "cp-cat")).select_by_value("LEAK")
    fill(driver, "cp-desc", "Water is leaking from the pipe outside our gate.")
    shot(driver, "UI09a_new_complaint")
    driver.find_element(By.ID, "cp-save").click()
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "complaint-rows"), "Open"))
    logout(driver)
    login_as_admin(driver)
    open_page(driver, "complaints")
    WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#complaint-rows .cu-btn"))).click()
    wait_visible(driver, "cu-modal")
    options = Select(driver.find_element(By.ID, "cu-status")).options
    assert [o.text for o in options] == ["Open (current)", "In progress", "Resolved"]
    assert [o.is_enabled() for o in options] == [False, True, False]
    shot(driver, "UI09c_update_complaint")
    driver.find_element(By.ID, "cu-save").click()
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "complaint-rows"), "In progress"))
    shot(driver, "UI09b_admin_complaints")


def test_TC_UI10_customer_changes_password(driver, base_url):
    ensure_customer(base_url, "pwuser")
    login(driver, "pwuser", "secret1")
    wait_visible(driver, "app")
    driver.find_element(By.ID, "who").click()
    WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.ID, "p-menu-btn"))).click()
    shot(driver, "UI10a_profile_menu")
    driver.find_element(By.ID, "menu-password").click()
    wait_visible(driver, "pw-modal")
    fill(driver, "p-cur", "secret1")
    fill(driver, "p-new", "newsecret9")
    fill(driver, "p-new2", "different9")
    driver.find_element(By.ID, "p-pass-btn").click()
    assert "do not match" in text_of(driver, "p-pass-msg", "match")
    fill(driver, "p-new2", "newsecret9")
    driver.find_element(By.ID, "p-pass-btn").click()
    assert "Password changed" in text_of(driver, "toast", "Password changed")
    logout(driver)
    login(driver, "pwuser", "newsecret9")
    wait_visible(driver, "app")


def test_TC_UI12_profile_name_is_edited_through_the_menu(driver, base_url):
    ensure_customer(base_url, "renamer")
    login(driver, "renamer", "secret1")
    wait_visible(driver, "app")
    driver.find_element(By.ID, "who").click()
    WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.ID, "p-menu-btn"))).click()
    driver.find_element(By.ID, "menu-name").click()
    wait_visible(driver, "pn-modal")
    fill(driver, "p-name", "Renamed Person")
    driver.find_element(By.ID, "p-name-btn").click()
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "profile-name"), "Renamed Person"))
    assert driver.find_element(By.ID, "who").text == "Renamed Person"
    shot(driver, "UI12_profile")


def test_TC_UI11_account_locks_after_five_failed_sign_ins(driver, base_url):
    ensure_customer(base_url, "lockme")
    for _ in range(5):
        login(driver, "lockme", "wrong-password")
        time.sleep(0.5)
    assert "locked" in text_of(driver, "auth-msg", "locked").lower()
    shot(driver, "UI11_account_locked")
    login(driver, "lockme", "secret1")                      # even the right password is refused while locked
    time.sleep(0.6)
    assert not driver.find_element(By.ID, "app").is_displayed()


# ---------------- customer history, type filter, captions ----------------
def test_TC_UI13_clicking_a_customer_name_opens_their_history(driver, base_url):
    make_billed_customer(base_url, "history1", "HISTMTR1")
    login_as_admin(driver)
    open_page(driver, "customers")
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "customer-rows"), "Billed history1"))
    for _ in range(5):
        try:
            driver.find_element(By.XPATH, "//a[contains(@class,'cust-link') and text()='Billed history1']").click()
            break
        except StaleElementReferenceException:
            time.sleep(0.4)
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "detail-name"), "Billed history1"))
    assert "HISTMTR1" in driver.find_element(By.ID, "detail-pane").text or "HISTMTR1" in driver.find_element(By.ID, "view").text
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "bill-rows"), "Unpaid"))
    driver.find_element(By.ID, "dtab-readings").click()
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "detail-pane"), "first reading"))
    shot(driver, "UI13_customer_history")
    driver.find_element(By.ID, "back-customers").click()
    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "type-filter")))


def test_TC_UI14_customers_can_be_filtered_by_connection_type(driver, base_url):
    h = api_admin_headers(base_url)
    cid = httpx.post(base_url + "/api/auth/register",
                     json={"username": "commco", "password": "secret1", "full_name": "Commercial Co"}).json().get("id")
    if cid:
        httpx.post(base_url + "/api/connections", headers=h, json={
            "customer_id": cid, "meter_no": "COMMTR9", "type": "COMMERCIAL", "address": "9 Market Road"})
    make_billed_customer(base_url, "domestic9", "DOMMTR9")
    login_as_admin(driver)
    open_page(driver, "customers")
    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "type-filter")))
    time.sleep(0.8)
    Select(driver.find_element(By.ID, "type-filter")).select_by_value("COMMERCIAL")
    rows = driver.find_element(By.ID, "customer-rows").text
    assert "Commercial Co" in rows and "Billed domestic9" not in rows
    shot(driver, "UI14_filter_commercial")
    Select(driver.find_element(By.ID, "type-filter")).select_by_value("DOMESTIC")
    rows = driver.find_element(By.ID, "customer-rows").text
    assert "Billed domestic9" in rows and "Commercial Co" not in rows


def test_TC_UI15_pages_have_no_caption_under_the_heading(driver, base_url):
    login_as_admin(driver)
    for page in ("dashboard", "customers", "readings", "bills", "payments", "complaints"):
        driver.find_element(By.ID, "nav-" + page).click()
        time.sleep(0.8)
        assert driver.find_elements(By.CSS_SELECTOR, ".lead") == [], page


def test_TC_UI16_reading_page_enables_billing_only_when_a_new_reading_exists(driver, base_url):
    make_billed_customer(base_url, "readcheck", "RDCHKMTR")     # has 2 readings and a bill already
    login_as_admin(driver)
    driver.find_element(By.ID, "nav-readings").click()
    row_btn = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".gen-btn[data-meter='RDCHKMTR']")))
    time.sleep(0.5)
    row_btn = driver.find_element(By.CSS_SELECTOR, ".gen-btn[data-meter='RDCHKMTR']")
    assert not row_btn.is_enabled()                              # already billed: nothing new to bill
    assert "Billed" in driver.find_element(By.ID, "reading-rows").text
    add_reading_ui(driver, "RDCHKMTR", 60)
    assert driver.find_element(By.CSS_SELECTOR, ".gen-btn[data-meter='RDCHKMTR']").is_enabled()   # new reading: ready to bill
    shot(driver, "UI16_readings_table")


# ---------------- dashboards ----------------
def test_TC_UI17_admin_dashboard_is_the_landing_page_with_essentials(driver, base_url):
    make_billed_customer(base_url, "dashadmin1", "DASHMTR1")          # leaves an unpaid bill of Rs 240
    login_as_admin(driver)
    nav = driver.find_element(By.ID, "nav-dashboard")
    assert "active" in nav.get_attribute("class")                      # landing page
    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "dash-outstanding")))
    time.sleep(0.5)
    assert driver.find_element(By.ID, "dash-outstanding").text.startswith("\u20b9")
    assert driver.find_element(By.ID, "dash-outstanding").text != "\u20b90.00"
    assert "Needs attention" in driver.find_element(By.ID, "view").text
    assert "Recent payments" in driver.find_element(By.ID, "view").text
    shot(driver, "UI17_admin_dashboard")


def test_TC_UI18_customer_dashboard_shows_amount_due_and_pays_from_there(driver, base_url):
    make_billed_customer(base_url, "dashcust", "DASHMTR2")
    login(driver, "dashcust", "secret1")
    wait_visible(driver, "app")
    assert "active" in driver.find_element(By.ID, "nav-dashboard").get_attribute("class")
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "dash-due"), "240.00"))
    shot(driver, "UI18a_customer_dashboard")
    driver.find_element(By.ID, "dash-pay").click()
    wait_visible(driver, "pay-modal")
    assert "\u20b9240.00" in driver.find_element(By.ID, "pay-total").text
    driver.find_element(By.ID, "confirm-ok").click()
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "view"), "all paid up"))
    assert driver.find_element(By.ID, "dash-due").text == "₹0.00"
    shot(driver, "UI18b_customer_all_paid")


def test_TC_UI19_dashboard_attention_link_opens_the_overdue_bills_filter(driver, base_url):
    # an overdue bill needs a past due date: record it through the API with old reading dates
    h = api_admin_headers(base_url)
    cid = httpx.post(base_url + "/api/auth/register",
                     json={"username": "latepayer", "password": "secret1", "full_name": "Late Payer"}).json()["id"]
    conn = httpx.post(base_url + "/api/connections", headers=h, json={
        "customer_id": cid, "meter_no": "LATEMTR1", "type": "DOMESTIC", "address": "3 Old Street"}).json()["id"]
    for value, day in ((10, "2026-01-01"), (30, "2026-02-01")):
        httpx.post(base_url + "/api/readings", headers=h, json={"connection_id": conn, "reading": value, "read_on": day})
    httpx.post(base_url + "/api/bills/generate", headers=h, json={"connection_id": conn})
    login_as_admin(driver)
    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "attention-list")))
    time.sleep(0.5)
    assert "overdue" in driver.find_element(By.ID, "attention-list").text
    driver.find_element(By.CSS_SELECTOR, "#attention-list .go-link[data-filter='OVERDUE']").click()
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "bill-rows"), "Overdue"))
    assert Select(driver.find_element(By.ID, "bill-filter")).first_selected_option.text == "Overdue"
    assert "Unpaid" not in driver.find_element(By.ID, "bill-rows").text


def test_TC_UI20_save_reading_and_generate_bill_in_one_step(driver, base_url):
    make_billed_customer(base_url, "onestep", "ONESTEP1")        # already billed: Generate bill is disabled
    login_as_admin(driver)
    open_page(driver, "readings")
    gen = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".gen-btn[data-meter='ONESTEP1']")))
    time.sleep(0.5)
    gen = driver.find_element(By.CSS_SELECTOR, ".gen-btn[data-meter='ONESTEP1']")
    assert not gen.is_enabled()
    assert "Add a new reading first" in gen.get_attribute("title")           # the reason is explained
    assert "waiting for next reading" in driver.find_element(By.ID, "reading-rows").text
    driver.find_element(By.CSS_SELECTOR, ".add-reading-btn[data-meter='ONESTEP1']").click()
    wait_visible(driver, "rd-modal")
    fill(driver, "m-read", 60)                                                # 25 kL since the last reading of 35
    shot(driver, "UI20_save_and_generate")
    driver.find_element(By.ID, "read-bill-btn").click()
    assert "generated" in text_of(driver, "toast", "generated")
    time.sleep(0.8)
    assert not driver.find_element(By.CSS_SELECTOR, ".gen-btn[data-meter='ONESTEP1']").is_enabled()   # billed again
    open_page(driver, "bills")
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "bill-rows"), "Billed onestep"))


# ---------------- branding, login wave, dashboard charts ----------------
def test_TC_UI21_login_page_shows_the_hydrocore_brand_and_wave(driver):
    assert driver.title == "HydroCore"
    assert driver.find_element(By.CSS_SELECTOR, ".auth-name").text == "HydroCore"
    assert driver.find_element(By.CSS_SELECTOR, ".auth-aside").is_displayed()          # brand panel beside the form
    assert driver.find_elements(By.CSS_SELECTOR, ".auth-logo svg use")                # the HydroCore mark, not a plain drop
    assert driver.find_element(By.CSS_SELECTOR, "label[for=l-user]").text == "Username"
    shot(driver, "UI21_login_wave")
    login_as_admin(driver)
    assert driver.find_element(By.CSS_SELECTOR, ".brand span").text == "HydroCore"
    assert "AquaBill" not in driver.page_source


def test_TC_UI22_dashboards_show_a_greeting_and_a_chart(driver, base_url):
    make_billed_customer(base_url, "chartcust", "CHARTMTR1")
    login_as_admin(driver)
    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#dash-chart svg rect")))
    assert driver.find_element(By.ID, "hero-title").text.startswith("Good ")
    assert len(driver.find_elements(By.CSS_SELECTOR, "#dash-chart svg rect")) == 12          # 6 months x (billed, collected)
    logout(driver)
    login(driver, "chartcust", "secret1")
    wait_visible(driver, "app")
    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#dash-chart svg rect")))
    assert "Billed" in driver.find_element(By.ID, "hero-title").text                          # greets by first name
    assert len(driver.find_elements(By.CSS_SELECTOR, "#dash-chart svg rect")) == 1            # one bill, one bar
    shot(driver, "UI22_customer_chart")
