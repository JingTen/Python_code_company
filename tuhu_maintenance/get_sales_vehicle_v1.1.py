# coding:utf-8
'''
依据已采集的车系级别数据，通过传参params访问途虎轮胎销售型选择页面
获取给定条件的每个生产年份下，允许存在的销售型

1.查询车系级别数据库，获取已经采集的车系信息
2.查询销售型级别数据库，获取已经采集的销售型信息
3.以上两步，得到需要采集的销售型传参
4.遍历传参访问，获取销售型结果
5.处理销售型结果，入库
'''

import pymysql
import requests
import time


# 查询车系级别数据库
def select_series_from_MySQL():
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    try:
        sql = """
            SELECT DISTINCT original_brand,brand,series_id,series,series2,series_factory,factory,displacement,product_year
            FROM `vehicle_power_class`
            WHERE displacement not in ('-')
            ORDER BY series_id,displacement,product_year;"""
        cur.execute(sql)
        result = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    result_list = []
    if result:
        for i in result:
            no_null_list = ['' if j == None else j for j in list(i)]
            result_list.append(no_null_list)

    return result_list

# 查询销售型级别数据库
def select_sales_from_MySQL():
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    try:
        sql = """
            SELECT DISTINCT original_brand,brand,series_id,series,series2,series_factory,factory,displacement,product_year
            FROM `vehicle_power_class_and_sales`
            ORDER BY series_id,displacement,product_year;"""
        cur.execute(sql)
        result = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    result_list = []
    if result:
        for i in result:
            result_list.append(list(i))
    return result_list

# 对比需要采集及已经采集的数据，得出需要采集的传参
def need_to_run_params(series_result, sales_result):
    if sales_result:
        for sales in sales_result:
            if sales in series_result:
                series_result.remove(sales)
        return series_result
    else:
        return series_result

# 传参访问，获取参数对应所有销售型数据
def get_sales_info(params):
    # 结果初始化
    result = []
    # 代理服务器
    proxy = "122.114.125.90:16819"
    # 用户名和密码(私密代理/独享代理)
    username = "841414840"
    password = "jhlahb8c"
    proxies = {
        "http": "http://%(user)s:%(pwd)s@%(proxy)s/" % {'user': username, 'pwd': password, 'proxy': proxy},
        "https": "http://%(user)s:%(pwd)s@%(proxy)s/" % {'user': username, 'pwd': password, 'proxy': proxy}
    }

    # 设置请求头
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }
    # 无参url
    url = 'https://item.tuhu.cn/Car/SelectVehicleSalesName?callback=__GetCarBrands__'
    # 尝试访问
    try:
        # response = requests.get(url,params=params,headers=headers,proxies=proxies)
        response = requests.get(url,params=params,headers=headers)
        if response.status_code == 200:
            response_str = response.text
            # 处理null值,处理前后多余字符串，并转为字典
            response_str = response_str.replace('null', '""').replace('__GetCarBrands__(', '')[:-1]
            response_dict = eval(response_str)
            # print(response_dict)
            # 判断是否返回销售型数据
            if 'SalesName' in response_dict:
                SalesVehicle = response_dict['SalesName']
                for sale in SalesVehicle:
                    LiYangID = sale['LiYangID']
                    TID = sale['TID']
                    SaleName = sale['Name']
                    result.append([TID, SaleName, LiYangID])
            else:
                print('%s传参有误' % params)
        else:
            print('%s访问失败' % params)
    finally:
        response.close()

    return result

# 销售型数据存入数据库
def sales_info_insert_into_MySQL(lists):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    # 处理None值
    lists_no_None = ['' if i == None else i for i in lists]
    try:
        sql = """
            INSERT INTO `vehicle_power_class_and_sales`
            (original_brand,brand,series_id,series,series2,series_factory,factory,displacement,product_year,tid,sales_name,liyang_id) 
            VALUES
            {};""".format(tuple(lists_no_None))
        cur.execute(sql)
        conn.commit()
    finally:
        cur.close()
        conn.close()



# 第一步，获取车系级别数据
series_result = select_series_from_MySQL()
# 第二步，获取销售型级别数据
sales_result = select_sales_from_MySQL()
# 第三步，比较第一二步，获取需要采集的传参数据
params_list = need_to_run_params(series_result, sales_result)

# 第四步，遍历传参访问，获取销售型结果
count = 0 # 计数
for i in params_list:
    # 硬等待
    time.sleep(5)

    count += 1
    # 初始化传参
    params = {
        "VehicleID": "",
        "PaiLiang": "",
        "Nian": "",
        "_": ""
    }
    # 传参设置
    params["VehicleID"] = i[2]
    params["PaiLiang"] = i[7]
    params["Nian"] = i[8]
    params['_'] = str(int(time.time()*1000))
    # 访问目标网址，获取销售型数据
    sales_result = get_sales_info(params)
    if sales_result:
        # 合并 车系级别数据 及 销售型数据，插入销售型数据库
        for j in sales_result:
            lists = i + j
            sales_info_insert_into_MySQL(lists)
            print('第%s条参数销售型数据插入完成' % count)
    else:
        print('第%s条参数销售型数据插入失败！！！！\n%s' % (count, params))
        time.sleep(1)
        continue


