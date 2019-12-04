# coding=utf-8
'''
丰田和雷克萨斯通过EPC颜色代码查找符合条件的VIN
'''

import pymysql
import requests
from bs4 import BeautifulSoup
import re

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

def select_vin_by_color(color_code):
    conn = pymysql.connect(host='192.168.3.110', user='jing', passwd='123456', db='toyota_201910', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE toyota_201910")
    sql = '''
    SELECT T1.*,`feature_vin`.vin_head
    FROM
        `feature_vin`,
        (SELECT head_ofs,frame_num,LEFT(prod_date,4),color
        FROM `feature_frame_less_data_for_carcolor`
        WHERE color = '{}'
        AND LEFT(prod_date,4) > 2013
        GROUP BY head_ofs) AS T1
    WHERE 
        T1.head_ofs = `feature_vin`.head_ofs 
        AND LEFT(`feature_vin`.vin_head,3) IN (
            'LFM', 'LVG', 'JTE', 'JTM', 'LTV', 'JTN', '5TD', '5TF', 'JF1', 'LCU', 'LFB', 'JTF', 'MHF', 'JTK', 'MR1', 'LFP', 
            '4T3', 'JTG', 'JTD', 'JTB', 'LTU', 'JT5', 'LF4', 'LAG', '2FM', 'JZS', 'L25', 'GGH', 'LVR', 'JT1', 'JLE', '2TE', 
            'GTJ', 'LPM', 'LGB', 'WBA', '5FM', 'LF0'
        )
    ORDER BY FIELD(LEFT(`feature_vin`.vin_head,3),'LFM', 'LVG', 'JTE', 'JTM', 'LTV', 'JTN', '5TD', '5TF', 'JF1', 'LCU', 'LFB', 'JTF', 'MHF', 'JTK', 'MR1', 'LFP', '4T3', 'JTG', 'JTD', 'JTB', 'LTU', 'JT5', 'LF4', 'LAG', '2FM', 'JZS', 'L25', 'GGH', 'LVR', 'JT1', 'JLE', '2TE', 'GTJ', 'LPM', 'LGB', 'WBA', '5FM', 'LF0')
    LIMIT 10;'''.format(color_code)
    cur.execute(sql)
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

def get_color_from_sjb(vin):
    '''数据宝刷数据'''
    # 设置请求头
    headers = {
        'Cookie': 'PHPSESSID=254mq8cqla25sn6hu9pcbh6hfc',
        'Host': 'vin-tools',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3'
    }
    url = 'http://vin-tools/index.php/Home/CatarcTools/QueryEngineCode?vin={}&full_data=1&tdsourcetag=s_pctim_aiomsg'.format(vin)
    r = requests.get(url, headers=headers, timeout=6)
    if r.status_code == 200:
        bsObj = BeautifulSoup(r.text, 'lxml')
        body = bsObj.find('pre')
        content = body.get_text()
        model_id = re.compile('车型ID：[0-9]{0,10}车型名称').search(content)
        color_name = re.compile('颜色：[\S|\s]{0,15}生产时间').search(content)
        if model_id:
            model_id = model_id.group().replace('车型ID：', '').replace('车型名称', '')
        else:
            model_id = ''
        if color_name:
            color_name = color_name.group().replace('颜色：', '').replace('生产时间', '')
        else:
            color_name = ''
        return [model_id, color_name]
    else:
        return None

color_list = ['1H4']
result_list = []
# 依据color_code查前几条VIN信息
for color in color_list:
    print('正在查找符合条件的车架号信息...', color)
    vins = select_vin_by_color(color)
    # 依据VIN信息推算真实VIN
    for i in vins:
        frame_num = i[1]
        vin_head = i[4][:8]
        year = i[2]
        vin = be_really(frame_num, vin_head, year)
        # 依据真实VIN刷数据宝颜色数据
        model_id_AND_color = get_color_from_sjb(vin)
        if model_id_AND_color:
            result_list.append([vin, color] + model_id_AND_color)
            if model_id_AND_color[1] != '':
                break
    print('该color_code结束', color)
print(result_list)

