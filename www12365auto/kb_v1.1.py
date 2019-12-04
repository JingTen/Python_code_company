# coding=utf-8
'''
车质网口碑数据采集（存入数据库）
'''
from urllib.request import urlopen
import json
import csv
import codecs
from bs4 import BeautifulSoup
import requests
import time


# 直接获取某页面的口碑记录列表
def get_html_list(page):
    # 手机端网页json数据可直接加载，只是口碑记录中的部分字段（优点、缺点、总结）显示几乎不完整
    url = 'http://m.12365auto.com/Server/forSeries.ashx?act=ReputationAppend&i=%d&s=5&bid=0&sid=0&mid=0&od=0' % page
    html = urlopen(url).read().decode('utf-8')
    html_list = json.loads(html)
    return html_list

# 修正手机端网页数据部分字段显示不全问题
def change_good_bad_content(cid, sid):
    # 设置睡眠
    if cid % 200 == 0:
        time.sleep(5)
    else:
        time.sleep(1)
    # 尝试获取三个字段完整信息，并存入字典
    # 避免同个用户cid会有多个同车系sid的口碑记录时不知是否会报错？？
    try:
        # 依据每条口碑记录的cid,sid获取该记录手机端的详细信息网页URL（其HTML信息完整）
        url = "http://m.12365auto.com/carseries/reputationInfo.aspx?cid=%d&sid=%d" % (cid, sid)
        html = session.get(url, headers=headers).content
        bsObj = BeautifulSoup(html, 'lxml')
        three_points = bsObj.findAll('div', {'class': 'box'})
        good = three_points[0].find('p').get_text()
        bad = three_points[1].find('p').get_text()
        content = three_points[2].find('p').get_text()
        change_dict = {'Good': good,
                       'Bad': bad,
                       'Content': content}
    except:
        change_dict = {}
        time.sleep(10)
    return change_dict

# 将口碑总列表写入csv文件
def write_newcsvfile(lists):
    csvfile = open('kb.csv', 'w', newline='', encoding='utf-8')
    writer = csv.writer(csvfile)
    # 标题列表
    title_list = ['ID', 'UserName', 'kbDate', 'BrandName', 'SeriesName', 'ModelsName', 'Sid', 'Title', 'Good', 'Bad',
                  'Content', 'Stars', 'Agree', 'Count']
    # 写入标题
    writer.writerow(title_list)
    # 遍历口碑总列表中每个页面的记录列表
    for list in lists:
        # 遍历每个页面记录列表中每条字典记录
        for dict in list:
            # 初始化每条口碑记录的列表
            kb_one_list = []
            # 通过每条字典记录获取用户ID和车系Sid；
            # 手机端每条记录URL详细记录修正三个字段
            cid = dict['ID']
            sid = dict['Sid']
            change_dict = change_good_bad_content(cid, sid)
            # 判断change_dict不为空时，修正三个字段；为空时，保留原记录
            if change_dict:
                dict['Good'] = change_dict['Good']
                dict['Bad'] = change_dict['Bad']
                dict['Content'] = change_dict['Content']
            else:
                pass
            # 遍历标题列表，按其顺序存入每条口碑记录列表
            for title in title_list:
                kb_one_list.append(dict[title])
            # 写入每条口碑记录
            writer.writerow(kb_one_list)
            # print(kb_one_list)
    # 关闭文件
    csvfile.close()

def utf8_2_gbk(oldfile, newfile='kb_for_gbk.csv'):
    f = codecs.open(oldfile, 'r', 'utf-8')
    utfstr = f.read()
    f.close()
    out_gbk_str = utfstr.encode('GB18030')
    f = open(newfile, 'wb')
    f.write(out_gbk_str)
    f.close()

# 请求头设置
session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"}
# 口碑最大页数
page_max = 350
# 初始化口碑总列表
kb_lists = []
# 尝试获取每个页面口碑记录列表，并存入口碑总列表
try:
    # 循环遍历每一个口碑页面
    for page in range(1, page_max):
        # 设置睡眠
        if page % 100 == 0:
            time.sleep(10)
        else:
            time.sleep(3)
        print("第%d页口碑JSON记录正在采集..." % page)
        page_list = get_html_list(page)
        kb_lists.append(page_list)
        print("第%d页口碑JSON记录采集完成！" % page)
# 无论尝试部分是否报错，最后都将已存入口碑总列表中的数据写入csv（utf-8）文件；
# 并另存为gbk编码形式的csv文件（避免EXCEL直接打开会乱码）；
finally:
    print("正在写入CSV文件...")
    write_newcsvfile(kb_lists)
    utf8_2_gbk(oldfile='kb.csv')

print("Game Over!")



