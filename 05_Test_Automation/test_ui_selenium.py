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
    assert menu == ["Customers", "Readings", "Bills", "Payments", "Complaints"]
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
    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "m-conn")))
    choose(driver, "m-conn", index=1)
    fill(driver, "m-read", 50)
    driver.find_element(By.ID, "read-btn").click()
    text_of(driver, "toast", "Reading saved")
    fill(driver, "m-read", 75)
    driver.find_element(By.ID, "read-btn").click()
    time.sleep(0.6)
    driver.find_element(By.ID, "gen-btn").click()
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
    assert menu == ["My bills", "Payments", "Complaints", "Estimate"]
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
    driver.find_element(By.ID, "cu-save").click()
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "complaint-rows"), "In progress"))
    shot(driver, "UI09b_admin_complaints")


def test_TC_UI10_customer_changes_password(driver, base_url):
    ensure_customer(base_url, "pwuser")
    login(driver, "pwuser", "secret1")
    wait_visible(driver, "app")
    driver.find_element(By.ID, "who").click()
    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "p-pass-btn")))
    fill(driver, "p-cur", "secret1")
    fill(driver, "p-new", "newsecret9")
    fill(driver, "p-new2", "different9")
    driver.find_element(By.ID, "p-pass-btn").click()
    assert "do not match" in text_of(driver, "p-pass-msg", "match")
    fill(driver, "p-new2", "newsecret9")
    driver.find_element(By.ID, "p-pass-btn").click()
    assert "Password changed" in text_of(driver, "p-pass-msg", "Password changed")
    shot(driver, "UI10_profile")
    logout(driver)
    login(driver, "pwuser", "newsecret9")
    wait_visible(driver, "app")


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
