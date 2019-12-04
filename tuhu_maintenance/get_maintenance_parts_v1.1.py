# coding:utf-8
'''
采集途虎养车（销售型+生产年份）条件下，各个销售型的所有匹配保养件信息
1.以销售型数据为具体参数，采集以下信息
    a.保养分类及项目描述（保养建议频率）
    b.保养具体项目 data_type,bytype_name,bytype,data_pid
2.依据以上参数，采集各销售型各生产年份下，各保养项目所能匹配的所有保养件信息

'''
import pymysql
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import urllib.parse
import time
from random import shuffle

############################### 函数封装 ###############################

# 查询销售型数据库，提供车型数据基础
def select_sales_year_from_MySQL(query_type='all'):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    if query_type == 'select':
        sql = '''
            SELECT DISTINCT 
                original_brand,brand,series_id,series,series2,series_factory,factory,displacement,product_year,tid,sales_name
            FROM `vehicle_power_class_and_sales`
            GROUP BY tid
            ORDER BY original_brand,series_id;'''
    elif query_type == 'all':
        sql = """
            SELECT DISTINCT 
                original_brand,brand,series_id,series,series2,series_factory,factory,displacement,product_year,tid,sales_name
            FROM `vehicle_power_class_and_sales`
            ORDER BY original_brand,series_id;"""
    else:
        print('请选择采集销售型数据基础！！！！！！！')
        return None
    cur.execute(sql)
    result = cur.fetchall()
    # 关闭连接
    cur.close()
    conn.close()

    result_list = []
    if result:
        for i in result:
            result_list.append(list(i))

    return result_list


# 销售车型所有保养项目示例商品信息，及保养频率信息（关键参数不正确或缺省时，返回空列表）
def get_example_products_info(Brand, VehicleId, PaiLiang, Nian, Tid, SalesName):
    # 访问的目标网址
    url = 'https://by.tuhu.cn/change/GetBaoYangPackages.html?vehicle={"Brand":"%s","VehicleId":"%s","PaiLiang":"%s","Nian":"%s","Tid":"%s","Properties":"null"}' % (
    Brand, VehicleId, PaiLiang, Nian, Tid)
    ########################
    # 处理带 + 号url
    url_1 = 'https://by.tuhu.cn/change/GetBaoYangPackages.html?vehicle='
    url_2 = '''{"Brand":"%s","VehicleId":"%s","PaiLiang":"%s","Nian":"%s","Tid":"%s","Properties":null}''' % (
    Brand, VehicleId, PaiLiang, Nian, Tid)
    url_2_trans = urllib.parse.quote(url_2, '/?=&() ')
    url_2_trans = url_2_trans.replace(' ', '+')
    url = url_1 + url_2_trans
    ########################
    # 设置请求头中的referer(需url中文转码)
    referer_zh = 'https://by.tuhu.cn/baoyang/%s/pl%s-n%s.html?tid=%s&salesName=%s' % (
    VehicleId, PaiLiang, Nian, Tid, SalesName)
    referer = urllib.parse.quote(referer_zh, ':/?=&()')
    # 设置请求头
    headers = {
        'accept-encoding': 'gzip, deflate, br',
        'accept': '*/*',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36',
        'referer': referer,
        # 'cookie': '_um_deti=1a66f4d8282142ec85686646027368a15;',
        'cookie': '_um_deti=2aae79979bd74e40b71d54a513ae2a306;'
    }
    # 用户名和密码(私密代理/独享代理)
    proxy = "39.97.170.201:16819"
    username = "841414840"
    password = "jhlahb8c"
    proxies = {
        "http": "http://%(user)s:%(pwd)s@%(proxy)s/" % {'user': username, 'pwd': password, 'proxy': proxy},
        "https": "http://%(user)s:%(pwd)s@%(proxy)s/" % {'user': username, 'pwd': password, 'proxy': proxy}
    }
    # 请求，若超时则重新请求
    r_num = 0
    while r_num < 10:
        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.close()
            # 请求返回结果文本字符串
            response_str = response.text
            # 处理NULL,false,true值
            response_str = response_str.replace('null', '""').replace('false', '"false"').replace('true', '"true"')
            # 转为列表形式(列表元素为三大保养分类的字典形式)
            response_list = eval(response_str)
            return url, referer, response_list
        # 超时，则等待后重新请求
        except requests.exceptions.RequestException:
            r_num += 1
            time.sleep(1)
        except:
            return None, None, None

    return None, None, None


# 解析销售车型所有保养项目示例商品信息，及保养频率信息
def analysis_example_products_info(example_products_info):
    '''
    传入示例产品response处理后结果列表，
    输出保养大小分类，保养项目及示例产品信息总列表
    '''
    maintenance_parts_and_example_products_list = []
    # 遍历三大保养分类（常规保养，深度保养，清洁保养）
    for i in example_products_info:
        CategoryType = i['CategoryType']  # 保养大分类
        CategoryName = i['CategoryName']  # 保养大分类名称
        SimpleCategoryName = i['SimpleCategoryName']  # 保养大分类简称
        Items_1 = i['Items']  # 保养大分类下所有小分类总列表，元素为字典
        # print(CategoryType,CategoryName,SimpleCategoryName)

        # 保养大分类下，遍历所有可能的保养项目（如常规保养下的小保养，空调滤清器等）
        for j in Items_1:
            PackageType = j['PackageType']  # 保养小分类
            PackageType_ZhName = j['ZhName']  # 保养小分类名称
            SuggestTip = j['SuggestTip']  # 保养建议
            BirefDescription = j['BirefDescription']  # 保养简述
            Items_2 = j['Items']  # 保养小分类下所有具体保养项目总列表，元素为字典
            # print(PackageType,PackageType_ZhName,SuggestTip,BirefDescription)

            # 保养小分类下，遍历所有具体保养项目（如小保养下的机油，机油滤清器）
            for k in Items_2:
                BaoYangType = k['BaoYangType']  # 保养项目
                BaoYangType_ZhName = k['ZhName']  # 保养项目名称
                DataTip = k['DataTip']  # 参考用量
                Products = k['Products']  # 保养项目下所有保养示例产品总列表，元素为字典
                # print(BaoYangType,BaoYangType_ZhName,DataTip)

                # 保养项目下，遍历所有保养示例产品
                for p in Products:
                    Product = p['Product']  # 保养示例产品信息
                    Oid = Product['Oid']
                    # Count = p['Count'] # 保养示例产品建议使用数量
                    # ProductId = Product['ProductId'] # 产品ID
                    Pid = Product['Pid']  # 示例产品ID + '|' + 序号
                    # print(CategoryType,CategoryName,SimpleCategoryName,PackageType,PackageType_ZhName,SuggestTip,BirefDescription,BaoYangType,BaoYangType_ZhName,DataTip,Pid)
                    maintenance_parts_and_example_products_list.append(
                        [CategoryType, CategoryName, SimpleCategoryName, PackageType, PackageType_ZhName, SuggestTip,
                         BirefDescription, BaoYangType, BaoYangType_ZhName, DataTip, Pid])
    return maintenance_parts_and_example_products_list

# 查询已采集的保养件使用库
def select_sales_vehicle_bytype_and_products():
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    sql = """
        SELECT DISTINCT original_brand,brand,series_id,series,series2,series_factory,factory,displacement,product_year,tid,sales_name
        FROM `sales_vehicle_bytype_and_products`;"""
    cur.execute(sql)
    result = cur.fetchall()
    # 关闭连接
    cur.close()
    conn.close()

    result_list = []
    if result:
        for i in result:
            result_list.append(list(i))

    return result_list

# 单项保养件所有商品信息抓取
def get_maintenance_parts(Brand, VehicleId, PaiLiang, Nian, Tid, SalesName, Vehicle, BaoYangType, pid):
    '''
    :param Brand: 带首部大写字母-品牌
    :param VehicleId: 车系ID
    :param PaiLiang: 排量
    :param Nian: 生产年份
    :param Tid: 销售车型ID
    :param SalesName: 销售车型ID
    :param Vehicle: 车系-厂商
    :param BaoYangType: 保养项目
    :param pid: 示例商品ID
    :return: 单项保养件所有商品字典
    '''
    # 设置请求头
    # referer设置
    referer_zh = 'https://by.tuhu.cn/baoyang/%s/pl%s-n%s.html?Tid=%s&SalesName=%s' % (VehicleId, PaiLiang, Nian, Tid, SalesName)
    referer = urllib.parse.quote(referer_zh, ':/?=&()')
    headers = {
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9",
        "x-requested-with": "XMLHttpRequest",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36",
        "origin": "https://by.tuhu.cn",
        "referer": referer
    }
    # data传参
    data = {
        "vehicle": '{"Brand":"%s","FuelType":"","Nian":"%s","OnRoadTime":"","PaiLiang":"%s","Properties":[],"SalesName":"%s","Tid":"%s","VehicleId":"%s","Vehicle":"%s"}' % (Brand,Nian,PaiLiang,SalesName,Tid,VehicleId,Vehicle),
        "baoyangType": "%s" % BaoYangType,
        "pid": "%s" % pid
    }
    # 目标网站
    url = "https://by.tuhu.cn/change/ChangeProduct.html"
    # 用户名和密码(私密代理/独享代理)
    proxy = "39.97.170.201:16819"
    username = "841414840"
    password = "jhlahb8c"
    proxies = {
        "http": "http://%(user)s:%(pwd)s@%(proxy)s/" % {'user': username, 'pwd': password, 'proxy': proxy},
        "https": "http://%(user)s:%(pwd)s@%(proxy)s/" % {'user': username, 'pwd': password, 'proxy': proxy}
    }

    # POST请求，若超时则等待后重新请求
    r_num = 0
    while r_num < 10:
        try:
            response = requests.post(url=url, headers=headers, data=data, timeout=20)
            # 硬等待
            # time.sleep(1)
            # 关闭
            response.close()
            response_str = response.text
            # 处理NULL值,false,true,并转为字典形式
            response_str = response_str.replace('null', '""').replace('false', '"false"').replace('true', '"true"')
            response_dict = eval(response_str)
            return url, referer, response_dict
        except requests.exceptions.RequestException:
            r_num += 1
            time.sleep(1)
        except:
            return None, None, None

    return None, None, None

# 单项保养件所有商品信息抓取后解析
def analysis_maintenance_parts(maintenance_parts_dict):
    # Data中包含所有页的保养产品信息,以页数为键，每页保养产品信息列表为值组成的字典
    all_data = maintenance_parts_dict['Data']
    # 初始化单项保养件商品总列表
    maintenance_parts_list = []
    # 判断是否存在保养件信息
    if all_data:
        for page, p_info in all_data.items():
            # 每个产品信息为字典形式
            for p_dict in p_info:
                Pid = p_dict['Pid'] # 商品ID
                DisplayName = p_dict['DisplayName'] # 商品显示名称
                PBrand = p_dict['Brand'] # 商品品牌

                PBrandImage = p_dict['BrandImage'] # 商品品牌图片
                PImage = p_dict['Image'] # 商品产品主图
                # 处理图片链接，修正为原始尺寸图片链接
                PBrandImage = PBrandImage[:PBrandImage.find('@')] if PBrandImage.count('@') == 1 else PBrandImage
                PImage = PImage[:PImage.find('@')] if PImage.count('@') == 1 else PImage

                Price = p_dict['Price'] # 商品价格
                Unit = p_dict['Unit'] # 商品单位
                IsOriginal = p_dict['IsOriginal'] # 商品是否属于原厂配件

                maintenance_parts_list.append([Pid, DisplayName, PBrand, PBrandImage, PImage, Price, Unit, IsOriginal])
    else:
        print('无保养件信息（）')

    return maintenance_parts_list

# 大表入库（最终成果表，包含车型参数，保养项目，商品详情）.
def sales_vehicle_bytype_and_products_insert_into_MySQL(lists):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    for one_new_line in lists:
        sql = '''
            INSERT INTO `sales_vehicle_bytype_and_products`
            (original_brand,brand,series_id,series,series2,series_factory,factory,displacement,product_year,tid,sales_name,
                CategoryType,CategoryName,SimpleCategoryName,PackageType,PackageType_ZhName,SuggestTip,BirefDescription,
                BaoYangType,BaoYangType_ZhName,DataTip,
                Pid,DisplayName,PBrand,PBrandImage,PImage,Price,Unit,IsOriginal)
            VALUES 
            {};
        '''.format(tuple(one_new_line))
        # print(sql)
        cur.execute(sql)

    # 提交，关闭
    conn.commit()
    cur.close()
    conn.close()

# 示例商品源码入库
def example_products_html_insert_into_MySQL(lists):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    sql = '''
        INSERT INTO `example_products_html`
        (Tid,Nian,url,referer,response)
        VALUES 
        {};
    '''.format(tuple(lists))
    cur.execute(sql)
    # 提交，关闭
    conn.commit()
    cur.close()
    conn.close()

# 单项保养项目所有商品源码入库
def products_html_insert_into_MySQL(lists):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    for one_new_products_html_line in lists:
        sql = '''
            INSERT INTO `products_html`
            (Tid,Nian,BaoYangType,example_pid,url,referer,response)
            VALUES 
            ('%s','%s','%s','%s','%s','%s',"""%s""");
        ''' % (one_new_products_html_line[0],
               one_new_products_html_line[1],
               one_new_products_html_line[2],
               one_new_products_html_line[3],
               one_new_products_html_line[4],
               one_new_products_html_line[5],
               str(one_new_products_html_line[6]))
        cur.execute(sql)

    # 提交，关闭
    conn.commit()
    cur.close()
    conn.close()

# 商品去重入库
def products_insert_into_MySQL(lists):
    # 先查询已存在商品信息
    exist_products_iofo_lists = select_products_from_MySQL()

    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    # 遍历采集商品结果列表，若不在已有商品数据库中，则入库
    for one_new_products_line in lists:
        if one_new_products_line[:-7] not in exist_products_iofo_lists:
            sql = '''
                INSERT INTO `products`
                (CategoryType,CategoryName,SimpleCategoryName,PackageType,PackageType_ZhName,SuggestTip,BirefDescription,
                    BaoYangType,BaoYangType_ZhName,DataTip,
                    Pid,DisplayName,PBrand,PBrandImage,PImage,Price,Unit,IsOriginal)
                VALUES 
                {};
            '''.format(tuple(one_new_products_line))
            cur.execute(sql)

    # 提交，关闭
    conn.commit()
    cur.close()
    conn.close()

# 查询已存在商品信息(忽略图片链接之后字段，因图片链接中img1-4替换得到的图片一致)
def select_products_from_MySQL():
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    sql = """
        SELECT 
            CategoryType,CategoryName,SimpleCategoryName,PackageType,PackageType_ZhName,SuggestTip,BirefDescription,
            BaoYangType,BaoYangType_ZhName,DataTip,Pid
        FROM `products`;
    """
    cur.execute(sql)
    conn.commit()
    result = cur.fetchall()
    cur.close()
    conn.close()

    # 处理查询结果为列表
    result_list = []
    if result:
        for i in result:
            result_list.append(list(i))
    return result_list

############################### 数据采集 ###############################

# 第一步，查销售型库
# 所有需要采集的销售型数据
sales_vehicle = select_sales_year_from_MySQL(query_type='all')
# 所有已经采集的销售型数据
exist_sales_vehicle = select_sales_vehicle_bytype_and_products()

print('需采集数量：%s;已采集数量：%s' % (len(sales_vehicle), len(exist_sales_vehicle)))
for i in exist_sales_vehicle:
    if i in sales_vehicle:
        sales_vehicle.remove(i)
print('现即将采集数量：%s' % len(sales_vehicle))

# 提取部分数据测试
# sales_vehicle = sales_vehicle[:50]

# 随机列表
# shuffle(sales_vehicle)

# 计数
count = 0

# print('开始遍历车型', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
# 遍历每个销售车型+生产年份
for single_sales_vehicel in sales_vehicle:
    time.sleep(1)
    count += 1

    # 初始化 每个销售车型+生产年份条件下所有保养大分类下小分类下保养项目下每条商品记录总列表
    new_line = []
    # 初始化 所有保养大分类下小分类下保养项目下每条商品记录总列表
    new_products_line = []
    # 初始化 每个销售车型+生产年份条件下所有保养大分类下小分类下保养项目下所有商品源码总列表
    new_products_html_line = []

    # 提取部分后续需要用到的车型参数
    Brand = single_sales_vehicel[0] # 带大写首字母品牌
    VehicleId = single_sales_vehicel[2] # 车系ID
    Series = single_sales_vehicel[3] # 车系名称
    Series2 = single_sales_vehicel[4] # 车系名称（宝马奔驰用）
    Factory = single_sales_vehicel[6] # 厂商
    PaiLiang = single_sales_vehicel[7] # 排量
    Nian = single_sales_vehicel[8] # 生产年份
    Tid = single_sales_vehicel[9] # 销售车型ID
    SalesName = single_sales_vehicel[10] # 销售车型名称
    # 车型名称-厂商
    if Series2:
        Vehicle = Series2 + '-' + Factory
    else:
        Vehicle = Series + '-' + Factory

    # print(Brand, VehicleId, PaiLiang, Nian, Tid, Vehicle)
    print('第%s条 <%s %s %s %s %s> 数据正在采集...' % (count, Brand, VehicleId, PaiLiang, Nian, Tid))

    # time.sleep(3)
    # print('开始获取示例商品信息', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    # 第二步，通过车型参数，获取销售车型所有保养项目示例商品信息（含保养频率信息）
    example_products_url, example_products_referer, example_products_info = get_example_products_info(Brand, VehicleId, PaiLiang, Nian, Tid, SalesName)
    if not example_products_info:
        print('第%s条 <%s %s %s %s %s> 数据获取示例商品信息出错！！！' % (count, Brand, VehicleId, PaiLiang, Nian, Tid))
        time.sleep(1)
        continue
    # print('开始解析示例商品信息', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    # 第三步，解析销售车型所有保养项目示例商品信息（含保养频率信息）
    analysis_example_products_lists = analysis_example_products_info(example_products_info)

    # 遍历每个示例商品，及其保养信息
    # [CategoryType, CategoryName, SimpleCategoryName, PackageType, PackageType_ZhName, SuggestTip, BirefDescription,
    #   BaoYangType, BaoYangType_ZhName, DataTip, Pid]
    # print('开始遍历样例数据', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    for every_example_products in analysis_example_products_lists:
        # time.sleep(1)
        # 第四步，传参，获取销售车型单项保养项目所有商品信息总列表
        BaoYangType = every_example_products[7]
        example_Pid = every_example_products[-1]
        maintenance_parts_url, maintenance_parts_referer, maintenance_parts_dict = get_maintenance_parts(Brand, VehicleId, PaiLiang, Nian, Tid, SalesName, Vehicle, BaoYangType, example_Pid)
        if not maintenance_parts_dict:
            print('第%s条 <%s %s %s %s %s> 数据获取商品信息 %s-%s 出错！！！' % (count, Brand, VehicleId, PaiLiang, Nian, Tid, BaoYangType, example_Pid))
            time.sleep(1)
            continue
        # 销售车型单项保养项目所有商品信息源码添加至总列表
        new_products_html_line.append([Tid, Nian, BaoYangType, example_Pid, maintenance_parts_url, maintenance_parts_referer, maintenance_parts_dict])

        # 第五步，解析销售车型单项保养项目所有商品信息
        analysis_maintenance_parts_list = analysis_maintenance_parts(maintenance_parts_dict)
        if not analysis_maintenance_parts_list:
            print('第%s条 <%s %s %s %s %s> 数据解析商品信息 %s-%s 出错！！！' % (count, Brand, VehicleId, PaiLiang, Nian, Tid, BaoYangType, example_Pid))
            continue
        # 遍历每个具体保养项目所有商品信息
        # [Pid, DisplayName, PBrand, PBrandImage, PImage, Price, Unit, IsOriginal]
        for products in analysis_maintenance_parts_list:
            new_line.append(single_sales_vehicel + every_example_products[:-1] + products)
            new_products_line.append(every_example_products[:-1] + products)
            # print([single_sales_vehicel + every_example_products + products])

    # print('开始入库', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    # 第六步，入库
    # 大表入库（最终成果表，包含车型参数，保养项目，商品详情）
    sales_vehicle_bytype_and_products_insert_into_MySQL(new_line)
    # 示例商品源码入库
    new_example_products_html_line = [Tid, Nian, example_products_url, example_products_referer, str(example_products_info)]
    example_products_html_insert_into_MySQL(new_example_products_html_line)
    # 单项保养项目所有商品源码入库
    products_html_insert_into_MySQL(new_products_html_line)
    # 商品去重入库
    products_insert_into_MySQL(new_products_line)
    # print('结束入库', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    print('第%s条 <%s %s %s %s %s> 数据采集成功！' % (count, Brand, VehicleId, PaiLiang, Nian, Tid))


















