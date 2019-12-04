# coding:utf-8
'''
读取vin.csv文件存为vin列表
遍历vin列表，刷EPC接口获取vininfo
存入MySql
'''

######################## 函数封装部分 ########################

import requests
import csv
import time
import pymysql
import traceback
from random import shuffle

# 连接数据库读取需要采集或已采集的vin列表
def get_vins_list_from_mysql(data_base, table, sql_select='vins_need_run'):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')

    cur = conn.cursor()

    cur.execute("USE %s" % data_base)

    # 判断是查询已采集VIN还是所有需采集VIN
    if sql_select == 'vins_need_run':
        sql = """SELECT vin FROM %s;""" % table
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

# 读取vin.csv文件（只有一列VIN数据）
def get_vin_from_csv(csvfile):
    vin_list  = []

    file = open(csvfile,'r')
    reader = csv.reader(file)

    for vin in reader:
        vin_list.append(vin[0])

    file.close()

    return vin_list

# 写入数据库
def insert_into_mysql(lists):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')

    cur = conn.cursor()

    cur.execute("USE gm_chevrolet")

    try:
        sql = """INSERT INTO 
        epc_vin_info 
        (vin,content,cookie,set_cookie,insert_time) 
        VALUES 
        ('%s','%s',"%s",'%s','%s');""" % (lists[0], pymysql.escape_string(lists[1]), lists[2], lists[3], lists[4])

        #print(sql)

        cur.execute(sql)

        conn.commit()

    finally:
        cur.close()
        conn.close()

# 通过vin刷EPC接口
def get_EPC_vin_info(vin):

    # 设置request headers
    headers = {
        'Host': 'dpj.saic-gm.com',
        'Connection': 'keep-alive',
        'x-resource-code': 'decodeVin',
        'x-app-version': '4.0.0.1',
        'oe-version-no': 'V4.0.0.1',
        'x-app-code': 'EPCOLOE',
        #'x-track-code': 'fbd60425-37c5-441f-b9ab-efa2aebdd343',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'x-Requested-With': 'XMLHttpRequest',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cookie': 'SGM_OAUTH_CODE=ceb42bf2804cc7cd5e34f730909898c3; dealer_mid:prod:=79e493c9-53d9-48f2-ba8b-77fc52e873e7'
    }

    # 接口URL
    url = 'https://dpj.saic-gm.com/MidNodeJS/epcoloe4dealer/rest/vehicles/%s' % vin

    response = requests.get(url,headers=headers)

    content = response.text

    cookie = response.cookies
    cookie_dict = requests.utils.dict_from_cookiejar(cookie)

    set_cookie = response.headers['Set-Cookie']

    return content, cookie_dict, set_cookie

# 采集成功与否记录写入txt文件
def records_txt(tips):
    records_file = open('xfl_remarks.txt', 'a+')

    records_file.write(tips + '\n')

    records_file.close()

######################## 数据采集部分 ########################

'''
# 第一步，读取csv文件存入vin列表
start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
print(start_time)
records_txt(start_time)
vins_need_run = get_vin_from_csv('xfl_yanzhengdate_.csv')
'''

# 查询数据库确定已采集及未采集数据
vins_need_run = get_vins_list_from_mysql('gm_chevrolet', 'chevrolet_vins')
vins_already_run = get_vins_list_from_mysql('gm_chevrolet', 'epc_vin_info', 'vins_already_run')

print('需采集VIN数量：%s;已采集VIN数量：%s' % (len(vins_need_run), len(vins_already_run)))

# 剔除已经采集的VIN，剩下需要采集的VIN
for vin in vins_already_run:
    if vin in vins_need_run:
        vins_need_run.remove(vin)

# 随机排序剩余需要采集的VIN列表
shuffle(vins_need_run)
all_vins_num = len(vins_need_run)
print('现即将采集VIN数量：%s' % all_vins_num)

# 第二步，遍历vin列表，刷EPC接口
count = 0 # 计数
for vin in vins_need_run:
    count += 1

    # 设置睡眠
    time.sleep(15)

    # 刷数据
    try:
        content, cookie_dict, set_cookie = get_EPC_vin_info(vin)

        # 第三步，实时存入MySql
        insert_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        vininfo = [vin, content, cookie_dict, set_cookie,insert_time]

        insert_into_mysql(vininfo)

        tip = "第%s条数据采集成功..." % count
        print(tip)
        records_txt(tip)

    except Exception as e:
        err = traceback.format_exc()
        end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

        print(err)
        print(end_time)
        records_txt(err)
        records_txt(end_time)




print('Game Over!')
