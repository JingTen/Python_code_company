# coding=utf-8
'''
重新解析保养产品HTML,去重存入保养产品表（若无则先新建）
以10000条数据为单位分批解析产品HTML（通过产品HTML表的id分批解析）
    第一步，数据库查询已经解析的产品信息
    第二步，数据库提取10000条需要解析的产品HTML
    第三步，解析产品HTML,去重存入解析结果
    第四步，解析结果去重存入已解析的产品表
'''
import pymysql

# 数据库产品表查询已解析的产品ID
def select_has_maintenance_products_from_MySQL():
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    sql = """
        SELECT 
            Pid
        FROM `tuhu_products`;
    """
    cur.execute(sql)
    result = cur.fetchall()
    # 关闭连接
    cur.close()
    conn.close()
    result_list = []
    if result:
        for i in result:
            result_list.append(i[0])
    return result_list

# 查询保养产品HTML,按条件提取
def select_products_HTML_from_MySQL(id_min, id_max):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    sql = """
        SELECT
            BaoYangType,response
        FROM `products_html`
        WHERE id BETWEEN %s AND %s;
    """ % (id_min, id_max)
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

# 单项保养件所有商品信息抓取后解析
def analysis_maintenance_parts(BaoYangType, maintenance_parts_dict):
    # Data中包含所有页的保养产品信息,以页数为键，每页保养产品信息列表为值组成的字典
    all_data = maintenance_parts_dict['Data']
    # 初始化单项保养件商品总列表
    maintenance_parts_list = []
    # 判断是否存在保养件信息
    if all_data:
        # 遍历每页保养件
        for page, p_info in all_data.items():
            # 遍历每个产品，每个产品信息为字典形式
            for p_dict in p_info:
                Pid = p_dict['Pid']  # 商品ID
                DisplayName = p_dict['DisplayName']  # 商品显示名称
                PBrand = p_dict['Brand']  # 商品品牌

                PBrandImage = p_dict['BrandImage']  # 商品品牌图片
                PImage = p_dict['Image']  # 商品产品主图
                # 处理图片链接，修正为原始尺寸图片链接
                PBrandImage = PBrandImage[:PBrandImage.find('@')] if PBrandImage.count('@') == 1 else PBrandImage
                PImage = PImage[:PImage.find('@')] if PImage.count('@') == 1 else PImage

                Price = str(p_dict['Price'])  # 商品价格
                Unit = p_dict['Unit']  # 商品单位
                IsOriginal = p_dict['IsOriginal']  # 商品是否属于原厂配件

                Tags = p_dict['Tags']
                tags_list = ["", "", "", ""]
                # 若存在Tags,则最多提取前4项Tags；不存在则设为默认空字符串
                if len(Tags) > 0:
                    for i in range(0, min(len(Tags), 4)):
                        tag = Tags[i]['Tag']
                        tags_list[i] = tag
                Tag_1 = tags_list[0]
                Tag_2 = tags_list[1]
                Tag_3 = tags_list[2]
                Tag_4 = tags_list[3]

                maintenance_parts_list.append(
                    [BaoYangType, Pid, DisplayName, PBrand, PBrandImage, PImage, Price, Unit, IsOriginal,
                     Tag_1, Tag_2, Tag_3, Tag_4])
    else:
        return None
    return maintenance_parts_list

# 解析结果入库
def maintenance_products_insert_into_MySQL(results_lists):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    for i in results_lists:
        sql = '''
            INSERT INTO `tuhu_products`
                (BaoYangType, Pid, DisplayName, PBrand, PBrandImage, PImage, Price, Unit, IsOriginal, 
                Tag_1, Tag_2, Tag_3, Tag_4)
            VALUES
            {};
        '''.format(tuple(i))
        cur.execute(sql)
    # 提交，关闭
    conn.commit()
    cur.close()
    conn.close()


# 以10000条数据为单位分批解析
for ii in range(0, 297):
    id_min = (10000 * ii) + 1
    id_max = (1 + ii) * 10000
    # 第一步，数据库查询已经解析的产品信息
    already_maintenance_product = select_has_maintenance_products_from_MySQL()

    # 第二步，数据库提取10000条需要解析的产品HTML
    need_mantenance_product_html = select_products_HTML_from_MySQL(id_min, id_max)

    # 第三步，解析产品HTML,去重存入解析结果
    # 每批的解析结果列表初始化
    single_10000 = []
    # 遍历需要解析的产品HTML,提取BaoYangType和HTML
    for jj in need_mantenance_product_html:
        BaoYangType = jj[0]
        # 处理HTML为字典(去掉前后各一个双引号)
        html_dict = eval(jj[1][1:-1])
        # HTML解析,存入入库列表
        maintenance_parts_list = analysis_maintenance_parts(BaoYangType, html_dict)
        if maintenance_parts_list:
            single_10000 += maintenance_parts_list
        else:
            print('无保养件信息')
    # 去重存入解析结果(存在图片一致但图片url不一致的情况，仅依据产品ID去重即可)
    single_10000_not_repeat = []
    single_10000_pid = ['']
    for kk in single_10000:
        if single_10000_not_repeat:
            if (kk[1] not in single_10000_pid) and (kk[1] not in already_maintenance_product):
                single_10000_not_repeat.append(kk)
                single_10000_pid.append(kk[1])
        else:
            if kk[1] not in already_maintenance_product:
                single_10000_not_repeat.append(kk)
                single_10000_pid.append(kk[1])

    # 第四步，解析结果去重存入已解析的产品表
    maintenance_products_insert_into_MySQL(single_10000_not_repeat)
    print('第%s批入库成功（id <= %s）' % (ii + 1, id_max))
