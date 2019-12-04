# coding=utf-8
'''
剔除原结果表多余字段，新增据保养项目所需商品数量Count字段

'''

import pymysql

# 查询现有结果表，剔除多余字段
def select_less_field_from_sales_vehicle_bytype_and_products(id_min, id_max):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    sql = """
        SELECT DISTINCT 
            original_brand,brand,series_id,series,series2,series_factory,factory,displacement,product_year,tid,sales_name,
            BaoYangType,BaoYangType_ZhName,PackageType,PackageType_ZhName,CategoryType,CategoryName,DataTip,Pid
        FROM `sales_vehicle_bytype_and_products`
        WHERE id BETWEEN %s AND %s;
    """ % (id_min, id_max)
    cur.execute(sql)
    result = cur.fetchall()
    # 关闭连接
    cur.close()
    conn.close()
    return result

# 将结果存入简化新结果表
def insert_into_new_result(tuples):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE tuhu_maintenance")
    for i in tuples:
        sql = '''
            INSERT INTO `tuhu_sales_vehicle_bytype_and_pid`
                (original_brand,brand,series_id,series,series2,series_factory,factory,displacement,product_year,tid,sales_name,
                BaoYangType,BaoYangType_ZhName,PackageType,PackageType_ZhName,CategoryType,CategoryName,DataTip,Pid)
            VALUES
            {};
        '''.format(i)
        cur.execute(sql)
    # 提交，关闭
    conn.commit()
    cur.close()
    conn.close()

# 分批查询存入（10000条一次）

for ii in range(0, 3052):
    id_min = (10000 * ii) + 1
    id_max = (1 + ii) * 10000
    tuples = select_less_field_from_sales_vehicle_bytype_and_products(id_min, id_max)
    insert_into_new_result(tuples)
    print('第%s次存入成功(id<%s)' % (ii+1, id_max))
print('GAME OVER!!!')