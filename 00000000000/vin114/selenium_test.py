# coding=utf-8

from selenium import webdriver
import requests
import time

# 设置请求头
options = webdriver.ChromeOptions()
options.add_argument('User-Agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36"')

# 禁用GPU加速
options.add_argument('--disable-gpu')
driver = webdriver.Chrome(options=options)

# 浏览器窗口最大化
driver.maximize_window()

url = 'http://www.vin114.net/web/webmemberuser/login.jhtml'
username = '18474764360'
password = 'qwe123'

driver.get(url)

# 用户名密码输入
driver.find_element_by_xpath('.//input[@placeholder="已验证手机/邮箱/用户名"]').clear()
driver.find_element_by_xpath('.//input[@placeholder="已验证手机/邮箱/用户名"]').send_keys(username)
driver.find_element_by_xpath('.//input[@placeholder="请您填写登录密码"]').clear()
driver.find_element_by_xpath('.//input[@placeholder="请您填写登录密码"]').send_keys(password)

ok = input('是否正确输入验证码？(y/n)')
if ok == 'y':
    time.sleep(5)
    cookies_dict = {}
    cookies = driver.get_cookies()
    print(cookies)
    for i in cookies:
        cookies_dict[i['name']] = i['value']
    print(cookies_dict)
    # 成功登录后输入VIN点击搜索,并获取当前VIN的levelIds
    vin = 'LVGCV90328G003494'
    driver.find_element_by_xpath('.//input[@id="searchvalue"]').clear()
    driver.find_element_by_xpath('.//input[@id="searchvalue"]').send_keys(vin)
    time.sleep(0.5)
    driver.find_element_by_xpath('.//input[@id="searchbutton"]').click()
    time.sleep(2)
    levelIds = driver.find_element_by_xpath('.//input[@id="hdlevelIds"]')
    print(levelIds)
    levelIds = levelIds.get_attribute('value')
    print(levelIds)
else:
    exit()









