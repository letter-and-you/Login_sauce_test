import time
import pickle
import pytest
import yaml
import os
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


@pytest.fixture(scope="module")
def driver():
    driver = webdriver.Edge()
    WebDriverWait(driver, 10)
    driver.maximize_window()
    yield driver
    time.sleep(2)
    driver.quit()


# 获取datas目录的路径
def get_datas_path():
    # 获取当前脚本所在目录（sauce_test的目录）
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 获取父目录（pytest_test_selenium目录）
    parent_dir = os.path.dirname(current_dir)
    data_path = os.path.join(parent_dir, "datas")
    return data_path


# 获取cookies目录的路径
def get_cookies_path():
    datas_dir = get_datas_path()
    cookies_path = os.path.join(datas_dir, "cookies.pkl")
    return cookies_path


# 加载yaml文件
def load_yaml():
    datas_dir = get_datas_path()
    yaml_path = os.path.join(datas_dir, "sauce_logindata.yaml")
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data

#获取测试数据
login_data = load_yaml()
positive_cases = login_data["positive_login_cases"]
negative_cases = login_data["negative_login_cases"]


class Testlogin:

    @pytest.fixture(autouse=True)
    def setup(self, driver):
        self.driver = driver
    #正例测试
    @pytest.mark.parametrize("case_data", positive_cases)
    def test_positive_login(self, case_data):
        # 传入账号密码
        uname = case_data["username"]
        pd = case_data["passwd"]
        decr = case_data["description"]
        # 登录操作
        login_success = login_action(self.driver, uname, pd)
        assert login_success, f"正例测试：{decr}失败"
        if login_success:
            # 登录成功后保存cookie
            pickle.dump(self.driver.get_cookies(), open(get_cookies_path(), "wb"))
            # 登录成功后退出登录，进行下一次登录测试
            self.driver.get("https://www.saucedemo.com/")
    #反例测试
    @pytest.mark.parametrize("case_data", negative_cases)
    def test_negative_login(self, case_data):
        # 传入账号密码
        uname = case_data["username"]
        pd = case_data["passwd"]
        decr = case_data["description"]
        # 登录操作
        login_success = login_action(self.driver, uname, pd)
        assert not login_success, f"反例测试:{decr}失败"
        # 登录成功后退出登录，进行下一次登录测试
        self.driver.get("https://www.saucedemo.com/")


def login_action(driver, username, password):
    driver.get("https://www.saucedemo.com/")
    # 输入用户名/账号
    input_user = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "user-name")))
    input_user.send_keys(username)
    # 输入密码
    input_pw = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "password")))
    input_pw.send_keys(password)
    # 点击登录
    input_submit = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "login-button")))
    input_submit.click()
    # 判断是否登录成功
    try:
        title = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "app_logo")))
        assert title.text == "Swag Labs", "正常登录并成功保存cookie"
        # 登录成功保存cookie
        return True
    except:
        try:
            error_msg = WebDriverWait(driver, 3).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#login_button_container > div > form > div.error-message-container.error > h3")))
            assert error_msg.is_displayed(), "登录失败，提示信息显示"
            print(f"登录失败，提示信息：{error_msg.text}")
            return False
        except:
            assert False, "登录失败，出现未知问题"
            return False


def test_cookie_login(driver):
    try:
        # 先尝试用cookie登录,看能不能记住已登录状态，直接访问商品页面
        driver.get("https://www.saucedemo.com/inventory.html")
        # 加载cookie
        cookies = pickle.load(open(get_cookies_path(), "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        # 刷新页面应用cookie
        driver.refresh()
        # 检查商品页面是否存在，即是否登录成功
        inventory = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "inventory_container"))
        )
        assert inventory.is_displayed(), "cookie登录后成功显示商品页面"
    except:
        assert "cookie登录失败,进行正常登录"
        # 如果cookie登录失败，进行正常登录
        # 遍历所有测试数据进行尝试登录
        for case_data in positive_cases:
            uname = case_data["username"]
            pd = case_data["passwd"]
            login_success = login_action(driver, uname, pd)
            if login_success:
                print(f"使用账号{uname}通过正常登录成功,已保存cookie")
                # 登录成功后保存cookie
                pickle.dump(driver.get_cookies(), open(get_cookies_path(), "wb"))
                break
        else:
            assert False, "所有账号均登录失败,无法通过正常登录获取cookie"

