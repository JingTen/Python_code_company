# coding=utf-8
import pymysql

class ConnectMysql(object):
    '''数据库操作'''
    def __init__(self):
        self.conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='second_hand_car_info',
                                    charset='utf8')
        self.cur = self.conn.cursor()
        self.cur.execute("USE second_hand_car_info")

    def close_connect(self):
        self.cur.close()
        self.conn.close()

    def carinfo_insert_into_mysql(self, lists):
        '''车辆信息写入数据库'''
        for i in lists:
            i_no_html = i[:-1]
            sql = """INSERT INTO `second_hand_car`
            (info_id,mobile_url,publicdate,title,province,city,brandid,seriesid,specid,vincode,price,mileage,carAge,
            trans,power,registedate,guo_hu,how_much_guo,color,license_plate_area) 
            VALUES 
            {};""".format(tuple(i_no_html))
            self.cur.execute(sql)
            self.conn.commit()
        self.close_connect()

    def html_insert_into_mysql(self, lists):
        '''车辆网页源码写入数据库'''
        for i in lists:
            sql = """INSERT INTO 
            `second_hand_car_html`
            (mobile_url,html)
            VALUES 
            ('%s','''%s''');""" % (i[1], pymysql.escape_string(i[-1]))
            self.cur.execute(sql)
            self.conn.commit()
        self.close_connect()

    def select_had_info_id(self):
        '''查找已采集的info_id'''
        sql = '''
            SELECT info_id FROM `second_hand_car`
        '''
        self.cur.execute(sql)
        had_info = self.cur.fetchall()
        had_info_list = [i[0] for i in had_info]
        self.close_connect()
        return had_info_list

    def select_area_info(self):
        '''获取地区信息'''
        area_dict = {}
        sql = '''
            SELECT province_id, province, city_id, city
            FROM `area_info`
        '''
        self.cur.execute(sql)
        result = self.cur.fetchall()
        self.close_connect()
        for i in result:
            if i[0] not in area_dict:
                area_dict[i[0]] = i[1]
            if i[2] not in area_dict:
                area_dict[i[2]] = i[3]
        return area_dict


    def update_area_info(self, lists):
        '''更新地区信息表'''
        select_sql = '''
            SELECT city_id FROM `area_info`
        '''
        self.cur.execute(select_sql)
        select_result = self.conn.commit()
        if select_result:
            select_result_list = [_[0] for _ in select_result]
        else:
            select_result_list = []
        for i in lists:
            if i[5] not in select_result_list:
                sql = '''
                    INSERT INTO `area_info`
                    (nu, province, province_id, province_py, city, city_id, city_py)
                    VALUES {};
                '''.format(tuple(i))
            self.cur.execute(sql)
        self.conn.commit()
        self.close_connect()



class TipToTXT(object):
    '''采集成功与否记录写入txt文件'''
    def __init__(self):
        pass

    def records_txt(selfm, tips):
        with open('SecondHandCarVincode.txt', 'a+') as f:
            f.write(tips + '\n')



