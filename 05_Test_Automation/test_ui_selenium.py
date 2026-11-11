"""Selenium UI tests (Microsoft Edge, headless). Screenshots are saved to 07_Screenshots."""
import os
import re
import socket
import threading
import time

import pytest
import uvicorn

pytestmark = pytest.mark.ui
selenium = pytest.importorskip("selenium")
from selenium import webdriver  # noqa: E402
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
    d.find_element(By.ID, "nav-" + name).click()


def logout(d):
    d.find_element(By.ID, "logout-btn").click()
    wait_visible(d, "auth-screen")


def test_TC_UI01_invalid_login_shows_error(driver):
    login(driver, "admin", "wrong-password")
    assert "Invalid username or password" in text_of(driver, "auth-msg", "Invalid")
    shot(driver, "UI01_login_screen_error")


def test_TC_UI02_bill_estimator(driver):
    login_as_admin(driver)
    open_page(driver, "estimator")
    fill(driver, "c-units", 25)
    driver.find_element(By.ID, "calc-btn").click()
    assert "Total: \u20b9240.00" in text_of(driver, "calc-out", "Total")
    shot(driver, "UI02_bill_estimator")


def test_TC_UI03_estimator_negative_units_rejected(driver):
    login_as_admin(driver)
    open_page(driver, "estimator")
    fill(driver, "c-units", -5)
    driver.find_element(By.ID, "calc-btn").click()
    assert "greater than or equal to 0" in text_of(driver, "calc-out", "greater")
    shot(driver, "UI03_negative_units")


def test_TC_UI04_admin_login_shows_admin_menu(driver):
    login_as_admin(driver)
    assert driver.find_element(By.ID, "who").text == "System Administrator"
    assert driver.find_element(By.ID, "role-label").text.lower() == "admin"
    assert driver.find_element(By.ID, "nav-customers").is_displayed()
    shot(driver, "UI04_admin_overview")


def test_TC_UI05_end_to_end_billing_and_payment(driver):
    # 1. customer registers from the Create account tab
    driver.find_element(By.ID, "tab-register").click()
    fill(driver, "r-name", "Ravi Kumar")
    fill(driver, "r-user", "ravi")
    fill(driver, "r-pass", "secret1")
    driver.find_element(By.ID, "register-btn").click()
    cust_id = re.search(r"customer id is: (\d+)", text_of(driver, "auth-msg", "customer id")).group(1)
    # 2. admin creates a connection, records two readings and generates the bill
    driver.find_element(By.ID, "tab-login").click()
    login_as_admin(driver)
    open_page(driver, "customers")
    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "a-cust")))
    Select(driver.find_element(By.ID, "a-cust")).select_by_value(cust_id)
    fill(driver, "a-meter", "UIMTR1")
    fill(driver, "a-addr", "7 River View")
    driver.find_element(By.ID, "conn-btn").click()
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.ID, "customer-rows"), "UIMTR1"))
    open_page(driver, "readings")
    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "m-conn")))
    Select(driver.find_element(By.ID, "m-conn")).select_by_index(1)
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
    row = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#bill-rows tr")))
    assert "UNPAID" in row.text
    row.find_element(By.CSS_SELECTOR, ".pay-btn").click()
    wait_visible(driver, "pay-modal")
    assert "\u20b9240.00" in driver.find_element(By.ID, "pay-total").text
    shot(driver, "UI05b_payment_dialog")
    driver.find_element(By.ID, "confirm-ok").click()
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#bill-rows .status"), "PAID"))
    shot(driver, "UI05c_bill_paid")


def test_TC_UI06_logout_returns_to_login_and_session_is_gone(driver):
    login_as_admin(driver)
    logout(driver)
    driver.refresh()
    wait_visible(driver, "auth-screen")
    assert not driver.find_element(By.ID, "app").is_displayed()


def test_TC_UI07_customer_does_not_see_admin_menu(driver):
    login(driver, "ravi", "secret1")
    wait_visible(driver, "app")
    assert driver.find_elements(By.ID, "nav-customers") == []
    assert driver.find_elements(By.ID, "nav-readings") == []
    assert driver.find_element(By.ID, "nav-bills").is_displayed()
    shot(driver, "UI07_customer_dashboard")
