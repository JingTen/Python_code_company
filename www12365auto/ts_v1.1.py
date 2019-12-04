# coding=utf-8

import requests
from bs4 import BeautifulSoup
import time
import datetime
import pymysql


class GetURL(object):
    ''' 通过requests访问指定网页获取内容 '''
    def __init__(self):
        self.headers = {
            'Referer': 'http://www.12365auto.com/zlts/0-0-0-0-0-0_0-0-1.shtml',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36'
        }
        # 设置代理IP
        ip = '106.35.34.177'
        port = '4253'
        self.proxies = {
            'http': '%s:%s' % (ip, port),
            'https': '%s:%s' % (ip, port)
        }
        self.proxies = None
        self.now = datetime.datetime.now()
        self.year = self.now.year
        self.month = self.now.month
        self.day = self.now.day
        self.version = str(self.year) + str(self.month).zfill(2) + str(self.day).zfill(2)

    def get_problem_type_info(self, version_time='20191120'):
        '''获取最新投诉问题类型信息'''
        version_time = self.version
        url = 'http://www.12365auto.com/js/cTypeInfo.js?version={}'.format(version_time)
        r = requests.get(url, headers=self.headers, timeout=6, proxies=self.proxies)
        r.close()
        response = eval(r.text.replace('var cTypeInfo = ', '').replace('\r\n', ''))
        ts_problem_types = []
        for i in response:
            big_id = i['id']
            name = i['name']
            value = i['value']
            zf = i['zf']
            if zf == 'z':
                zf_name = '质量问题'
            elif zf == 'f':
                zf_name = '服务问题'
            else:
                zf_name = ''
            items = i['items']
            for ii in items:
                small_id = ii['id']
                title = ii['title']
                code = value + str(small_id)
                ts_problem_types.append([big_id, name, value, zf, zf_name, small_id, title, code])
        return ts_problem_types

    def get_series_info(self, version_time='20191120'):
        ''' 获取最新车系信息 '''
        version_time = self.version
        url = 'http://www.12365auto.com/js/brandsHaveSeries.js?version={}'.format(version_time)
        r = requests.get(url, headers=self.headers, timeout=6, proxies=self.proxies)
        r.close()
        r = eval(r.text.replace('var brandsHaveSeries = ', '').replace(';\r\n', '').replace('\n', ''))
        series_lists = []
        for i in r:
            id = i['id']
            name = i['name']
            initials = i['initials']
            brand_logo = i['brand_logo']
            brand_logo = brand_logo.replace('http://img.12365auto.com/f', '')
            brand_logo = 'http://img.12365auto.com/f' + brand_logo
            big_config = i['config']
            for ii in big_config:
                brandsId = ii['brandsId']
                brandsName = ii['brandsName']
                brandsIsInlet = ii['brandsIsInlet']
                small_config = ii['config']
                for iii in small_config:
                    seriesId = iii['seriesId']
                    seriesName = iii['seriesName']
                    seriesAttribute = iii['seriesAttribute']
                    series_logo = iii['series_logo']
                    series_logo = series_logo.replace('http://img.12365auto.com/f', '')
                    series_logo = 'http://img.12365auto.com/f' + series_logo
                    series_lists.append(
                        [id, name, initials, brand_logo, brandsId, brandsName, brandsIsInlet, seriesId, seriesName,
                         seriesAttribute, series_logo])
        return series_lists

    def get_page_html(self, page):
        '''依据页数获取投诉问题列表数据'''
        url = 'http://www.12365auto.com/zlts/0-0-0-0-0-0_0-0-{}.shtml'.format(page)
        r = requests.get(url, headers=self.headers, timeout=10, proxies=self.proxies)
        r.close()
        if r.status_code == 200:
            bsObj = BeautifulSoup(r.content, 'lxml')
            table = bsObj.find('div', {'class': 'tslb_b'}).find('table')
            tr = table.find_all('tr')[1:]
            ts_page_list = []
            # 遍历每条投诉信息
            for i in tr:
                single_ts = []
                info = i.find_all('td')
                # (1).获取投诉编号，投诉品牌，投诉车系，投诉车型，投诉简述，典型问题，投诉时间，投诉状态 8 项目基本信息
                for j in info:
                    single_ts.append(j.get_text())
                # (2).获取品牌id，车系id，车型id，服务问题
                bid = info[2].attrs['bid']
                sid = info[2].attrs['sid']
                mid = info[2].attrs['mid']
                fw = info[2].attrs['fw']
                # (3).获取每条投诉详细内容url
                description_url = i.find('td', {'class': 'tsjs'}).find('a').attrs['href']
                for k in [bid, sid, mid, fw, description_url]:
                    single_ts.append(k)
                ts_page_list.append(single_ts)
            return ts_page_list

    def get_tsnrANDtshf(self, url):
        # 初始化投诉内容和投诉回复列表
        tsnrANDtshf_list = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.6 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3"
        }
        try:
            r = requests.get(url, headers=headers, timeout=10, proxies=self.proxies)
            r.encoding = 'gb18030'
            r.close()
        except:
            print('%s 投诉详细内容获取失败！！！' % url)
            tsnrANDtshf_list = ['', '']
        else:
            if r.status_code == 200:
                bsObj = BeautifulSoup(r.text, 'html.parser')
                tsnr = bsObj.find('div', {'class': 'tsnr'})
                tshf = bsObj.find('div', {'class': 'tshf'})
                if tsnr and tshf:
                    tsnr_list = tsnr.find_all('p')
                    tsnr_deal = ''
                    for i in tsnr_list:
                        if i.get_text():
                            tsnr_deal += i.get_text()
                    tshf_list = tshf.find('p').get_text()
                    tsnrANDtshf_list.append(tsnr_deal)
                    tsnrANDtshf_list.append(tshf_list)
                else:
                    print('%s - 未成功获取投诉内容及投诉回复！' % url)
                    tsnrANDtshf_list = ['未成功获取', '未成功获取']
            elif r.status_code == 404:
                tsnrANDtshf_list = ['网页不存在', '网页不存在']
            else:
                print('%s 响应错误' % url)
                tsnrANDtshf_list = ['', '']
        return tsnrANDtshf_list


class ConnectMYSQL(object):
    ''' 连接数据库进行相关操作 '''
    def __init__(self):
        self.conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='12365auto', charset='utf8')
        self.cur = self.conn.cursor()
        self.cur.execute("USE 12365auto")
        self.ts_table = 'ts20191121'

    def close_mysql(self):
        self.cur.close()
        self.conn.close()

    def update_ts_problem_types(self, new_ts_problem_types):
        '''查询已有投诉问题类型表，获取最新投诉问题类型并更新'''
        select_sql = '''
            SELECT * FROM `ts_problem_types`
        '''
        self.cur.execute(select_sql)
        had_types = self.cur.fetchall()
        # 更新
        for new in new_ts_problem_types:
            single_type = tuple(new)
            if single_type not in had_types:
                insert_sql = '''
                    INSERT INTO `ts_problem_types`
                    (big_id,name,value,zf,zf_name,small_id,title,code)
                    VALUES 
                    {}
                '''.format(single_type)
                self.cur.execute(insert_sql)
        self.conn.commit()
        self.close_mysql()

    def update_series_info(self, new_series_lists):
        '''查询已有车系信息，获取最新车系信息并更新'''
        select_sql = '''
            SELECT * FROM `series_info`
        '''
        self.cur.execute(select_sql)
        had_series = self.cur.fetchall()
        # 更新
        for new in new_series_lists:
            single_series = tuple(new)
            if single_series not in had_series:
                insert_sql = '''
                    INSERT INTO `series_info`
                    (id, name, initials, brand_logo, brandsId, brandsName, brandsIsInlet, seriesId, seriesName,
                         seriesAttribute, series_logo)
                    VALUES 
                    {}
                '''.format(single_series)
                self.cur.execute(insert_sql)
        self.conn.commit()
        self.close_mysql()

    def select_problem_code(self):
        '''查询问题代码及其描述，方便与采集的问题代码进行匹配转换为文字描述'''
        sql = '''
            SELECT code,name,title,zf_name FROM `ts_problem_types`
        '''
        self.cur.execute(sql)
        result = self.cur.fetchall()
        self.close_mysql()
        problem_type_dict = {}
        if result != ((None,),):
            for i in result:
                problem_type_dict[i[0]] = {'name': i[1], 'title': i[2], 'zf_name': i[3],
                                           'description': i[1] + ':' + i[2]}
            return problem_type_dict
        else:
            return None

    def insert_into_ts_info(self, ts_page_result):
        '''更新投诉信息至数据库'''
        # 先查询已经采集的投诉ID
        sql = '''
            SELECT ts_id FROM `ts20191121`
        '''
        self.cur.execute(sql)
        had_ts_id = self.cur.fetchall()
        had_ts_id_list = [i[0] for i in had_ts_id]
        # 遍历每条投诉记录，判断更新或插入数据库
        for one_ts_list in ts_page_result:
            if str(one_ts_list[0]) not in had_ts_id_list:
                sql = '''
                    INSERT INTO {}
                    (ts_id,brand,series,model_name,brief_description,typical_problems_codes,date,state,brand_id,
                    series_id,model_id,description_url,quality_problem,service_problem,content,reply)
                    VALUES 
                    {};
                '''.format(self.ts_table, tuple(one_ts_list))
            else:
                sql = '''
                    UPDATE %s
                    SET brand = '%s',
                        series = '%s',
                        model_name = '%s',
                        brief_description = '%s',
                        typical_problems_codes = '%s',
                        date = '%s',
                        state = '%s',
                        brand_id = '%s',
                        series_id = '%s',
                        model_id = '%s',
                        description_url = '%s',
                        quality_problem = '%s',
                        service_problem = '%s',
                        content = '%s',
                        reply = '%s'
                    WHERE ts_id = '%s'
                ''' % (self.ts_table, one_ts_list[1], one_ts_list[2], one_ts_list[3], one_ts_list[4], one_ts_list[5],
                       one_ts_list[6], one_ts_list[7], one_ts_list[8], one_ts_list[9], one_ts_list[10], one_ts_list[11],
                       one_ts_list[12], one_ts_list[13], one_ts_list[14], one_ts_list[15], one_ts_list[0])
            self.cur.execute(sql)
        self.conn.commit()
        self.close_mysql()

    def select_fail_tsnrANDtshf(self):
        '''查询未成功采集的投诉内容及投诉回复记录'''
        sql = '''
            SELECT ts_id,description_url FROM {}
            WHERE content IN
            ('','未成功获取')
        '''.format(self.ts_table)
        self.cur.execute(sql)
        fail_result = self.cur.fetchall()
        fail_result_list = []
        if fail_result != ((None,),):
            for i in fail_result:
                fail_result_list.append(list(i))
        self.close_mysql()
        return fail_result_list

    def update_fail_tsnrANDtshf(self):
        '''失败的投诉内容及回复记录重新采集后更新至数据库'''
        sql = '''
            UPDATE {}
            SET 
            content = {},
            reply = {}
            WHERE ts_id = {}
        '''.format()

def analysis_problem_code(problem_type_dict, ts_page_list):
    ''' 解析投诉问题代码为文字描述 '''
    # 投诉结果新列表
    new_ts_page_list = []
    for i in ts_page_list:
        # 提取问题代码为列表
        codes_list = i[5].split(',')[:-1]
        # 提取服务问题分类字段：
        fw_str = i[11]
        fw_list = []
        if fw_str:
            fw_list = fw_str.split(',')
        # 解析问题代码
        quality_problem_text_list = []
        service_problem_text_list = []
        for j in codes_list:
            # 问题代码信息字典
            if j in problem_type_dict:
                code_info = problem_type_dict[j]
                code_text = code_info['name'] + ':' + code_info['title']
                code_zf_name = code_info['zf_name']
            else:
                print(j, '不在投诉问题类型字典中！！！')
                first_str = j[:1]
                problem_type_dict_keys = [_ for _ in problem_type_dict.keys()]
                for start in problem_type_dict_keys:
                    if start.startswith(first_str):
                        code_info = problem_type_dict[start]
                        code_text = code_info['name']
                        code_zf_name = code_info['zf_name']
                        break
            # 依据问题分类（质量问题或服务问题）加入对应列表
            if code_zf_name == '质量问题':
                quality_problem_text_list.append(code_text)
            elif code_zf_name == '服务问题':
                if code_info['name'] in fw_list:
                    fw_list.remove(code_info['name'])
                service_problem_text_list.append(code_text)
            else:
                pass
        # 服务问题特殊处理
        service_problem_text_list += fw_list
        # 处理质量问题，服务问题列表为单个字符串
        quality_problem_str = ';'.join(quality_problem_text_list)
        service_problem_str = ';'.join(service_problem_text_list)
        # 原单条投诉信息列表新增质量问题描述，服务问题描述
        del i[11]
        i.append(quality_problem_str)
        i.append(service_problem_str)
        new_ts_page_list.append(i)
    return new_ts_page_list


'''
# 1.检查投诉问题类型更新
# 1.1 访问投诉问题类型网页，获取最新类型
new_ts_problem_types = GetURL().get_problem_type_info()
# 1.2 类型检查更新(入库)
ConnectMYSQL().update_ts_problem_types(new_ts_problem_types)

# 2.检查车系
# 2.1 访问车系信息网页，获取最新车系信息
series_lists = GetURL().get_series_info()
# 2.1 车系检查更新(入库)
ConnectMYSQL().update_series_info(series_lists)
'''

# 3.获取问题代码及描述
problem_type_dict = ConnectMYSQL().select_problem_code()

# 4.遍历每页投诉网页，获取页面投诉信息
start_page = 1
end_page = 100
for page in range(start_page, end_page+1):
    print('第%s页（共%s页）投诉记录正在采集...' % (page, end_page))
    ts_page_list = GetURL().get_page_html(page)
    # 原网页投诉问题代码解析为文本描述
    new_ts_page_list = analysis_problem_code(problem_type_dict, ts_page_list)
    # 遍历每条投诉记录，获取详细投诉内容与回复内容
    ts_page_result = []
    for one_ts in new_ts_page_list:
        time.sleep(1.2)
        description_url = one_ts[11]
        tsnrANDtshf_list = GetURL().get_tsnrANDtshf(description_url)
        one_ts += tsnrANDtshf_list
        ts_page_result.append(one_ts)
    # 每页更新入库
    ConnectMYSQL().insert_into_ts_info(ts_page_result)
    print('第%s页（共%s页）投诉记录入库成功！' % (page, end_page))

'''
####### 未成功采集的投诉内容及投诉回复重新采集 ##########
# 查询未成功采集记录
fail_result_list = ConnectMYSQL().select_fail_tsnrANDtshf()
# 重新采集
if fail_result_list:
    success_result_list = []
    for fail in fail_result_list:
        fail_ts_id = fail[0]
        fail_url = fail[1]
        tsnrANDtshf_list = GetURL().get_tsnrANDtshf(fail_url)
        time.sleep(1)
        success_result_list.append(fail + tsnrANDtshf_list)

for i in success_result_list:
    print(i)
'''