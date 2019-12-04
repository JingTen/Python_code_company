# conding:utf-8
'''
车主之家销量数据更新
依据年月获取最新数据
'''

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import random
from bs4 import BeautifulSoup
import re
import pymysql
import requests
import copy


# -----------------------------------函数封装部分-----------------------------------

# 无头浏览器获取bsObj
def PhantomJS_get_bsObj(series_id):
    url = 'https://xl.16888.com/s/%s/' % series_id
    # 设置PhantomJS请求头
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36")
    driver = webdriver.PhantomJS(desired_capabilities=dcap)
    driver.implicitly_wait(20)
    driver.get(url)
    # 随机睡眠
    time.sleep(random.random() + 3)
    pageSource = driver.page_source
    bsObj = BeautifulSoup(pageSource, 'lxml')
    driver.close()
    return bsObj

# 获取指定车系的销量首页
def get_sales_by_series_id(series_id):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36'
    }
    url = 'https://xl.16888.com/s/%s/' % series_id
    bsObj = ''
    try:
        r = requests.get(url, headers=headers, timeout=10)
    except:
        print('%s - 访问失败！' % url)
    else:
        r.close()
        if r.status_code == 200:
            r = requests.get(url, headers=headers, timeout=10)
            bsObj = BeautifulSoup(r.text, 'lxml')
        else:
            print('%s - 未正常返回！' % url)
    return bsObj

# 获取车主之家所有车系ID
def get_series_id_list(bsObj):
    cs = bsObj.find_all(lambda tag: tag.has_attr("href") and tag.has_attr("target") and tag.has_attr('title'))
    series_id_list = []
    for i in cs:
        if "https://www.16888.com/" in i['href']:
            series_id = i['href'][22:-1]
            series_id_list.append(series_id)
    return series_id_list

# 获取最大页数
def get_total_page(bsObj):
    pageObj = bsObj.find('div', {'class': 'xl-data-pageing lbBox'})
    if pageObj == None:
        print('无销量记录')
        pages = 0
    else:
        # 总页数:以下表达式在只有一页销量数据时报错
        # last_page = int(bsObj.find_all('a',{'class':'lineBlock num'})[-1].get_text())
        # 总数量计算总页数
        count_num = bsObj.find('span', {'class': 'lineBlock va-m'}).get_text()
        count_num = int(re.findall(re.compile(r'\d{1,}'), count_num)[0])
        # 判断总数量是否能被50整除，余数不为零时候，总页数为整除后+1
        if count_num % 50 == 0:
            pages = count_num // 50
        else:
            pages = count_num // 50 + 1
    return pages

# 获取品牌；厂商；车型名称及ID
def get_brandANDfirmANDseries(bsObj):
    info = bsObj.find_all('a', {'class': 'select-text selected'})
    info_list = []
    for i in info:
        id = i['data-bid']
        info_list.append(id)
        info_list.append(i.find('span').get_text())
    if "选择品牌" in info_list or "选择厂商" in info_list or "选择车型" in info_list:
        print("此车系无销量数据")
        return None
    return info_list

# 获取每页底层表单数据
def get_tbody(bsObj, info_list):
    # ['品牌ID','品牌','厂商ID','厂商','车系ID','车系','年月','月销量','当月销量排名','占厂商份额','在厂商排名','在车身类别中排名','车身类别']
    # 初始化每页年月销量记录
    y_m_xl_page_list = []
    # 获取销量数据
    tr_list = bsObj.find('tbody').find_all('tr')[1:]
    car_body = bsObj.find('tbody').find('tr').find_all('th')[-1].get_text()
    car_body = car_body.replace('在', '').replace('排名', '')
    # 完整记录填入列表
    for i in tr_list:
        td_list = i.find_all('td')
        # 初始化每条年月销量记录
        # y_m_xl_list = []
        y_m_xl_list = info_list[:]
        for j in td_list:
            data = j.get_text()
            y_m_xl_list.append(data)
        y_m_xl_list.append(car_body)
        y_m_xl_page_list.append(y_m_xl_list)
    return y_m_xl_page_list

# 获取固定（最新）年月销量底层表单数据
def get_year_month_tbody(bsObj, info_list):
    # ['品牌ID','品牌','厂商ID','厂商','车系ID','车系','年月','月销量','当月销量排名','占厂商份额','在厂商排名','在车身类别中排名','车身类别']
    # 初始化每页年月销量记录
    y_m_xl_page_list = []
    # 车身名称获取
    car_body = bsObj.find('tbody').find('tr').find_all('th')[-1].get_text()
    car_body = car_body.replace('在', '').replace('排名', '')
    # 获取页面销量数据
    tr_list = bsObj.find('tbody').find_all('tr')[1:]
    for i in tr_list:
        td_list = i.find_all('td')
        # 初始化每条年月销量记录
        y_m_xl_list = copy.deepcopy(info_list)
        for j in td_list:
            data = j.get_text()
            y_m_xl_list.append(data)
        y_m_xl_list.append(car_body)
        y_m_xl_page_list.append(y_m_xl_list)
    return y_m_xl_page_list

# 更新写入数据库
def insert_into_mysql(lists):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='auto16888', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE auto16888")
    # 先查询以入库的车系ID与销量年月
    select_sql = '''
        SELECT 车系ID,年月 FROM `car_sales_volume`;
    '''
    cur.execute(select_sql)
    had_data_result = cur.fetchall()
    had_data_list = []
    for had_data in had_data_result:
        had_data_list.append(list(had_data))
    # 判断是否更新入库
    for data in lists:
        if [data[4], data[6]] not in had_data_list:
            sql = """INSERT INTO car_sales_volume 
            (品牌ID,品牌,厂商ID,厂商,车系ID,车系,年月,月销量,当月销量排名,占厂商份额,在厂商排名,在车身类别中排名,车身类别) 
            VALUES 
            {};""".format(tuple(data))
            cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

# 获取所有车系ID
def select_series_from_mysql(table_name):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='auto16888', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE auto16888")
    sql = '''
        SELECT DISTINCT series_id FROM {};
    '''.format(table_name)
    cur.execute(sql)
    conn.commit()
    series_result =cur.fetchall()
    cur.close()
    conn.close()
    series_list = []
    for i in series_result:
        series_list.append(i[0])
    return series_list


# -----------------------------------数据采集部分-----------------------------------

# 第一步，数据库获取所有车主之家车系ID
series_list = select_series_from_mysql('all_series')
old_series_list = select_series_from_mysql('all_series_old')
new_list = list(set(series_list) - set(list(old_series_list)))
series_count = len(new_list)
# 车系ID列表升序排序
new_list.sort()
# series_id_list = ['57872', '128207']
# 第二步，遍历车系ID获取销量数据
count = 0
for series_id in new_list:
    count += 1
    print('%s 第%s条(共%s条)销量数据正在采集...' % (series_id, count, series_count))
    bsObj = PhantomJS_get_bsObj(series_id)
    time.sleep(2)
    if bsObj:
        info_list = get_brandANDfirmANDseries(bsObj)
        if info_list:
            y_m_xl_page_list = get_year_month_tbody(bsObj, info_list)
            # 第三步，存入数据库
            insert_into_mysql(y_m_xl_page_list)
            print('第%s条(共%s条)销量数据更新成功！！' % (count, series_count))

