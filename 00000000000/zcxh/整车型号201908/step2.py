# -*- coding: <encoding name> -*- : # -*- coding: utf-8 -*-
'''
车型库 匹配燃油&工信部组合之外数据（燃油进口）

圈定车系匹配
'''

import csv
import ast
import codecs


# 定义判断函数
def StrListInStr(str_list, str2):
    for i in str_list:
        if i not in str2:
            return False
    return True


def utf8_2_gbk(oldfile):
    # 设置新文件名称
    newfile = "gbk_%s" % oldfile

    f = codecs.open(oldfile, 'r', 'utf-8')
    utf_str = f.read()
    f.close()

    out_gbk_str = utf_str.encode('GB18030')

    f = open(newfile, 'wb')
    f.write(out_gbk_str)
    f.close()


# 车型库车型名称：{限定条件：车系}
# 初始化车型库车系字典
cxkcx_dict = {}

with open('cxk_jkpp.csv', 'r') as csvfile:
    reader = csv.reader(csvfile)

    for line in reader:
        k = line[0]
        v = line[1]
        cxkcx_dict[k] = v
csvfile.close()

print(cxkcx_dict)
print(len(cxkcx_dict))