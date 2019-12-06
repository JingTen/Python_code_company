# coding=utf-8
'''京东底盘号匹配
锁定条件：
京东厂商品牌车系组合字段、排量、车门数、功率、长度

'''

import csv
import codecs

def read_csv(file_name):
    '''读取csv文件为列表'''
    with open(file_name, 'r') as f:
        reader = csv.reader(f)
        result = list(reader)
        return result

def write_csvfile(lists):
    '''结果写入csv文件'''
    with open('result.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for i in lists:
             writer.writerow(i)


def utf8_2_gbk(oldfile):
    '''utf8转为gbk'''
    newfile = "gbk_%s" % oldfile
    with codecs.open(oldfile, 'r', 'utf-8') as f:
        utf_str = f.read()
        out_gbk_str = utf_str.encode('GB18030')
    with open(newfile, 'wb') as f1:
        f1.writer(out_gbk_str)



# 文件读取
jd_file_name = 'jd.csv'
cxk_file_name = 'cxk.csv'
jd = read_csv('jd.csv')
cxk = read_csv('cxk.csv')
print(cxk)
print(jd)

# 结果字典初始化
result = {}
# 遍历匹配
# 汽车之家车型库遍历
for one_cxk in cxk:
    cxk_id = one_cxk[0]
    cxk_series = one_cxk[1]
    cxk_pl = one_cxk[2]
    cxk_door = one_cxk[3]
    cxk_power = one_cxk[4]
    cxk_long = one_cxk[5]
    # 京东车型库遍历
    for one_jd in jd:
        dp_id = one_jd[0]
        dp_series = one_jd[1]
        dp_pl = one_jd[2]
        dp_door = one_jd[3]
        dp_power = one_jd[4]
        dp_long = one_jd[5]
        dp_code = one_jd[6]
        # 车系匹配
        if cxk_series == dp_series:
            # 排量匹配
            if cxk_pl == dp_pl or (not cxk_pl or not dp_pl):
                # 车门匹配
                if (not cxk_door or not dp_door) or cxk_door == dp_door:
                    # 功率匹配
                    if (not cxk_power or not dp_power) or abs(float(cxk_power)-float(dp_power)) <= 2:
                        # 长度匹配
                        if (not cxk_long or not dp_long) or abs(int(cxk_long)-int(dp_long)) <= 2:
                            if cxk_id not in result:
                                result[cxk_id] = [dp_code]
                            else:
                                result[cxk_id].append(dp_code)
                                result[cxk_id] = list(set(result[cxk_id]))
result_list = []
for k, v in result.items():
    dp_codes = ';'.join(v)
    result_list.append([k, dp_codes])
print(len(result_list))










