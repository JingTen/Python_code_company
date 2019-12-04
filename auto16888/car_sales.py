from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import random
from bs4 import BeautifulSoup
from urllib.request import urlopen
import re
import pymysql


# -----------------------------------函数封装部分-----------------------------------


# 无头浏览器获取bsObj
def PhantomJS_get_bsObj(url):
    # 设置PhantomJS请求头
    dcap = dict(DesiredCapabilities.PHANTOMJS)

    dcap["phantomjs.page.settings.userAgent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36")

    driver = webdriver.PhantomJS(desired_capabilities=dcap)

    driver.get(url)

    # 随机睡眠
    time.sleep(random.random() + 3)

    pageSource = driver.page_source

    bsObj = BeautifulSoup(pageSource, 'lxml')

    driver.close()

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
        print("未成功获取")

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


# 写入数据库
def insert_into_mysql(lists):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')

    cur = conn.cursor()

    cur.execute("USE auto16888")

    try:
        for i in lists:
            sql = """INSERT INTO 
            car_sales_volume 
            (品牌ID,品牌,厂商ID,厂商,车系ID,车系,年月,月销量,当月销量排名,占厂商份额,在厂商排名,在车身类别中排名,车身类别) 
            VALUES 
            ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');""" % (
            i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9], i[10], i[11], i[12])

            cur.execute(sql)

            conn.commit()

    finally:
        cur.close()
        conn.close()


# -----------------------------------数据采集部分-----------------------------------

# 第一步，获取所有车主之家车系ID
url = "https://auto.16888.com/"

bsObj = PhantomJS_get_bsObj(url)

series_id_list = get_series_id_list(bsObj)

# 车系ID列表升序排序
series_id_list.sort()
print("车系ID范围：%s---%s" % (series_id_list[0], series_id_list[-1]))

# 第二步，遍历车系ID获取销量数据
for series_id in series_id_list:

    # 每个车系的销售记录首页URL
    series_id_first_url = "https://xl.16888.com/s/%s/" % series_id

    # 获取总页数
    bsObj = PhantomJS_get_bsObj(series_id_first_url)
    total_page = get_total_page(bsObj)

    # 第三步，遍历每页，提取车系销量数据
    if total_page == 0:
        print("车系ID:%s--当前无任何销量数据" % series_id)

    else:
        for page in range(1, total_page + 1):

            series_id_url = "https://xl.16888.com/s/%s-%s.html" % (series_id, page)

            try:
                bsObj = PhantomJS_get_bsObj(series_id_url)

                info_list = get_brandANDfirmANDseries(bsObj)

                y_m_xl_page_list = get_tbody(bsObj, info_list)

                # 第四步，存入MySQL
                insert_into_mysql(y_m_xl_page_list)

                print("%s第%s页（共%s页）销量记录采集完成" % (series_id, page, total_page))

            except:
                print("链接：%s采集报错" % series_id_url)


