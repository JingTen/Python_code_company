import pymysql
import json
import hashlib

# 采集成功与否记录写入txt文件
def records_txt(tips):
    records_file = open('666.txt', 'a+')

    records_file.write(str(tips) + '\n')

    records_file.close()


# 处理content后写入数据库
def insert_into_mysql(lists, table_name):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')

    cur = conn.cursor()

    cur.execute("USE gm_chevrolet")

    try:
        if table_name == 'vin_hash':
            sql = """INSERT INTO 
            vin_hash 
            (country,region,manufacturer,model,bodyType,constraintType,engineType,checkPos,modelYear,assemblyFactory,sequence,vin,series,body,productMonth,optionCodes,hash) 
            VALUES 
            ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',"%s",'%s');""" % (lists[0], lists[1], lists[2], lists[3], lists[4], lists[5], lists[6], lists[7], lists[8], lists[9],
               lists[10], lists[11], lists[12], lists[13], lists[14], lists[15], lists[16])

            #print(sql)

            cur.execute(sql)
            conn.commit()

        elif table_name == 'vin_codes':
            for i in lists:
                sql = """INSERT INTO 
                vin_codes 
                (optionCode,descriptionCN,descriptionEN) 
                VALUES 
                ("%s","%s","%s");""" % (i[0], i[1], i[2])

                #print(sql)

                cur.execute(sql)
                conn.commit()

    finally:
        cur.close()
        conn.close()

def deal_with_content(content):
    '''
    处理单个字典形式content
    返回两个列表：
    1.单个vin基本信息列表
    2.配置代码及中英文解析列表
    '''
    vin_info_list = []  # 初始化vin基本信息列表
    optionCode_list = []  # 初始化配置代码列表
    optionCode_description_list = []  # 初始化配置代码描述列表

    # 当content结果中有键-vin且共有16组键值对时，默认采集成功（结果结构一致，存在rpos为空的情况）
    if 'vin' in content and len(content) == 16:

        # 遍历固定顺序结构的16个键值对
        for k, v in content.items():

            # 当轮到配置代码键值对且不为空时，提取配置代码

            if k == 'rpos' and v is not None:
                for i in v:
                    # print(i['optionCode'],i['descriptionCN'],i['descriptionEN'])
                    optionCode_description_list.append([i['optionCode'], i['descriptionCN'], i['descriptionEN']])
                    optionCode_list.append(i['optionCode'])

            else:
                vin_info_list.append(v)

        # vin基本信息列表最后添加optionCode_list及其hash值(以md5形式生成16进制的32位哈希值)
        vin_info_list.append(optionCode_list)
        vin_info_list.append(hashlib.md5(str(optionCode_list).encode('utf8')).hexdigest())

        return vin_info_list, optionCode_description_list

# 读取VIN采集信息进行解析并存入VIN解析表
def dispose_of_vin_info(table_name):
    conn1 = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')

    cur1 = conn1.cursor()

    cur1.execute("USE gm_chevrolet")

    try:
        sql = """SELECT content
        FROM %s
        WHERE LEFT(vin,3) = 'LSG'
        AND LEFT(content,10) = '{"country"'
        AND (insert_time BETWEEN '2019-09-08' AND '2019-09-09');
        """ % table_name

        # 执行sql语句
        cur1.execute(sql)

        # 获取所有记录列表
        results = cur1.fetchall()

        # 记录总数
        all_num = len(results)
        count = 0

        for content in results:
            count += 1

            # json加载字符串形式的字典时，null会自动转化为None
            content = json.loads(content[0])

            # 单个处理content
            vin_info_list, optionCode_description_list = deal_with_content(content)

            # 处理结束，将结果存入数据库中的vin_hash和vin_codes表
            insert_into_mysql(vin_info_list, 'vin_hash')
            insert_into_mysql(optionCode_description_list, 'vin_codes')

            print('第%s条(共%s条)数据写入成功...' %(count,all_num))

    finally:
        cur1.close()
        conn1.close()



dispose_of_vin_info('epc_vin_info_test')










