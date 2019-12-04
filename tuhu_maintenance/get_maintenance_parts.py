# coding:utf-8
'''
采集途虎养车（销售型+生产年份）条件下，各个销售型的所有匹配保养件信息
0.以销售型数据为具体参数，采集以下信息
    1.保养分类及项目描述（保养建议频率）
    2.保养具体项目 data_type,bytype_name,bytype,data_pid
3.依据以上参数，采集各销售型各生产年份下，各保养项目所能匹配的所有保养件信息

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
def select_sales_year_from_MySQL():
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    sql = """
        SELECT DISTINCT original_brand,brand,series_id,series,series2,series_factory,factory,displacement,product_year,tid,sales_name
        FROM `vehicle_power_class_and_sales`;"""
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

# 保养项目频率等相关信息
def maintenance_frequency(Brand,VehicleId,PaiLiang,Nian,Tid,):
    # 目标网址
    url = '''https://by.tuhu.cn/change/GetBaoYangPackageDescription.html?vehicle={"Brand":"%s","VehicleId":"%s","PaiLiang":"%s","Nian":"%s","Tid":"%s","Properties":"null"}''' % (Brand, VehicleId, PaiLiang, Nian, Tid)
    headers = {
        "authority": "by.tuhu.cn",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36",
    }
    response = requests.get(url, headers=headers,verify=False)
    response_str = response.content.decode('utf-8')
    # 处理NULL,false,true值
    response_str = response_str.replace('null', '""').replace('false', '"false"').replace('true', '"true"')
    # 转为列表形式(列表元素为三大保养分类的字典形式)
    response_list = eval(response_str)
    # 关闭
    response.close()

    # 解析出保养项目的描述、保养频率
    # 重置以data-type为键的字典，方便后续提取
    data_type_dict = {}
    for category_dict in response_list:
        # 提取保养类别
        CategoryType = category_dict['CategoryType']
        # 提取保养类别名称
        CategoryName = category_dict['CategoryName']
        SimpleCategoryName = category_dict['SimpleCategoryName']
        # 提取保养类别下需要做的具体保养项目信息（列表形式，元素为字典形式的各个具体保养项目）
        Items = category_dict['Items']
        for package in Items:
            # 提取保养项目 PackageType（相当于data-type）
            PackageType = package['PackageType']
            # 提取保养项目中文名
            ZhName = package['ZhName']
            # 提取保养简述
            BirefDescription = package['BirefDescription']
            # 提取保养建议
            SuggestTip = package['SuggestTip']
            # 提取详细说明
            DetailDescription = package['DetailDescription']
            # 是否紧急
            IsVeryUrgent = package['IsVeryUrgent']
            # 推荐文本
            RecommendText = package['RecommendText']
            data_type_dict[PackageType] = {
                'ZhName': ZhName,
                'CategoryType': CategoryType,
                'CategoryName': CategoryName,
                'SuggestTip': SuggestTip,
                'BirefDescription': BirefDescription,
                'IsVeryUrgent': IsVeryUrgent,
                'DetailDescription': DetailDescription,
                'RecommendText': RecommendText
            }
    return data_type_dict

# 解析小保养、所有保养HTML,提取data_type,bytype,data_pid
def analysis_maintenance_HTML(byHTML):
    '''
    :param byHTML: 保养项目表格的源码（字符串形式）
    :return: [[data_type,bytype,bytype_name,data_pid],[...],...]
    '''
    # 端碗美味的汤，解析byHTML
    bsObj = BeautifulSoup(byHTML, 'lxml')

    #初始化所有保养信息[data_type,bytype,bytype_name,data_pid]总列表
    byHTML_result = []

    # 所有保养项目列表
    data_types = bsObj.find_all('div', {'class': 'packageService open'})
    for data_type in data_types:
        # data-type
        single_data_type = data_type.attrs['data-type']
        # data-type下所有BaoYangType列表
        all_BaoYangType = data_type.find_all('tr')
        for BaoYangType in all_BaoYangType:
            # 每个BaoYangType下有两个td标签，第一个包含bytype信息，第二个包含pid信息
            td = BaoYangType.find_all('td')
            bytype = td[0].find('div', {'class': 'BaoYangType'}).attrs['bytype']
            bytype_name = td[0].find('p').get_text().strip()
            data_pids = td[1].find_all('div', {'class': 'data_pid'})
            # data_pids为空时，表明销售型无此保养项目，忽略即可
            if data_pids:
                for data_pid in data_pids:
                    single_data_pid = data_pid.attrs['data_pid']
                    byHTML_result.append([single_data_type, bytype, bytype_name, single_data_pid])

    return byHTML_result

# 模拟浏览器访问具体销售型，遍历点击所有保养项目
def get_bytype_and_dataPid(VehicleId,PaiLiang,Nian,Tid,SalesName):
    '''
    :param VehicledId: 车系IDget_bytype_and_dataPid
    :param PaiLiang: 排量
    :param Nian: 生产年份
    :param Tid: 销售车型ID
    :param SalesName: 销售型名称
    :return: url_zh,xbyHTML,allHTML,HTML_analysis
            中文网址，小保养源码，所有保养源码(小保养除外),所有保养解析大列表（各元素为[data_type,bytype,bytype_name,data_pid]）
    '''
    # 中文形式网址
    url_zh = 'https://by.tuhu.cn/baoyang/%s/pl%s-n%s.html?Tid=%s&SalesName=%s' % (VehicleId, PaiLiang, Nian, Tid, SalesName)
    # 网址转码(部分符号不转)
    url = urllib.parse.quote(url_zh, ':/?=&()')

    # 创建无头浏览器
    options = webdriver.ChromeOptions()
    options.add_argument('User-Agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36"')
    options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=options)
    # 隐式等待
    driver.implicitly_wait(20)
    # 窗口最大化
    driver.maximize_window()
    # 模拟访问
    driver.get(url)

    time.sleep(2)

    # 判断保养项目是否存在
    package_baoyangExist = driver.find_elements_by_xpath('.//div[@id="package_baoyang"]')
    if package_baoyangExist:
        # 小保养：访问目标网页时，默认只是勾选小保养，单独获取其bytype,data_pid及HTML
        inventory_left = driver.find_element_by_xpath('.//div[@class="inventory_left"]')
        xbyHTML = inventory_left.get_attribute("outerHTML")

        # 所有保养（小保养除外）：遍历点击所有保养项目(可能会出现保养项目同时做提示，需关闭，否则无法正确点击)
        search = driver.find_elements_by_tag_name('dd')
        for i in search:
            i.click()
        time.sleep(1.5)
        # 检测保养关联提示，出现时关闭
        tips = driver.find_element_by_xpath('.//div[@id="package_baoyang"]').find_elements_by_xpath('.//a[@class="btn"]')
        if tips:
            for tip in tips:
                tip.click()
        # 再次检测除小保养外，所有未点击的保养项目，若存在则点击
        not_checked = driver.find_elements_by_xpath('.//dd[not(contains(@class,"checked"))]')
        for j in not_checked:
            if j.get_attribute('data-type') == 'xby':
                pass
            else:
                j.click()
        time.sleep(1.5)
        allHTML = inventory_left.get_attribute("outerHTML")

        # 小保养，所有保养（小保养除外）HTML解析，合并
        xbyHTML_analysis = analysis_maintenance_HTML(xbyHTML)
        allHTML_analysis = analysis_maintenance_HTML(allHTML)

        HTML_analysis = xbyHTML_analysis + allHTML_analysis

        return url_zh, xbyHTML, allHTML, HTML_analysis

    else:
        print('页面无保养类别信息：%s %s %s %s %s' % (VehicleId, PaiLiang, Nian, Tid, SalesName))
        return None, None, None, None

# 单项保养件所有商品信息抓取
def get_maintenance_parts(Brand, VehicleId, PaiLiang, Nian, Tid, SalesName, Vehicle, baoyangType, pid):
    '''
    :param Brand: 带首部大写字母-品牌
    :param VehicleId: 车系ID
    :param PaiLiang: 排量
    :param Nian: 生产年份
    :param Tid: 销售车型ID
    :param SalesName: 销售车型ID
    :param Vehicle: 车系-厂商
    :param baoyangType: 保养项目
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
        "baoyangType": "%s" % baoyangType,
        "pid": "%s" % pid
    }
    # 目标网站
    url = "https://by.tuhu.cn/change/ChangeProduct.html"
    # POST请求
    try:
        response = requests.post(url=url, headers=headers, data=data, timeout=20)
        # 硬等待
        time.sleep(1)
        # 关闭
        response.close()
        response_str = response.text
        # 处理NULL值,false,true,并转为字典形式
        response_str = response_str.replace('null', '""').replace('false', '"false"').replace('true', '"true"')
        response_dict = eval(response_str)
        return response_dict
    except:
        return None

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

# 大小保养项目源码HTML入库
def byHTML_insert_into_MySQL(byHTML_list):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")

    sql = """
        INSERT INTO `sales_vehicle_bytype_html`
        (tid,product_year,url_zh,xbyHTML,allHTML) 
        VALUES
        {};""".format(tuple(byHTML_list))
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

# 查询已存在商品信息(忽略图片链接之后字段，因图片链接中img1-4替换得到的图片一致)
def select_products_iofo():
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    sql = """
        SELECT 
            baoyang_type,baoyang_type_name,data_type,data_type_zh_name,category_type,category_name,
            suggest_tip,biref_description,is_very_urgent,detail_description,recommend_text,
            pid,p_display_name,p_brand
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

# 销售车型对应保养商品信息入库（产品库，保养件使用库）
def sales_vehicle_bytype_and_products_insert_into_MySQL(single_sales_vehicel, single_data_type_info_list, maintenance_parts_list):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")

    # 查询已存在商品信息
    exist_products_iofo_lists = select_products_iofo()

    # 遍历商品总列表，一条条入库
    for products in maintenance_parts_list:
        # 保养件使用入库
        new_line = single_sales_vehicel + single_data_type_info_list + products
        sql1 = '''
            INSERT INTO `sales_vehicle_bytype_and_products`
            (original_brand,brand,series_id,series,series2,series_factory,factory,displacement,product_year,tid,sales_name,
            baoyang_type,baoyang_type_name,data_type,data_type_zh_name,category_type,category_name,
            suggest_tip,biref_description,is_very_urgent,detail_description,recommend_text,
            pid,p_display_name,p_brand,p_brand_image_url,p_image_url,p_price,p_unit,p_is_original)
            VALUES
            {};'''.format(tuple(new_line))
        cur.execute(sql1)

        # 商品入库(商品信息不存在时，入库)
        products_list = single_data_type_info_list + products
        if products_list[:-5] not in exist_products_iofo_lists:
            sql2 = '''
                INSERT INTO `products`
                (baoyang_type,baoyang_type_name,data_type,data_type_zh_name,category_type,category_name,
                suggest_tip,biref_description,is_very_urgent,detail_description,recommend_text,
                pid,p_display_name,p_brand,p_brand_image_url,p_image_url,p_price,p_unit,p_is_original)
                VALUES
                {};'''.format(tuple(products_list))
            cur.execute(sql2)
    # 提交，关闭
    conn.commit()
    cur.close()
    conn.close()

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

############################### 数据采集 ###############################

# 第一步，查销售型库
# 所有需要采集的销售型数据
sales_vehicle = select_sales_year_from_MySQL()
# 所有已经采集的销售型数据
exist_sales_vehicle = select_sales_vehicle_bytype_and_products()

print('需采集数量：%s;已采集数量：%s' % (len(sales_vehicle), len(exist_sales_vehicle)))
for i in exist_sales_vehicle:
    if i in sales_vehicle:
        sales_vehicle.remove(i)
print('现即将采集数量：%s' % len(sales_vehicle))

# 提取第一个测试
# sales_vehicle = sales_vehicle[:1]
# 随机列表
shuffle(sales_vehicle)

# 计数
count = 0
# 遍历每个销售车型+生产年份
for single_sales_vehicel in sales_vehicle:
    count += 1

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

    # 第二步，通过车型参数，访问销售型保养页面，获取该销售型所有data_type，以字典形式存储，方便使用
    data_type_dict = maintenance_frequency(Brand, VehicleId, PaiLiang, Nian, Tid)
    # print(data_type_dict)
    time.sleep(1)

    # 第三步，模拟浏览器访问具体销售型，遍历点击所有保养项目（分两部分：小保养及所有保养（小保养除外））
    try:
        url_zh, xbyHTML, allHTML, HTML_analysis = get_bytype_and_dataPid(VehicleId, PaiLiang, Nian, Tid, SalesName)
    except:
        print(print('第%s条 <%s %s %s %s %s> 数据采集失败（模拟浏览器部分）...' % (count, Brand, VehicleId, PaiLiang, Nian, Tid)))
        continue
    time.sleep(1)
    # 以上任意结果返回None,跳出本次循环，继续下一个参数
    if None in [xbyHTML, allHTML, HTML_analysis]:
        continue

    # 大小保养项目源码HTML入库列表:
    byHTML_list = [Tid, Nian, url_zh, xbyHTML, allHTML]
    byHTML_insert_into_MySQL(byHTML_list)

    # 第四步，依据以上几步返回数据，传参，获取各销售型所有具体保养项目的所有保养商品信息
    # 遍历保养项目HTML解析出各 baoyangtype,pid
    for every_type in HTML_analysis:
        # 初始化单项保养类别信息列表
        single_data_type_info_list = []

        data_type = every_type[0]
        baoyangType = every_type[1]
        baoyangType_name = every_type[2]
        pid = every_type[3]
        # 访问目标网站，获取单项保养件所有商品字典
        maintenance_parts_dict = get_maintenance_parts(Brand, VehicleId, PaiLiang, Nian, Tid, SalesName, Vehicle, baoyangType, pid)
        time.sleep(2)
        if maintenance_parts_dict == None:
            continue
        # 解析单项保养件所有商品，返回总列表
        maintenance_parts_list = analysis_maintenance_parts(maintenance_parts_dict)
        if not maintenance_parts_list:
            continue
        # 依据data_type访问data_type_dict,提取保养类别及频率等相关信息(字典形式)
        single_data_type_info_dict = data_type_dict[data_type]
        # 分别提取：data_tpye的中文名，保养类别，类别名称，保养建议，保养简述，是否紧急，详细描述，推荐文本
        # 所有单项保养类别信息依次添加至单项保养类别信息列表
        single_data_type_info_list.append(baoyangType)
        single_data_type_info_list.append(baoyangType_name)
        single_data_type_info_list.append(data_type)
        single_data_type_info_list.append(single_data_type_info_dict['ZhName'])
        single_data_type_info_list.append(single_data_type_info_dict['CategoryType'])
        single_data_type_info_list.append(single_data_type_info_dict['CategoryName'])
        single_data_type_info_list.append(single_data_type_info_dict['SuggestTip'])
        single_data_type_info_list.append(single_data_type_info_dict['BirefDescription'])
        single_data_type_info_list.append(single_data_type_info_dict['IsVeryUrgent'])
        single_data_type_info_list.append(single_data_type_info_dict['DetailDescription'])
        single_data_type_info_list.append(single_data_type_info_dict['RecommendText'])

        # 第五步，开始入库(保养件使用库及产品库)
        sales_vehicle_bytype_and_products_insert_into_MySQL(single_sales_vehicel, single_data_type_info_list, maintenance_parts_list)

    print('第%s条 <%s %s %s %s %s> 数据采集成功！' % (count, Brand, VehicleId, PaiLiang, Nian, Tid))




