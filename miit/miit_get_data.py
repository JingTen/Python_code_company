# coding:utf-8
'''
抓取中国汽车燃料消耗量查询系统数据
网址：http://www.miit.gov.cn/asopCmsSearch/n2257/n2280/index.html
依据高级检索页面，所有选项选全部，依次遍历网页，获取燃料消耗信息，存入数据库
'''

import requests
import time
import pymysql

# ------------------------------ ↓ ↓ ↓ 函数定义部分 ↓ ↓ ↓ ------------------------------------- #

# 每页原始网页数据存储
def page_source_insert_into_MySQL(tuples):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE miit_gov_fuel_consumption")
    try:
        sql = """
            INSERT INTO `fuel_consumption_response` 
            (`url`,`page`,`response`) 
            VALUES
            {};""".format(tuples)
        # print(sql)
        cur.execute(sql)
        conn.commit()
    finally:
        cur.close()
        conn.close()


# 每条油耗数据存入数据库
def insert_into_MySQL(lists):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE miit_gov_fuel_consumption")
    data_tuple = tuple(lists)
    try:
        sql = """
            INSERT INTO `fuel_consumption_info` 
            (`市郊工况`,`车辆型号`,`生产企业`,`市区工况`,`综合工况`,`车辆种类`,`备案号`,`使用国家标准`,`通告日期`,`通用名称`,`最大设计总质量`,`实际录入时间`,`整车整备质量`,`驱动形式`,`变速器类型`,`发动机型号`,`额定功率`,`燃料类型`,`车辆品牌`,`车辆产地`,`备注`,`排量`) 
            VALUES{};
        """.format(data_tuple)

        cur.execute(sql)

    finally:
        conn.commit()
        cur.close()
        conn.close()

# ------------------------------ ↑ ↑ ↑ 函数定义部分 ↑ ↑ ↑ ------------------------------------- #

# ------------------------------ ↓ ↓ ↓ 快代理设置 ↓ ↓ ↓ ------------------------------------- #
# 快代理IP
proxy = "122.114.125.90:16819"
#用户名和密码(私密代理/独享代理)
username = "841414840"
password = "jhlahb8c"
proxies = {
    "http": "http://%(user)s:%(pwd)s@%(proxy)s/" % {'user': username, 'pwd': password, 'proxy': proxy},
    "https": "http://%(user)s:%(pwd)s@%(proxy)s/" % {'user': username, 'pwd': password, 'proxy': proxy}
}
# ------------------------------ ↑ ↑ ↑ 快代理设置 ↑ ↑ ↑ ------------------------------------- #

# 设置请求头
headers = {
    'Host': 'www.miit.gov.cn',
    'Connection': 'keep-alive',
    'Accept': 'text/javascript, application/javascript, */*',
    'x-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36',
    'Referer': 'http://www.miit.gov.cn/asopCmsSearch/n2257/n2280/index.html',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cookie': 'JSESSIONID=6B305E8AAF24D140A5AFFF086BD335AA; Hm_lvt_af6f1f256bb28e610b1fc64e6b1a7613=1569584885'
}

# 采集网站url结构：url = url_head + url_page + url_foot + url_time
url_head = "http://www.miit.gov.cn/asopCmsSearch/searchIndex.jsp?params=%257B%2522goPage%2522%253A"
url_foot = "%252C%2522orderBy%2522%253A%255B%257B%2522orderBy%2522%253A%2522pl%2522%252C%2522reverse%2522%253Afalse%257D%255D%252C%2522pageSize%2522%253A10%252C%2522queryParam%2522%253A%255B%257B%2522shortName%2522%253A%2522allRecord%2522%252C%2522value%2522%253A%25221%2522%257D%255D%257D&callback=jsonp"

# ------------------------------ ↓ ↓ ↓ 数据采集部分 ↓ ↓ ↓ ------------------------------------- #

# 第一步，获取总页数，遍历
all_page = 5114
start_page = 885

for url_page in range(start_page, all_page+1):
    # 设置等待时间
    time.sleep(30)

    # 程序访问网站时间转化
    url_time = int(round(time.time() * 1000))
    # 标准化url
    url = url_head + str(url_page) + url_foot + str(url_time)
    # 代理访问每页油耗网站
    try:
        response = requests.get(url=url, proxies=proxies, headers=headers, timeout=30)
        response.close()
    except:
        time.sleep(200)
        response = requests.get(url=url, proxies=proxies, headers=headers, timeout=30)

    # 正确返回结果时，处理油耗数据并存入数据库
    if response.status_code == 200:
        response = response.text.strip()

        # 第二步，原始网站信息存入数据库
        # 处理存入字段为元组形式（url,page,response）
        page_source_tuple = tuple([url, str(url_page), response])
        # 存入原始网站表
        page_source_insert_into_MySQL(page_source_tuple)

        # 第三步，处理原始网站信息为字典形式，并提取所有油耗记录
        response_dict = eval(response[19:-2])
        # 提取字典中的油耗信息
        page_info = response_dict['resultMap']
        # 插入数据库字段属性顺序列表
        # ['市郊工况','车辆型号','生产企业','市区工况','综合工况','车辆种类','备案号','使用国家标准','通告日期','通用名称','最大设计总质量','实际录入时间','整车整备质量','驱动形式','变速器类型','发动机型号','额定功率','燃料类型','车辆品牌','车辆产地','备注','排量']
        get_info_list =['sjgk','clxh','scqy','sqgk','zhgk','clzl','baID','sygjbz','tgrq','tymc','zdsjzzl','sjlrsj','zczbzl','qdxs','bsqlx','fdjxh','edgl','rllx','clpp','clcd','bz','pl']

        # 第四步，遍历每页油耗记录，整理存入每页结果列表
        # 初始化每页结果列表
        page_result_list = []
        # 遍历每页油耗信息，每条记录存入单个列表(字典形式提取键值)，并加入每页结果列表
        for single in page_info:
            # 初始化每条记录存储列表
            single_info_list = []
            # 遍历需要获取的属性值列表,存在时存入，否则存'-'
            for attr in get_info_list:
                if attr in single:
                    attr_value = single[attr]
                    single_info_list.append(attr_value)
                else:
                    single_info_list.append('-')
            page_result_list.append(single_info_list)

        # 第五步，采集的每页所有记录插入数据库
        for i in page_result_list:
            # print(i)
            insert_into_MySQL(i)

        print('第%d页油耗数据采集完毕...' % url_page)

    else:
        print('第%d页油耗数据采集失败！！' % url_page)
        time.sleep(300)






