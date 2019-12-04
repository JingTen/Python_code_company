'''
雪佛兰低年款VIN查询EPC获取VIN_INFO

'''

from selenium import webdriver
import requests
import time

# 设置请求头
options = webdriver.ChromeOptions()
options.add_argument('x-resource-code="decodeVin"')
options.add_argument('User-Agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36"')

# 禁用GPU加速
#options.add_argument('--disable-gpu')
driver = webdriver.Chrome(chrome_options=options)

# 浏览器窗口最大化
driver.maximize_window()

# 链接登入
url = 'http://dp.saic-gm.com/dp/'
username = 'dn1zbp'
password = 'Xfl888888'


driver.get(url)
# 用户名密码输入
driver.find_element_by_xpath('.//input[@placeholder="用户名"]').clear()
driver.find_element_by_xpath('.//input[@placeholder="用户名"]').send_keys(username)
driver.find_element_by_xpath('.//input[@placeholder="密码"]').clear()
driver.find_element_by_xpath('.//input[@placeholder="密码"]').send_keys(password)

# 手动输入验证码并登入
time.sleep(15)

# 刷VIN接口
vin = 'LSGTB54M7AY038351'
vin_url = 'https://dpj.saic-gm.com/epcoloe4dealer/src/vinDecode.html?vin=%s' % vin

dealerSelect_url = 'https://dpj.saic-gm.com/epcoloe4dealer/src/index.html'
driver.get(dealerSelect_url)
time.sleep(3)

driver.find_element_by_class_name('btn-group').click()
time.sleep(3)

'''
# 模拟填入VIN并点击VIN解码
driver.find_element_by_id('vin').clear()
driver.find_element_by_id('vin').send_keys(vin)
driver.find_element_by_xpath('.//button[@ng-click="gotoVinDecode();"]').click()
print(driver.page_source)
print("-" * 40)
print(driver.page_source)
'''

driver.get('https://dpj.saic-gm.com/epcoloe4dealer/src/vinDecode.html?vin=LSGTB54M7AY038351')
time.sleep(5)

'''
driver.get('https://dpj.saic-gm.com/MidNodeJS/epcoloe4dealer/rest/vehicles/LSGTB54M7AY038351')
time.sleep(3)
print(driver.page_source)
'''

driver.get('https://dpj.saic-gm.com/MidNodeJS/epcoloe4dealer/rest/vehicles/LSGTB54M7AY038351')
time.sleep(3)
print(driver.page_source)










