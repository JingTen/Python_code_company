# coding=utf-8
'''
丰田外观颜色匹配
'''

import pymysql
import csv
import copy


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

################### 1

def select_hash(model_id):
    '''车型ID 查 hash'''
    conn = pymysql.connect(host='192.168.3.110', user='jing', passwd='123456', db='toyota_201910', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE toyota_201910")
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

def select_frame_num(hash_list):
    '''通过 hash 查 frame_num'''
    conn = pymysql.connect(host='192.168.3.110', user='jing', passwd='123456', db='toyota_201910', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE toyota_201910")
    # hash_list长度为1时，需修正，否则sql报语法错误
    if len(hash_list) != 1:
        sql = '''
            SELECT frame_num
            FROM `sub_vin_parts_hash` 
            WHERE `sub_vin_parts_hash`.parts_hash IN {};
        '''.format(tuple(hash_list))
    else:
        sql = '''
            SELECT frame_num
            FROM `sub_vin_parts_hash` 
            WHERE `sub_vin_parts_hash`.parts_hash = '{}';
        '''.format(hash_list[0])
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

################### 2
def select_vin8_by_head_ofs(head_ofs_list):
    '''通过 head_ofs 查 vin8'''
    conn = pymysql.connect(host='192.168.3.110', user='jing', passwd='123456', db='toyota_201910', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE toyota_201910")
    # hash_list长度为1时，需修正，否则sql报语法错误
    if len(head_ofs_list) != 1:
        sql = '''
            SELECT head_ofs,vin_head
            FROM `feature_vin` 
            WHERE `feature_vin`.head_ofs IN {};
        '''.format(tuple(head_ofs_list))
    else:
        sql = '''
            SELECT head_ofs,vin_head
            FROM `feature_vin` 
            WHERE `feature_vin`.head_ofs = '{}';
        '''.format(head_ofs_list[0])
    cur.execute(sql)
    result = cur.fetchall()
    result_dict = {}
    if result != ((None,),):
        for i in result:
            if i[0] not in result_dict:
                result_dict[i[0]] = [i[1]]
            else:
                result_dict[i[0]].append(i[1])
    cur.close()
    conn.close()
    return result_dict

def read_csv_of_vin_info(file_name):
    data_list = []
    with open(file_name, 'r', encoding='utf-8', newline='') as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            data_list.append(row)
    return data_list


'''
### 1.查找车型ID所有可能出现的颜色代码，结果存入csv
# 需要查找的model_id列表
model_id_list = ['12409', '12410', '25988', '25990', '3496', '3497', '21970', '7668', '17568', '7933', '2493', '3020',
                 '8111', '10612', '10614', '14508', '14321', '14509', '14382', '14507', '15618', '11244', '15146',
                 '11260', '20899', '20901', '20902', '7511', '12931', '11262', '20908', '31824', '11257', '11261',
                 '11258', '15147', '3638', '17200', '17201', '17198', '17199', '18405', '15863', '17202', '18404',
                 '17143', '18412', '15513', '5116', '17541', '17904', '6066', '1380', '12105', '12104', '7693', '8495',
                 '8497', '8496', '8498', '12181', '16980', '16972', '16981', '16959', '16983', '5425', '8501', '2757',
                 '3799', '3805', '8479', '8480', '8477', '27871', '3088', '8628', '12175', '15381', '15153', '8627',
                 '15380', '15270', '18889', '18891', '18890', '18892', '18894', '18897', '2965', '3075', '4113',
                 '12176', '18898', '8607', '12177', '15154', '18899', '18900', '24018', '16749', '16748', '21138',
                 '21139', '16747', '16746', '21141', '5095', '10669', '15155', '10673', '10668', '5099', '10675',
                 '12180', '15157', '16745', '16744', '15767', '21143', '27122', '22040', '22042', '22045', '22047',
                 '30497', '13034', '13506', '13035', '13036', '12989', '16364', '16365', '5283', '13037', '13000',
                 '23574', '32857', '6651', '10445', '13460', '13445', '21300', '6318', '8207', '7561', '9909', '9910',
                 '9911', '9912', '9913', '17101', '17103', '17106', '20424', '9018', '9197', '17578', '10179', '11443',
                 '14934', '16763', '16761', '16766', '16765', '20701', '16764', '27313', '26330', '28127', '19209',
                 '19210', '19211', '19221', '18920', '22461', '30389', '30264', '28517', '34988', '36767', '33016',
                 '34520']


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
write_csv('toyota_toyota.csv', all_result)
print('写入CSV文件成功')
'''


### 2.依据head_ofs, year, frame_num生成真实VIN

head_ofs_list = ['000f6fc6', '000cf7aa', '0003894c', '000f7e4e', '000f7d94', '000226bc', '000fa9e6', '000fab5a',
                 '000c3150', '000c337e', '00264384', '00263fe2', '0026a2b2', '0026a13e', '0025cae8', '000c04fe',
                 '001971a2', '0000672c', '000067e6', '000d0a8e', '000d0b48', '002a6906', '002a684c', '0000c942',
                 '0000d428', '0000d656', '00036cf6', '00037098', '00024258', '0003dcda', '0003dd94', '000441d8',
                 '00035acc', '00035e6e', '00035fe2', '001ac37c', '001c1d54', '001c1c9a', '001c19b2', '001c699e',
                 '001c68e4', '001c65fc', '001c63ce', '002d70fe', '002d6d5c', '0025c746', '0025c68c', '002d7614',
                 '000cb1ea', '000cb35e', '000cb2a4', '000cb418', '000ca878', '000cb076', '001a6b92', '002d6900',
                 '002d6be8', '001bc624', '002ad602', '002ad6bc', '002ad3d4', '002c6e56', '002c6ce2', '002c793c',
                 '002c736c', '002c7426', '002b4016', '002b30d4', '002b2dec', '002b2ea6', '002c99ee', '002b452c',
                 '002ca360', '002ca930', '002d926a', '002d1572', '002d26e2', '002d1e2a', '002d5106', '002d4e1e',
                 '00004164', '0000421e', '00003dc2', '00002f3a', '00002ff4', '00030684', '0003016e', '000307f8',
                 '0003415e', '00033fea', '00034446', '000342d2', '00033732', '00033a1a', '0003344a', '000d29cc',
                 '000d2858', '000d2a86', '0002d804', '0002d3a8', '0002d8be', '0002d5d6', '000c9f06', '000c9fc0',
                 '000ca41c', '000c9cd8', '001879e0', '0002c520', '0002c5da', '0029e356', '0029e926', '0029e9e0',
                 '0029e63e', '0029ec0e', '0029f7ae', '0029f6f4', '001c0842', '001c032c', '001c4bd4', '001c4c8e',
                 '001c4d48', '001c4778', '001c4f76', '001c582e', '001bbf9a', '002c4da4', '002c4f18', '002c8b66',
                 '002c8e4e', '002d8c9a', '002d8610', '002d8d54', '001c431c', '00187926', '001876f8', '0018763e',
                 '002d9552']
# 获取head_ofs与vin8映射字典（很可能一对多）
head_ofs_match_vin8_dict = select_vin8_by_head_ofs(head_ofs_list)
file_name = 'toyota_toyota_vin_info.csv'
data_list = read_csv_of_vin_info(file_name)
# 所有原始数据匹配vin8
new_data_list = []
for data in data_list:
    head_ofs = data[1]
    if head_ofs in head_ofs_match_vin8_dict:
        vin8_list = head_ofs_match_vin8_dict[head_ofs]
        # print(head_ofs, vin8_list)
        data.append(vin8_list)
        new_data_list.append(data)

last_result = []
# 遍历增加了VIN8的数据生成真实VIN
for i in new_data_list:
    frame_num = i[3]
    year = i[2]
    # 遍历新数据中的所有VIN8
    for j in i[-1]:
        old_data = copy.deepcopy(i)
        old_data[5] = str(old_data[5])
        vin = be_really(frame_num, j, year)
        old_data.append(vin)
        last_result.append(old_data)
print(last_result)

# 结果写入CSV
write_csv('toyota_toyota_vin_info_color.csv', last_result)

