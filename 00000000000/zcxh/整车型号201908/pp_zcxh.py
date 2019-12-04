# -*- coding: <encoding name> -*- : # -*- coding: utf-8 -*-
'''
车型库 匹配燃油&工信部组合数据
'''

import csv
import ast
import codecs

# 定义长宽高函数
def longAndhigh(ckg_list,ckg2):
    for i in ckg_list:
        if i not in ckg2:
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


ry_dict = {}
with open('ry.csv','r') as csvfile:
    reader = csv.reader(csvfile)

    for line in reader:
        #print(line)
        k = line[0]
        v = line[1]
        v = ast.literal_eval(v)
        #print(v)
        ry_dict[k] = v

csvfile.close()



cxk_dict = {}
with open('cxk.csv','r') as cxkfile:
    reader = csv.reader(cxkfile)

    for line in reader:
        k = line[0]
        v = line[1]
        v = ast.literal_eval(v)
        cxk_dict[k] = v
cxkfile.close()



# 初始化匹配结果
result = []
# 遍历车型库
for k1,v1 in cxk_dict.items():
    id = k1

    print("%s---正在匹配" % id)

    for k11,v11 in v1.items():
        xdtj1 = k11
        ckg_list = v11

        # 遍历燃油&工信部数据
        for k2,v2 in ry_dict.items():
            bh = k2

            for k22,v22 in v2.items():
                xdtj2 = k22
                ckg2 = v22

                # 开始匹配
                # 判断限定条件
                if xdtj1 == xdtj2:

                    # 判断长宽高
                    if longAndhigh(ckg_list,ckg2):
                        result.append([id,bh])

# 结果写入CSV文件
resultfile = open('result.csv','w',newline='',encoding='utf-8')

writer = csv.writer(resultfile)

for i in result:
    writer.writerow(i)

resultfile.close()

# 结果文件转换格式
utf8_2_gbk(result.csv)

print('结果输出完毕！')



