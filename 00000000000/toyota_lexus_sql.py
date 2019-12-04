# coding=utf-8
'''
丰田雷克萨斯外观颜色匹配
'''

import pymysql
import csv


def be_really(vins, vin_head, year):
    vin_end = vins.split("-")[1]
    v = get_right_vin(vin_head, vin_end[0], int(vin_end[1:]), year)
    return v

def get_right_vin(vin8, vin2, vin_end, year):
    """
    根据权重校验获取有效的vin(该vin并不一定存在)
    :param vin8: vin的前8位
    :param vin2: vin的10,11位
    :param vin_end: vin的后6位
    :return: 有效的vin
    """
    # vin中字母对应的值
    dict_alp = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'J': 1, 'K': 2, 'L': 3, 'M': 4,
                'N': 5, 'P': 7, 'R': 9, 'S': 2, 'T': 3, 'U': 4, 'V': 5, 'W': 6, 'X': 7, 'Y': 8, 'Z': 9,
                '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '*': 0}
    # vin中数字对应的加权系数值，第9位是权重位
    dict_index = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 10, 9: 0,
                  10: 9, 11: 8, 12: 7, 13: 6, 14: 5, 15: 4, 16: 3, 17: 2}
    # 年份表
    dict_year = {
        2020: 'L', 2019: 'K', 2018: 'J', 2017: 'H', 2016: 'G', 2015: 'F', 2014: 'E', 2013: 'D', 2012: 'C',
        2011: 'B', 2010: 'A', 2009: '9', 2008: '8', 2007: '7', 2006: '6', 2005: '5', 2004: '4', 2003: '3'
    }
    vin2 = dict_year[int(year)] + vin2
    # 前八位权重值
    q1 = 0
    for i in range(1, len(vin8) + 1):
        q1 += (dict_alp[vin8[i - 1]] * dict_index[i])

    # 第9位暂时补‘*’，待算出v9后替换掉‘*’
    vin = vin8 + "*" + vin2 + "%06d" % vin_end
    # 权重值
    q2 = 0
    for i in range(10, len(vin) + 1):
        q2 += (dict_alp[vin[i - 1]] * dict_index[i])
    # 确认vin的第9位的值
    v9 = "X" if (q1 + q2) % 11 == 10 else str((q1 + q2) % 11)
    vin = vin.replace("*", v9)
    return vin

def select_hash(model_id):
    '''车型ID 查 hash'''
    conn = pymysql.connect(host='192.168.3.110', user='jing', passwd='123456', db='toyota_201910', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE toyota_201910")
    sql = '''
        SELECT GROUP_CONCAT(vin_group_hash)
        FROM `vin_config_hash_map` 
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

def select_vin_info(hash_list):
    '''通过 hash 查 VIN信息'''
    conn = pymysql.connect(host='192.168.3.110', user='jing', passwd='123456', db='toyota_201910', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE toyota_201910")
    sql = '''
        SELECT head_ofs,vin,prod_date
        FROM `vin_pnc_group` 
        WHERE `vin_pnc_group`.pnc_hash IN {};
    '''.format(tuple(hash_list))
    cur.execute(sql)
    result = cur.fetchall()
    result_list = []
    if result != ((None,),):
        for i in result:
            result_list.append(list(i))
    cur.close()
    conn.close()
    return result_list

def select_frame_num(hash_list):
    '''通过 hash 查 frame_num'''
    conn = pymysql.connect(host='192.168.3.110', user='jing', passwd='123456', db='toyota_201910', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE toyota_201910")
    sql = '''
        SELECT vin
        FROM `vin_pnc_group` 
        WHERE `vin_pnc_group`.pnc_hash IN {};
    '''.format(tuple(hash_list))
    cur.execute(sql)
    result = cur.fetchall()
    result_list = []
    if result != ((None,),):
        for i in result:
            result_list.append(i[0])
        result_list = list(set(result_list))
    cur.close()
    conn.close()
    return result_list

def select_color(frame_num_list, model_id):
    '''通过 frame_num 查颜色代码'''
    conn = pymysql.connect(host='192.168.3.110', user='jing', passwd='123456', db='toyota_201910', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE toyota_201910")
    sql = '''
        SELECT head_ofs,LEFT(prod_date,4),frame_num,color,MIN(prod_date),MAX(prod_date),COUNT(*)
        FROM `feature_frame_less_data_for_carcolor`
        WHERE frame_num IN {}
        GROUP BY color
        ORDER BY COUNT(*) DESC;
    '''.format(tuple(frame_num_list))
    cur.execute(sql)
    result = cur.fetchall()
    result_list = []
    if result != ((None,),):
        for i in result:
            result_list.append([str(model_id)] + list(i))
    cur.close()
    conn.close()
    return result_list

def write_csv(file_name, lists):
    with open(file_name, 'a+', encoding='utf-8', newline='') as f:
        csv_writer = csv.writer(f)
        for line in lists:
            csv_writer.writerow(line)



'''
### 1.查找车型ID所有可能出现的颜色代码，结果存入csv
# 需要查找的model_id列表
model_id_list = ['6520', '23153', '8385', '8390', '4488', '15629', '14829', '23525', '12481', '17021', '6154', '10865',
                 '17030', '24494', '11188', '10648', '32665', '32663', '32661', '6178', '12437', '16505', '17383',
                 '4910', '13987', '5194', '4916', '13684', '11773', '24074', '23358', '22601', '34958', '6015', '12472',
                 '13403', '19944', '13405', '13341', '12685', '19946', '19947', '6013', '12686', '8780', '11061',
                 '14777', '16503', '18057', '18058', '32658', '18008', '20607', '20606', '19588', '18825', '20605',
                 '20604', '18797', '24075', '24324', '24224', '24476', '22225']
# 遍历model_id查询所有符合条件的color
count_num = len(model_id_list)
all_result = []
count = 0
for model_id in model_id_list:
    count += 1
    hash_lists = select_hash(model_id)
    if hash_lists:
        frame_num_list = select_frame_num(hash_lists)
        if frame_num_list:
            color_result = select_color(frame_num_list, model_id)
            if color_result:
                for i in color_result:
                    all_result.append(i)
            else:
                all_result.append([str(model_id), '-', '-', '-', '-', '-', '-', '-'])
        else:
            all_result.append([str(model_id), '-', '-', '-', '-', '-', '-', '-'])
    else:
        all_result.append([str(model_id), '-', '-', '-', '-', '-', '-', '-'])
    print('第%s条（共%s条）数据查询完毕！' % (count, count_num))

# 存入csv文件
write_csv('toyota_lexus.csv', all_result)
print('写入CSV文件成功')
'''

### 2.依据