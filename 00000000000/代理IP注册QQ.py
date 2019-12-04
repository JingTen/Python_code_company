# coding:utf-8
'''
通用别克

IP限定地区：河南郑州（必须河南）

读取MySQL数据库表提取需要跑EPC的VIN及已经跑过EPC的VIN
得出需要但未跑EPC的VIN列表
遍历vin列表，刷EPC接口获取vininfo
存入MySql


'''

######################## 函数封装部分 ########################

import requests
import time
import pymysql
import traceback
from random import shuffle
import requests
import telnetlib
from selenium import webdriver
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
import traceback


# 连接数据库读取需要采集或已采集的vin列表
def get_vins_list_from_mysql(data_base, table, sql_select='vins_need_run'):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')

    cur = conn.cursor()

    cur.execute("USE %s" % data_base)

    # 判断是查询已采集VIN还是所有需采集VIN
    if sql_select == 'vins_need_run':
        sql = """SELECT vin FROM %s
        WHERE year_code IN ('6','7','8','9','A','B','C','D');""" % table
    if sql_select == 'vins_already_run':
        sql = """SELECT vin FROM %s;""" % table

    try:
        cur.execute(sql)

        result = cur.fetchall()

        conn.commit()

    finally:
        cur.close()
        conn.close()

    vins_list = []
    for vin in result:
        vins_list.append(vin[0])

    return vins_list


# 写入数据库
def insert_into_mysql(lists):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')

    cur = conn.cursor()

    cur.execute("USE gm_buick")

    try:
        sql = """INSERT INTO 
        epc_vin_info 
        (vin,content,insert_time) 
        VALUES 
        ('%s','%s','%s');""" % (lists[0], pymysql.escape_string(lists[1]), lists[2])

        # print(sql)

        cur.execute(sql)

        conn.commit()

    finally:
        cur.close()
        conn.close()


# selenium模拟登入获取cookie
def get_new_header(ip, port):
    # 设置请求头
    options = webdriver.ChromeOptions()
    options.add_argument('x-resource-code="decodeVin"')
    options.add_argument(
        'User-Agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36"')
    options.add_argument('--proxy-server=http://%s:%s' % (ip, port))

    driver = webdriver.Chrome(chrome_options=options)

    # 浏览器窗口最大化
    driver.maximize_window()

    # 链接登入
    url = 'http://dp.saic-gm.com/dp/'
    username = 'ddhd6b'
    password = 'Aa888888'

    driver.get(url)
    # 用户名密码输入
    driver.find_element_by_xpath('.//input[@placeholder="用户名"]').clear()
    driver.find_element_by_xpath('.//input[@placeholder="用户名"]').send_keys(username)
    driver.find_element_by_xpath('.//input[@placeholder="密码"]').clear()
    driver.find_element_by_xpath('.//input[@placeholder="密码"]').send_keys(password)

    # 手动输入验证码并登入
    time.sleep(15)

    # 手动点击至可需获取的cookies网页后，手动输入确认
    deal_with = input('Are you deal with that? (y/n)>>>>>>')

    if deal_with == 'y':
        pass

    cookie = driver.get_cookies()

    for i in cookie:
        name = i['name']
        if name == "SGM_OAUTH_CODE":
            SGM_OAUTH_CODE_value = i['value']
        elif name == "dealer_mid:prod:":
            dealer_mid_value = i['value']
    cookie_value = 'SGM_OAUTH_CODE=%s; dealer_mid:prod:=%s' % (SGM_OAUTH_CODE_value, dealer_mid_value)

    # 设置request headers
    headers = {
        'Host': 'dpj.saic-gm.com',
        'Connection': 'keep-alive',
        'x-resource-code': 'decodeVin',
        'x-app-version': '4.0.0.1',
        'oe-version-no': 'V4.0.0.1',
        'x-app-code': 'EPCOLOE',
        # 'x-track-code': 'fbd60425-37c5-441f-b9ab-efa2aebdd343',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'x-Requested-With': 'XMLHttpRequest',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cookie': 'SGM_OAUTH_CODE=72dc50111304a73714976211df30d6da; dealer_mid:prod:=1e2c4388-1cdb-47dc-b3d5-292f395a532b'
    }

    headers['Cookie'] = cookie_value

    return headers


# 通过vin刷EPC接口
def get_EPC_vin_info(vin, headers, ip, port):
    # 设置代理IP
    proxies = {
        'http': '%s:%s' % (ip, port),
        'https': '%s:%s' % (ip, port)
    }

    # 设置request headers

    # 接口URL
    url = 'https://dpj.saic-gm.com/MidNodeJS/epcoloe4dealer/rest/vehicles/%s' % vin

    response = requests.get(url, headers=headers, proxies=proxies, timeout=180, verify=False)

    content = response.text

    # 关闭连接
    response.close()

    return content

# 代理ip测试
def ip_test(ip, port):
    # 设置代理IP
    proxies = {
        'http': '%s:%s' % (ip, port),
        'https': '%s:%s' % (ip, port)
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36',
        'Accept': 'application/json, text/plain, */*'
    }

    # 测试URL
    url = 'https://www.hao123.com/'

    response = requests.get(url, headers=headers, proxies=proxies, timeout=3, verify=False)

    content = response.text

    # 关闭连接
    response.close()

    return content


# 采集成功与否记录写入txt文件
def records_txt(tips):
    records_file = open('buick_remarks.txt', 'a+')

    records_file.write(tips + '\n')

    records_file.close()


# 检验IP是否有效
def check_ip(ip, port):
    try:
        telnetlib.Telnet(ip, port, timeout=3)
        return True
    except:
        return False


# 程序报错发邮件提醒
def mail(error):
    my_sender = '841414840@qq.com'  # 发件人邮箱账号
    my_pass = 'gdwxjcdxamxgbedb'  # 发件人邮箱密码（授权码）
    my_user = '841414840@qq.com'  # 收件人邮箱账号，给自己发

    ret = True
    try:
        msg = MIMEText('%s' % error, 'plain', 'utf-8')
        msg['From'] = formataddr(["FromPython_Buick", my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        msg['To'] = formataddr(["FK", my_user])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject'] = "通用别克采集任务中断"  # 邮件的主题，也可以说是标题

        server = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 发件人邮箱中的SMTP服务器，端口是25
        server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(my_sender, [my_user, ], msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
    except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
        ret = False
    return ret


######################## 数据采集部分 ########################

# 必须为河南省IP!!!!!!!!
ip = "1.199.43.18"
port = "57114"

ip = "1.199.194.248"
port = "4251"

# 检测代理IP是否有效
ip_can_do_work = check_ip(ip, port)
if ip_can_do_work == False:
    print('IP无效，程序中断')
    exit()
else:
    print('IP有效')


# 测试代理IP是否能用
ip_content = ip_test(ip,port)
print(ip_content)
'''


# IP可用，获取代理IP下请求头
headers = get_new_header(ip, port)

# 查询数据库确定已采集及未采集数据
vins_need_run = get_vins_list_from_mysql('gm_buick', 'buick_vins')
vins_already_run = get_vins_list_from_mysql('gm_buick', 'epc_vin_info', 'vins_already_run')

print('需采集VIN数量：%s;已采集VIN数量：%s' % (len(vins_need_run), len(vins_already_run)))

# 剔除已经采集的VIN，剩下需要采集的VIN
for vin in vins_already_run:
    if vin in vins_need_run:
        vins_need_run.remove(vin)

# 随机排序剩余需要采集的VIN列表
shuffle(vins_need_run)
all_vins_num = len(vins_need_run)
print('现即将采集VIN数量：%s' % all_vins_num)

# 报错次数初始化
error_count = 0

# 逐个VIN刷接口并从列表中删除
for i in range(1, all_vins_num + 1):
    # 设置睡眠
    sleep_select = i % 50
    if sleep_select == 0:
        time.sleep(200)
    else:
        time.sleep(40)

    try:
        vin = vins_need_run.pop()
        content = get_EPC_vin_info(vin, headers, ip, port)

        # 实时存入MySQL
        insert_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        vin_info = [vin, content, insert_time]

        insert_into_mysql(vin_info)

        print('第%s条数据采集成功...' % i)

    except:

        error_count += 1
        print('第%s条数据采集失败！！！' % i)

        # 捕捉报错
        traceback.print_exc()
        error_reason = traceback.format_exc()

        # 发送报错信息至邮箱
        ret = mail(error_reason)
        if ret:
            print("邮件发送成功")
        else:
            print("邮件发送失败")

        time.sleep(300)

        # 三次连续报错则退出程序
        if error_count > 2:
            print('采集程序中断...')
            exit()

print("GAME OVER")
'''




