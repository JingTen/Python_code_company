# coding=utf-8
'''
日产外观颜色匹配
通过已经匹配的车型ID查询该车型ID下所有可能出现的外观颜色信息
'''

import pymysql

def select_hash(model_id):
    '''车型ID 查 hash'''
    conn = pymysql.connect(host='192.168.3.114', user='jing', passwd='123456', db='vin_nissan', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE vin_nissan")
    sql = '''
        SELECT GROUP_CONCAT(vin_group_hash) 
        FROM `sub_config_hash_map` 
        WHERE match_ids LIKE "%{}%";
    '''.format(model_id)
    cur.execute(sql)
    result = cur.fetchall()
    result_list = []
    if result != ((None, ),):
        result_list = result[0][0].split(',')
        result_list = list(set(result_list))
    cur.close()
    conn.close()
    return result_list

def select_vin(hash_list):
    '''通过 hash 查 VIN'''
    conn = pymysql.connect(host='192.168.3.114', user='jing', passwd='123456', db='vin_nissan', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE vin_nissan")
    if len(hash_list) == 1:
        sql = '''
                    SELECT `sub_vin_parts_hash`.vin
                    FROM `sub_vin_parts_hash` 
                    WHERE `sub_vin_parts_hash`.parts_hash = '%s';
                ''' % hash_list[0]
    else:
        sql = '''
            SELECT `sub_vin_parts_hash`.vin
            FROM `sub_vin_parts_hash` 
            WHERE `sub_vin_parts_hash`.parts_hash IN {};
        '''.format(tuple(hash_list))
    cur.execute(sql)
    result = cur.fetchall()
    result_list = []
    if result != ((None,),):
        for i in result:
            result_list.append(i[0])
    cur.close()
    conn.close()
    return result_list

def select_vin_color_info(vin_list):
    '''通过 hash 查 VIN 外观颜色信息'''
    conn = pymysql.connect(host='192.168.3.114', user='jing', passwd='123456', db='vin_nissan', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE vin_nissan")
    # REPLACE(`app_nissan_vin`.color,' PRC','') AS 'color_code',
    sql = '''
        SELECT T2.*,`nissan_body_color`.name
        FROM
            (SELECT 
                `app_nissan_vin`.vin, `app_nissan_vin`.date,
                LEFT(`app_nissan_vin`.color, 3) AS 'color_code',
                MIN(`app_nissan_vin`.date) AS 'MIN_date', MAX(`app_nissan_vin`.date) AS 'MAX_date',
                COUNT(*)
            FROM `app_nissan_vin`
            WHERE `app_nissan_vin`.vin IN 
            {}
            GROUP BY `color_code`
            ORDER BY COUNT(*) DESC) AS T2
        LEFT JOIN `nissan_body_color`
        ON T2.color_code = `nissan_body_color`.code;
    '''.format(tuple(vin_list))
    cur.execute(sql)
    result = cur.fetchall()
    result_list = []
    if result != ((None,),):
        result = sorted(result, key=lambda _: _[5], reverse=True)
        print('------- vin -------,   date,  code,  start,  end,   count,  name')
        for i in result:
            print(i)
            result_list.append(i)
    cur.close()
    conn.close()
    return result_list


while True:
    model_id = input("请输入要查询的车型ID(输入q退出):")
    if model_id == "q":
        break
    # 第一步，通过车型ID查可能的所有hash，并转化为列表，方便后续查询
    hash_list = select_hash(model_id)
    # 第二步，通过已查出的hash列表，查找所有的符合条件的VIN
    if hash_list:
        vin_list = select_vin(hash_list)
        # 第三步，通过vin列表，给出所有VIN去重后的外观颜色信息
        if vin_list:
            model_id_color = select_vin_color_info(vin_list)
            # print(model_id_color)
        else:
            print('无符合条件的vin_list')
    else:
        print('无符合条件的hash_list')

    model_id = ''

