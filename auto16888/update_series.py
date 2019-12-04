# coding=utf-8
'''车主之家车系更新(直接重新采集) '''
from bs4 import BeautifulSoup
import requests
import re
import pymysql

def series_info_insert_into_mysql(lists):
    '''车系信息存入数据库'''
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='auto16888', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE auto16888")
    for i in lists:
        sql = """INSERT INTO all_series
        (brand,brand_id,factory,factory_id,series,series_id,price,brand_4S_num,remarks) 
        VALUES 
        {};""".format(tuple(i))
        cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

def get_series_info():
    '''
    访问车主之家车型页面，并解析车系信息
    '''
    headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36'
    }
    url = 'https://auto.16888.com/'
    r = requests.get(url, headers=headers, timeout=10)
    bsObj = BeautifulSoup(r.text, 'html.parser')
    # 初始化车系结果列表
    all_series_lists = []
    brands = bsObj.find_all('div', {'class': 'brand_box'})
    for brand in brands:
        # 品牌信息提取
        brand_name = brand.find('a').attrs['name']
        brand_info = brand.find('div', {'class': 'brand_mane f_l'}).find_all('a')[-1]
        brand_4S_num = brand_info.get_text().replace(brand_name, '').replace('4S店', '').replace('家', '')
        brand_id = brand_info.attrs['href'].replace('https://dealer.16888.com/?tag=search&brandId=', '')
        # 品牌下厂商信息提取
        factorys_info = brand.find('div', {'class': 'brand_list f_r'}).find_all(re.compile('h1|ul'))
        for i in range(0, len(factorys_info), 2):
            # 厂商信息
            factory_name = factorys_info[i].find('a').get_text()
            factory_id = factorys_info[i].find('a').attrs['href'].replace('https://www.16888.com/f/', '').replace('/', '')
            # 厂商下车系信息
            series_info = factorys_info[i + 1].find_all('li')
            for series in series_info:
                # 车系名称，车系ID
                series_single_info = series.find('span', {'class': 'name'}).find('a')
                series_name = series_single_info.attrs['title']
                series_id = series_single_info.attrs['href'].replace('https://www.16888.com/', '').replace('/', '')
                # 价格
                price = series.find('p').get_text().replace('\xa0', '')
                # 备注
                if series_single_info.find('div') != None:
                    remarks = series_single_info.find('div')['title']
                else:
                    remarks = ''
                # 单挑车系信息存入总列表
                all_series_lists.append([brand_name, brand_id, factory_name, factory_id, series_name,
                                         series_id, price, brand_4S_num, remarks])
    return all_series_lists

all_series_lists = get_series_info()
series_info_insert_into_mysql(all_series_lists)