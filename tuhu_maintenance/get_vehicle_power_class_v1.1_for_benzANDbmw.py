# coding:utf-8
'''
采集途虎养车动力总成级别的车型数据（仅适合奔驰宝马）

获取途虎养车网站的所有品牌-车系-排量-年份

修复bug:
1.点击车系后，车型选择弹框消失，无法继续排量选择
2.点击车系后，车型选择弹框存在，但需再次选择车系（如宝马）

'''

from selenium import webdriver
import requests
import time
import pymysql
from selenium.common.exceptions import NoSuchElementException

# 存入数据库
def insert_into_MySQL(lists):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    try:
        sql = """
            INSERT INTO 
            `vehicle_power_class`
            (original_brand,brand,series_id,series,series2,series_factory,factory,displacement,product_year,maintenance_url) 
            VALUES
            {};""".format(tuple(lists))
        cur.execute(sql)
        conn.commit()
    finally:
        cur.close()
        conn.close()
# 查询已采集完成的[品牌-途虎车系ID-排量]，避免重复采集
def collected_data_from_MySQL():
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    sql = '''
        SELECT DISTINCT brand,series_id,displacement
        FROM `vehicle_power_class`;
    '''
    cur.execute(sql)
    result = cur.fetchall()
    # 处理查询结果
    if result:
        collected_data = []
        for i in result:
            i_list = list(i)
            collected_data.append(i_list)
    else:
        collected_data = []

    return collected_data


# 模拟访问途虎养车首页
def www_tuhu_cn(url='https://www.tuhu.cn/'):
    # 创建会话
    options = webdriver.ChromeOptions()
    # 设置请求头
    options.add_argument('User-Agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36"')
    options.add_argument('Accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3"')
    options.add_argument('Origin="https://www.tuhu.cn"')
    # options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=options)
    # 隐式等待
    driver.implicitly_wait(30)
    # 浏览器窗口最大化
    driver.maximize_window()
    # 模拟访问目标网址
    driver.get(url)
    # 硬等待
    time.sleep(20)
    return driver

# 手动点击车型选择弹框
def click_carSelect(driver):
    driver.find_element_by_xpath('.//div[@id="myCar"]').click()
    time.sleep(3)

# 遍历采集
def collect_vehicle_power_class(driver,collected_data):
    # 车型选择弹框 - 所有内容
    CarSelect = driver.find_element_by_xpath('.//div[@id="carSelect"]')
    # 车型选择弹框 - 品牌首字母
    CarZiMus = CarSelect.find_element_by_xpath('.//div[@id="div2"]').find_element_by_tag_name('ul').find_elements_by_tag_name('li')
    # 字母层级
    count = 0  # 计数
    for letter in CarZiMus:
        if len(letter.text) == 1 and letter.text == 'B':
            letter.click()  # 点击字母
            time.sleep(2)

            # 品牌层级
            CarBrands = driver.find_element_by_xpath('.//div[@id="CarBrands"]').find_elements_by_tag_name('li')
            for brand in CarBrands:
                # 提取信息：品牌
                OriginalBrand = brand.get_attribute('data-brand')
                Brand = brand.get_attribute('data-brand')[4:]
                # print(OriginalBrand,Brand)
                if Brand not in ['宝马']:
                    # print('%s暂时不采集'% Brand)
                    continue
                brand.click()  # 点击品牌
                time.sleep(2)

                # 车系层级(第一层)
                Series1 = driver.find_element_by_xpath('.//div[@id="div5"]').find_elements_by_xpath('.//li[not(contains(@class,"CarBrandTitle"))]')
                for series1_index in range(len(Series1)):
                    series = driver.find_element_by_xpath('.//div[@id="div5"]').find_elements_by_xpath('.//li[not(contains(@class,"CarBrandTitle"))]')

                    # 提取信息：第一层车系
                    # 判断是否为，已经采集的，且点击车系无详细销售型的数据
                    #if [Brand,SeriesID,'-'] in collected_data:
                    #    continue
                    series1 = series[series1_index].get_attribute('data-vehicle')
                    series[series1_index].click()  # 点击第一层车系
                    time.sleep(3)

                    # 车系层级（第二层）
                    Series2 = driver.find_element_by_xpath('.//div[@id="div5"]').find_elements_by_xpath(
                        './/li[not(contains(@class,"CarBrandTitle"))]')
                    for series2_index in range(len(Series2)):
                        series_2 = driver.find_element_by_xpath('.//div[@id="div5"]').find_elements_by_xpath(
                            './/li[not(contains(@class,"CarBrandTitle"))]')
                        # 提取信息：第二层车系
                        SeriesID = series_2[series2_index].get_attribute('data-id')
                        SeriesAndFactory = series_2[series2_index].get_attribute('data-vehicle')
                        SeriesName = series_2[series2_index].text
                        Factory = SeriesAndFactory[SeriesAndFactory.find('-') + 1:]


                        series_2[series2_index].click()  # 点击第二层车系
                        time.sleep(3)

                        # 点击车系后，判断车型选择弹框是否存在
                        # 1.存在，继续，并判断是否需要再次选择车系（暂时未解决）
                        # 2.不存在，则该品牌车系下无更细销售型，重新点击车系选择弹框
                        try:
                            carSelect_element_existOrNot = driver.find_element_by_xpath('.//div[@id="carSelect"]')

                            # 排量层级
                            Displacements = driver.find_element_by_xpath('.//div[@id="div5"]').find_elements_by_tag_name('li')
                            Displacements_len = len(Displacements)

                            for displacement_index in range(Displacements_len):
                                displacements = driver.find_element_by_xpath('.//div[@id="div5"]').find_elements_by_tag_name('li')

                                # 提取排量名称
                                DisplacementName = displacements[displacement_index].get_attribute('data-pailiang')
                                DisplacementText = displacements[displacement_index].text
                                if DisplacementName == DisplacementText:
                                    pass
                                else:
                                    print('品牌：%s  车系：%s  排量：%s  排量属性取值与文本取值不一致' % (OriginalBrand, SeriesName, DisplacementName))

                                # 判断是否已经采集
                                check_list = [Brand,SeriesID,DisplacementName]
                                if check_list in collected_data:
                                    continue

                                displacements[displacement_index].click()  # 点击排量
                                time.sleep(3)

                                try:
                                    # 年份层级
                                    YearProduct = driver.find_element_by_xpath('.//div[@id="div5"]').find_elements_by_tag_name('li')
                                    for years in YearProduct:
                                        Years = years.get_attribute('data-nian')
                                        # print(Years)
                                        maintenance_url = 'https://by.tuhu.cn/baoyang/' + SeriesID + '/pl' + DisplacementName + '-n' + str(Years) + '.html'
                                        result_list = [OriginalBrand, Brand, SeriesID, series1, SeriesName, SeriesAndFactory, Factory, DisplacementName, Years, maintenance_url]

                                        # 插入数据库
                                        insert_into_MySQL(result_list)
                                        count += 1  # 成功插入计数
                                        print('第%s条记录成功入库...[%s-%s-%s-%s]' % (count, Brand, SeriesName, DisplacementName, Years))

                                    driver.find_element_by_xpath('.//div[@data-index="3"]').click()  # 关闭排量
                                    time.sleep(2)
                                except:
                                    print('品牌：%s  车系：%s  排量：%s  年份选项未采集完整' % (OriginalBrand, SeriesName, DisplacementName))
                                    driver.find_element_by_xpath('.//div[@data-index="3"]').click()
                                    time.sleep(2)
                                    continue

                            driver.find_element_by_xpath('.//div[@data-index="2"]').click()  # 关闭第二层车系
                            time.sleep(2)

                        except NoSuchElementException:
                            # 插入数据库，只是缺少排量之后信息
                            result_list = [OriginalBrand, Brand, SeriesID, series1, SeriesName, SeriesAndFactory, Factory, '-', '-', '-']
                            insert_into_MySQL(result_list)

                            # 关闭浏览器，重新获取已采集数据，并继续遍历采集数据
                            collected_data = collected_data_from_MySQL()
                            driver.close()

                            driver = www_tuhu_cn(url='https://www.tuhu.cn/')
                            click_carSelect(driver)
                            driver = collect_vehicle_power_class(driver, collected_data)

                    driver.find_element_by_xpath('.//div[@data-index="12"]').click()  # 关闭第一层车系
                    time.sleep(2)

                driver.find_element_by_xpath('.//div[@data-index="1"]').click()  # 关闭品牌
                time.sleep(2)





collected_data = collected_data_from_MySQL()
driver = www_tuhu_cn(url='https://www.tuhu.cn/')
click_carSelect(driver)
driver = collect_vehicle_power_class(driver, collected_data)








