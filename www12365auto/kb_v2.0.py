# coding=utf-8
'''
车质网口碑数据采集（存入数据库）
'''
from urllib.request import urlopen
import json
from bs4 import BeautifulSoup
import requests
import time
import pymysql

# 直接获取某页面的口碑记录列表
def get_html_list(page):
    # 手机端网页json数据可直接加载，只是口碑记录中的部分字段（优点、缺点、总结）显示几乎不完整
    url = 'http://m.12365auto.com/Server/forSeries.ashx?act=ReputationAppend&i=%d&s=5&bid=0&sid=0&mid=0&od=0' % page
    html = urlopen(url).read().decode('utf-8')
    html_list = json.loads(html)
    return html_list

# 修正手机端网页数据部分字段显示不全问题
def change_good_bad_content(id, sid):
    # 请求头设置
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Host": "m.12365auto.com"}
    # 依据每条口碑记录的cid,sid获取该记录手机端的详细信息网页URL（其HTML信息完整）
    url = "http://m.12365auto.com/carseries/reputationInfo.aspx?cid=%d&sid=%d" % (id, sid)
    try:
        html = session.get(url, headers=headers, timeout=20)
        html.close()
    except:
        print('ID:%d Sid:%d 访问失败！！！' % (id, sid))
        return None
    else:
        if html.status_code == 200:
            # 解析HTML获取优点，缺点，总结 及车型主图链接
            bsObj = BeautifulSoup(html.content, 'lxml')
            three_points = bsObj.findAll('div', {'class': 'box'})
            if len(three_points) == 3:
                good = three_points[0].find('p').get_text()
                bad = three_points[1].find('p').get_text()
                content = three_points[2].find('p').get_text()
                # 获取图片链接
                img = bsObj.find('div', {'class': 'cxnr'}).find('img').attrs['src']
                return [good, bad, content, img]
            else:
                return None
        else:
            return None

# 解析口碑记录字典
def analysis_kb_json(ks_json):
    analysis_lists = []
    # 尝试解析
    try:
        # 遍历每条口碑记录字典
        for kb_dict in ks_json:
            # 提取口碑字典中的所有信息
            BrandName = kb_dict['BrandName']
            SeriesName = kb_dict['SeriesName']
            ModelsName = kb_dict['ModelsName']
            kbDate = kb_dict['kbDate']
            UserName = kb_dict['UserName']
            ID = kb_dict['ID']
            Stars = kb_dict['Stars']
            Title = kb_dict['Title']
            Good = kb_dict['Good']
            Bad = kb_dict['Bad']
            Content = kb_dict['Content']
            Agree = kb_dict['Agree']
            Photo = kb_dict['Photo']
            Count = kb_dict['Count']
            Sid = kb_dict['Sid']

            one_kb_list = [ID, UserName, kbDate, BrandName, SeriesName, ModelsName, Sid, Title, Good, Bad, Content,
                           Stars, Agree, Count, Photo]
            analysis_lists.append(one_kb_list)
        return analysis_lists
    except:
        print('JSON解析出错')
        return None

def kb_info_insert_into_MySQL(kb_lists):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE 12365auto")
    # 先查询已采集的KB_ID
    sql = '''
        SELECT KB_ID FROM `kb20191115`
    '''
    cur.execute(sql)
    run_KB_ID = cur.fetchall()
    run_KB_ID_list = [ii[0] for ii in run_KB_ID]
    # 遍历每条口碑记录，判断更新或插入数据库
    for one_kb_list in kb_lists:
        if str(one_kb_list[0]) not in run_KB_ID_list:
            sql = '''
                INSERT INTO `kb20191115`
                (KB_ID, UserName, kbDate, BrandName, SeriesName, ModelsName, Sid, Title, Good, Bad, Content, 
                    Stars, Agree, Count, Photo)
                VALUES
                {}; 
            '''.format(tuple(one_kb_list))
        else:
            sql = '''
                UPDATE `kb20191115`
                SET UserName = '%s',
                    kbDate = '%s',
                    BrandName = '%s',
                    SeriesName = '%s',
                    ModelsName = '%s',
                    Sid = '%s',
                    Title = '%s',
                    Good = '%s',
                    Bad = '%s',
                    Content = '%s',
                    Stars = '%s',
                    Agree = '%s',
                    Count = '%s',
                    Photo = '%s'
                WHERE KB_ID = '%s'
            ''' % (one_kb_list[1],one_kb_list[2],one_kb_list[3],one_kb_list[4],one_kb_list[5],one_kb_list[6],
                   one_kb_list[7],one_kb_list[8],one_kb_list[9],one_kb_list[10],one_kb_list[11],one_kb_list[12],
                   one_kb_list[13],one_kb_list[14],one_kb_list[0])
        cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

############################### ↓↓↓↓↓↓ 数据采集 ↓↓↓↓↓↓ ###############################

# 口碑最大页数
page_max = 150
# 初始化口碑总列表
kb_lists = []
# 尝试获取每个页面口碑记录列表，并存入口碑总列表
# 遍历每页口碑网页
for page in range(1, page_max+1):
    print("第%d页口碑JSON记录正在采集..." % page)
    # 直接获取每页5条口碑JSON记录（优点，缺点，总结通常不完整）
    page_list = get_html_list(page)
    # 获取每条口碑具体页面HTML，解析完整的优点，缺点，总结及图片链接，更新原JSON记录
    for i in page_list:
        id = i['ID']
        sid = i['Sid']
        time.sleep(2)
        three_points_Photo = change_good_bad_content(id, sid)
        if three_points_Photo:
            i['Good'] = three_points_Photo[0]
            i['Bad'] = three_points_Photo[1]
            i['Content'] = three_points_Photo[2]
            i['Photo'] = three_points_Photo[3]
        else:
            print("第%d页口碑记录获取详细信息存在遗漏。。" % page)
    # 解析口碑记录
    analysis_lists = analysis_kb_json(page_list)
    # 每页口碑记录存入数据库
    kb_info_insert_into_MySQL(analysis_lists)
    print("第%d页口碑记录成功入库！！！" % page)

