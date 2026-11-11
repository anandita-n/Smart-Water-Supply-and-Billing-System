"""Selenium UI tests (Microsoft Edge, headless). Screenshots are saved to 07_Screenshots."""
import os
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
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402

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


def test_TC_UI01_invalid_login_shows_error(driver):
    login(driver, "admin", "wrong-password")
    assert "Invalid username or password" in text_of(driver, "auth-msg", "Invalid")
    shot(driver, "UI01_invalid_login")


def test_TC_UI02_bill_estimator(driver):
    fill(driver, "c-units", 25)
    driver.find_element(By.ID, "calc-btn").click()
    assert "Total: 240" in text_of(driver, "calc-out", "Total")
    shot(driver, "UI02_bill_estimator")


def test_TC_UI03_estimator_negative_units_rejected(driver):
    fill(driver, "c-units", -5)
    driver.find_element(By.ID, "calc-btn").click()
    assert text_of(driver, "calc-out", "greater") != ""
    shot(driver, "UI03_negative_units")


def test_TC_UI04_admin_login_shows_admin_panel(driver):
    login(driver, "admin", "admin123")
    WebDriverWait(driver, 8).until(EC.visibility_of_element_located((By.ID, "admin")))
    assert "ADMIN" in driver.find_element(By.ID, "who").text
    shot(driver, "UI04_admin_dashboard")


def test_TC_UI05_end_to_end_billing_and_payment(driver):
    # 1. customer registers
    fill(driver, "r-name", "Ravi Kumar")
    fill(driver, "r-user", "ravi")
    fill(driver, "r-pass", "secret1")
    driver.find_element(By.ID, "register-btn").click()
    msg = text_of(driver, "auth-msg", "Customer id")
    cust_id = msg.split(":")[-1].strip()
    # 2. admin creates connection, readings and bill
    login(driver, "admin", "admin123")
    WebDriverWait(driver, 8).until(EC.visibility_of_element_located((By.ID, "admin")))
    fill(driver, "a-cust", cust_id)
    fill(driver, "a-meter", "UIMTR1")
    fill(driver, "a-addr", "7 River View")
    driver.find_element(By.ID, "conn-btn").click()
    text_of(driver, "admin-msg", "Connection created")
    fill(driver, "m-conn", 1)
    fill(driver, "m-read", 50)
    driver.find_element(By.ID, "read-btn").click()
    text_of(driver, "admin-msg", "Reading saved")
    fill(driver, "m-read", 75)
    driver.find_element(By.ID, "read-btn").click()
    time.sleep(0.5)
    driver.find_element(By.ID, "gen-btn").click()
    assert "total: 240" in text_of(driver, "admin-msg", "Bill generated")
    shot(driver, "UI05a_bill_generated")
    # 3. customer logs in and pays
    driver.get(driver.current_url)
    login(driver, "ravi", "secret1")
    WebDriverWait(driver, 8).until(EC.visibility_of_element_located((By.ID, "bills")))
    row = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#bill-rows tr")))
    assert "UNPAID" in row.text
    row.find_element(By.TAG_NAME, "button").click()
    WebDriverWait(driver, 8).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#bill-rows .status"), "PAID"))
    shot(driver, "UI05b_bill_paid")
