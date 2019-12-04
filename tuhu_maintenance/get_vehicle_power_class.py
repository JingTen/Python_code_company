# coding:utf-8
'''
采集途虎养车动力总成级别的车型数据

获取途虎养车网站的所有品牌-车系-排量-年份

'''


from selenium import webdriver
import requests
import time
import pymysql

# 存入数据库
def insert_into_MySQL(lists):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')

    cur = conn.cursor()

    cur.execute("USE tuhu_maintenance")

    try:
        sql = """
            INSERT INTO 
            `vehicle_power_class`
            (original_brand,brand,series_id,series,series_factory,factory,displacement,product_year,maintenance_url) 
            VALUES
            {};""".format(tuple(lists))

        # print(sql)

        cur.execute(sql)

        conn.commit()

    finally:
        cur.close()
        conn.close()

# 模拟浏览器遍历车型信息
# 设置请求头
options = webdriver.ChromeOptions()
options.add_argument('User-Agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36"')
options.add_argument('Accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3"')
options.add_argument('Origin="https://www.tuhu.cn"')
# options.add_argument('--headless')
ip = '122.114.125.90'
port = '16819'
# options.add_argument('--proxy-server=http://%s:%s' % (ip, port))

driver = webdriver.Chrome(chrome_options=options)
# 浏览器窗口最大化
driver.maximize_window()

url = 'https://www.tuhu.cn/'
driver.get(url)
time.sleep(20)

# 车型选择弹框
driver.find_element_by_xpath('.//div[@id="myCar"]').click()
time.sleep(3)

# 车型选择弹框 - 所有内容
CarSelect = driver.find_element_by_xpath('.//div[@id="carSelect"]')

# 车型选择弹框 - 品牌首字母
CarZiMus = CarSelect.find_element_by_xpath('.//div[@id="div2"]').find_element_by_tag_name('ul').find_elements_by_tag_name('li')

# 暂时有问题的品牌
runned_brand = ['比亚迪','保时捷','别克','宝龙','成功','长安','昌河']
dont_run_brand = ['奔驰','萨博','宝马','标致','宾利']

# 字母层级
count = 0 # 计数
for letter in CarZiMus:
    if len(letter.text) == 1 and letter.text not in ['A', 'B']:
        letter.click()  # 点击字母
        time.sleep(2)

        # 品牌层级
        CarBrands = driver.find_element_by_xpath('.//div[@id="CarBrands"]').find_elements_by_tag_name('li')
        for brand in CarBrands:

            # 提取信息：品牌
            OriginalBrand = brand.get_attribute('data-brand')
            Brand = brand.get_attribute('data-brand')[4:]
            # print(OriginalBrand,Brand)

            # 跳过品牌采集
            if Brand in dont_run_brand or Brand in runned_brand:
                print('%s暂时不跑' % Brand)
                continue

            brand.click()  # 点击品牌
            time.sleep(2)

            # 车系层级
            Series = driver.find_element_by_xpath('.//div[@id="div5"]').find_elements_by_xpath(
                './/li[not(contains(@class,"CarBrandTitle"))]')
            Series_len = len(Series)
            for series_index in range(len(Series)):
                series = driver.find_element_by_xpath('.//div[@id="div5"]').find_elements_by_xpath(
                    './/li[not(contains(@class,"CarBrandTitle"))]')

                # 提取信息：车系ID，车系-品牌厂商，车系
                SeriesID = series[series_index].get_attribute('data-id')
                SeriesAndFactory = series[series_index].get_attribute('data-vehicle')
                SeriesName = series[series_index].text
                Factory = SeriesAndFactory[SeriesAndFactory.find('-')+1:]
                # print(SeriesID,SeriesAndFactory,SeriesName)

                if Brand == '长安商用' and (SeriesName in ['长安星韵']):
                    continue
                series[series_index].click()  # 点击车系
                time.sleep(2)

                try:
                    # 排量层级
                    Displacements = driver.find_element_by_xpath('.//div[@id="div5"]').find_elements_by_tag_name('li')
                    Displacements_len = len(Displacements)

                    for displacement_index in range(Displacements_len):
                        displacements = driver.find_element_by_xpath('.//div[@id="div5"]').find_elements_by_tag_name(
                            'li')

                        # 提取排量名称
                        DisplacementName = displacements[displacement_index].get_attribute('data-pailiang')
                        DisplacementText = displacements[displacement_index].text
                        if DisplacementName == DisplacementText:
                            pass
                        else:
                            print('品牌：%s  车系：%s  排量：%s  排量属性取值与文本取值不一致' % (OriginalBrand, SeriesName, DisplacementName))

                        displacements[displacement_index].click()  # 点击排量
                        time.sleep(3)

                        try:
                            # 年份层级
                            YearProduct = driver.find_element_by_xpath('.//div[@id="div5"]').find_elements_by_tag_name(
                                'li')
                            for years in YearProduct:
                                Years = years.get_attribute('data-nian')
                                # print(Years)
                                maintenance_url = 'https://by.tuhu.cn/baoyang/' + SeriesID + '/pl' + DisplacementName + '-n' + str(Years) + '.html'
                                result_list = [OriginalBrand, Brand, SeriesID, SeriesName, SeriesAndFactory, Factory, DisplacementName, Years, maintenance_url]
                                #print(result_list)
                                # 插入数据库
                                insert_into_MySQL(result_list)
                                count += 1 # 成功插入计数
                                print('第%s条记录成功入库...[%s-%s-%s-%s]' %(count, Brand, SeriesName, DisplacementName, Years))
                        except:
                            print('品牌：%s  车系：%s  排量：%s  年份选项未采集完整' % (OriginalBrand, SeriesName, DisplacementName))
                            driver.find_element_by_xpath('.//div[@data-index="3"]').click()
                            time.sleep(2)
                            continue

                        driver.find_element_by_xpath('.//div[@data-index="3"]').click()  # 关闭排量
                        time.sleep(2)
                except:
                    print('品牌：%s  车系：%s  排量选项未采集完整' % (OriginalBrand, SeriesName))
                    driver.find_element_by_xpath('.//div[@data-index="2"]').click()
                    time.sleep(2)
                    continue

                driver.find_element_by_xpath('.//div[@data-index="2"]').click()  # 关闭车系
                time.sleep(2)

            driver.find_element_by_xpath('.//div[@data-index="1"]').click()  # 关闭品牌
            time.sleep(2)