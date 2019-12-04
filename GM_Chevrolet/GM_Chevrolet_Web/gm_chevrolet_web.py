'''
通用雪佛兰工具网页

'''

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
import pymysql
from collections import Counter
import hashlib
import time

app = Flask(__name__)

bootstrap = Bootstrap(app)


###############↓--↓--↓--↓--↓--↓-BEGIN 选配置生成动态分组逻辑-↓--↓--↓--↓--↓--↓--↓################
def SQL_MSB():
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE gm_chevrolet")

    sql = '''
    SELECT 
        table1.model,table1.series,table1.body,
        MIN(table2.productMonth) AS '生产开始时间',
        MAX(table2.productMonth) AS '生产结束时间',
        table1.`VIN数量`
    FROM
        (SELECT 
            model,series,body,COUNT(*) AS 'VIN数量' 
            FROM `gm_chevrolet`.`vin_hash` 
            WHERE hash != '[]'
            GROUP BY model,series,body) table1
    LEFT JOIN
        (SELECT 
            model,series,body,productMonth 
            FROM `gm_chevrolet`.`vin_hash`  
            WHERE productMonth NOT LIKE '1%' AND productMonth != 'None') table2

    ON (table1.model = table2.model AND table1.series = table2.series AND table1.body = table2.body) 
    GROUP BY table1.model,table1.series,table1.body,table1.`VIN数量`
    ORDER BY table1.model,table1.series,table1.body;
    '''

    cur.execute(sql)
    results = cur.fetchall()
    conn.close()

    return results

def SQL_MSBV(model, series, body):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE gm_chevrolet")

    sql = '''
    SELECT 
        table1.model,table1.series,table1.body,
        table1.`VIN8`,
        MIN(table2.productMonth) AS '生产开始时间',
        MAX(table2.productMonth) AS '生产结束时间',
        table1.`VIN数量`
    FROM
        (SELECT
            model,series,body,LEFT(vin,8) AS 'VIN8',COUNT(*) AS 'VIN数量'
            FROM `gm_chevrolet`.`vin_hash` 
            WHERE `model` = "%s" AND `series` = "%s" AND `body` = "%s" AND hash != '[]'
            GROUP BY model,series,body,LEFT(vin,8)) table1
    LEFT JOIN
        (SELECT 
            model,series,body,LEFT(vin,8) AS 'VIN8',productMonth 
            FROM `gm_chevrolet`.`vin_hash`  
            WHERE LEFT(productMonth,1) != '1' AND productMonth != 'None') table2
    ON
        (table1.model = table2.model AND table1.series = table2.series AND table1.body = table2.body AND table1.`VIN8` = table2.`VIN8`) 
    GROUP BY table1.`VIN8`
    ORDER BY table1.`VIN数量` DESC;
    ''' % (model, series, body)

    cur.execute(sql)
    results = cur.fetchall()
    conn.close()

    return results

def SQL_MSBVS(model, series, body, VIN8):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE gm_chevrolet")

    sql_hash = '''
        SELECT optionCodes FROM `gm_chevrolet`.`vin_hash` 
        WHERE hash != '[]' AND `model` = "%s" AND `series` = "%s" AND `body` = "%s" AND LEFT(vin,8) = "%s"
    ''' % (model, series, body, VIN8)

    cur.execute(sql_hash)
    results_hash = cur.fetchall()

    # 每个VIN的所有配置代码存入同一个列表，已备统计
    all_codes = []
    for i in results_hash:
        all_codes.extend(eval(i[0]))

    # 每个配置代码出现的次数以字典形式存储
    all_codes_count = Counter(all_codes)

    # 列表去重
    all_codes = list(set(all_codes))

    # 对原始列表进行排序
    all_codes.sort()

    # 转化为tuple，方便SQL语句导入变量
    all_codes = tuple(all_codes)

    # 查询所有code对应的中文描述
    sql = '''
        SELECT optionCode,descriptionCN FROM vin_codes
        WHERE optionCode in {}
        ORDER BY optionCode;
    '''.format(all_codes)

    cur.execute(sql)
    results_descriptionCN = cur.fetchall()

    # 将配置代码与中文描述结果（元组里面有元组）转成字典形式
    results_descriptionCN_dict = {}
    for i in results_descriptionCN:
        results_descriptionCN_dict[i[0]] = i[1]

    conn.close()

    return all_codes_count, results_descriptionCN_dict

def SQL_MSBVS_table_display(model, series, body, VIN8):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE gm_chevrolet")

    sql = '''
    SELECT 
        table1.model,table1.series,table1.body,
        table1.`VIN8`,
        MIN(table2.productMonth) AS '生产开始时间',
        MAX(table2.productMonth) AS '生产结束时间',
        table1.`VIN数量`
    FROM
        (SELECT
            model,series,body,LEFT(vin,8) AS 'VIN8',COUNT(*) AS 'VIN数量'
            FROM `gm_chevrolet`.`vin_hash` 
            WHERE `model` = "%s" AND `series` = "%s" AND `body` = "%s" AND hash != '[]' AND LEFT(vin,8) = "%s"
            GROUP BY model,series,body,LEFT(vin,8)) table1
    LEFT JOIN
        (SELECT 
            model,series,body,LEFT(vin,8) AS 'VIN8',productMonth 
            FROM `gm_chevrolet`.`vin_hash`  
            WHERE LEFT(productMonth,1) != '1' AND productMonth != 'None') table2
    ON
        (table1.model = table2.model AND table1.series = table2.series AND table1.body = table2.body AND table1.`VIN8` = table2.`VIN8`) 
    GROUP BY table1.`VIN8`
    ORDER BY table1.`VIN数量` DESC;
    ''' % (model, series, body, VIN8)

    cur.execute(sql)
    results = cur.fetchall()
    conn.close()

    return results

# 加入对比配置代码（重置），生成动态hash
def SQL_MSBVS_SetCompare(model, series, body, VIN8, check_codes):
    # 连接数据库，查询符合条件数据
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE gm_chevrolet")

    ###############↓--↓--↓--↓--↓--↓-BEGIN 删除符合车型条件的动态分组数据-↓--↓--↓--↓--↓--↓--↓################
    sql_delete = '''
        DELETE FROM `vin_result`
        WHERE
            `vin_result`.Model = '%s'
            AND `vin_result`.Series = '%s'
            AND `vin_result`.Body = '%s'
            AND `vin_result`.VIN8 = '%s';
    ''' % (model, series, body, VIN8)

    cur.execute(sql_delete)
    conn.commit()
    ###############↑--↑--↑--↑--↑--↑-END  删除符合车型条件的动态分组数据-↑--↑--↑--↑--↑--↑--↑################


    sql = '''
        SELECT model,series,body,LEFT(vin,8) AS 'VIN8',optionCodes 
        FROM `vin_hash`
        WHERE `model` = '%s' AND `series` = '%s' AND `body` = '%s' AND LEFT(vin,8) = '%s'
        GROUP BY optionCodes;
    ''' % (model, series, body, VIN8)

    cur.execute(sql)
    results = cur.fetchall()

    # 遍历每条符合条件的查询结果
    for i in results:

        # 提取每条记录的所有配置代码列表，遍历已选择的对比项配置代码，确认两列表的包含关系（YesOrNo）
        optionCodes = eval(i[4])

        # 初始化YesOrNo列表
        YesOrNo = []

        for check_code in check_codes:
            if check_code in optionCodes:
                YesOrNo.append('Yes')
            else:
                YesOrNo.append('No')

        # 动态hash条件 = 前部车系条件(除去optionCodes) + 后部动态条件
        dynamic_hash_condition = tuple(list(i)[:-1]) + tuple([str(check_codes), str(YesOrNo)])

        # 动态hash条件生成动态hash值（以md5形式生成16进制的32位哈希值）
        dynamic_hash = hashlib.md5(str(dynamic_hash_condition).encode('utf8')).hexdigest()

        # 动态条件及动态hash结果入库，等待匹配
        insert_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        dynamic_result = i + tuple([str(check_codes), str(YesOrNo)]) + (dynamic_hash,insert_time,)

        sql_insert = '''
            INSERT INTO `vin_result` (Model,Series,Body,VIN8,optionCodes,CheckCodes,YesOrNo,DynamicHash,InsertTime)
            VALUES{}
        '''.format(dynamic_result)

        cur.execute(sql_insert)
        conn.commit()

    conn.close()

# 获取动态hash分组结果
def SQL_MSBVS_GetDynamicHash(model, series, body, VIN8):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE gm_chevrolet")

    sql = '''
        SELECT `vin_result`.DynamicHash,`vin_result`.CheckCodes,`vin_result`.YesOrNo,COUNT(*)
        FROM `vin_hash`
        LEFT JOIN `vin_result`
        ON
            `vin_hash`.`model` = `vin_result`.Model
            AND `vin_hash`.`series` = `vin_result`.Series 
            AND `vin_hash`.`body` = `vin_result`.Body
            AND LEFT(`vin_hash`.`vin`,8) = `vin_result`.VIN8
            AND `vin_hash`.optionCodes = `vin_result`.optionCodes
        WHERE
            `vin_result`.Model = '%s'
            AND `vin_result`.Series  = '%s'
            AND `vin_result`.Body = '%s'
            AND `vin_result`.VIN8 = '%s'
        GROUP BY DynamicHash;
        ''' % (model, series, body, VIN8)

    cur.execute(sql)
    results = cur.fetchall()

    # 单独提取对比配置代码列表，方便展示操作
    if results:
        CheckCodes_list = eval(results[0][1])
    else:
        CheckCodes_list = []
    conn.close()

    return results, CheckCodes_list


@app.route('/Home/Chevrolet/model_series_body')
def index():

    results = SQL_MSB()

    return render_template('MSB.html', results=results)

@app.route('/Home/Chevrolet/model=<model>&series=<series>&body=<body>')
def MSBV(model, series, body):

    results = SQL_MSBV(model, series, body)

    return render_template('MSBV.html', results=results)


@app.route('/Home/Chevrolet/model=<model>&series=<series>&body=<body>&VIN8=<VIN8>', methods=['GET', 'POST'])
def MSBVS(model, series, body, VIN8):
    '''
    if request.method == 'GET':
        print('get')
    elif request.method == 'POST':
        print('post')
        # 处理POST传过来的data(配置代码)为列表
        print(request.form.to_dict())
        check_codes = [k for k, v in request.form.to_dict().items()]
        check_codes = eval(check_codes[0])
        print(type(check_codes),check_codes)
    '''
    results_table_display = SQL_MSBVS_table_display(model, series, body, VIN8)

    all_codes_count, results_descriptionCN_dict = SQL_MSBVS(model, series, body, VIN8)

    results_DynamicHash, CheckCodes_list = SQL_MSBVS_GetDynamicHash(model, series, body, VIN8)

    return render_template('MSBVS.html',
                           results_table_display=results_table_display,
                           results_descriptionCN_dict=results_descriptionCN_dict,
                           all_codes_count=all_codes_count,
                           results_DynamicHash=results_DynamicHash,
                           CheckCodes_list=CheckCodes_list)

# 加入对比配置代码，并生成动态hash值
@app.route('/Home/Chevrolet/model=<model>&series=<series>&body=<body>&VIN8=<VIN8>/SetCompare', methods=['POST'])
def MSBVS_SetCompare(model, series, body, VIN8):

    # 处理POST传过来的data(配置代码)为列表
    check_codes = [k for k, v in request.form.to_dict().items()]
    check_codes = eval(check_codes[0])

    # 重置动态hash分组并入库
    SQL_MSBVS_SetCompare(model, series, body, VIN8, check_codes)

    return '<h1>来错地方了</h1>'

###############↑--↑--↑--↑--↑--↑-END  选配置生成动态分组逻辑-↑--↑--↑--↑--↑--↑--↑################

# 获取车型库所有车型
def SQL_vehicle_list():
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE gm_chevrolet")
    # 查询车型列表
    sql = '''
        SELECT 
            `chevrolet_vehicle_database`.`厂商`,
            `chevrolet_vehicle_database`.`车系`,
            `chevrolet_vehicle_database`.`车型Id`,
            `chevrolet_vehicle_database`.`车型名称`,
            `chevrolet_vehicle_database`.`动力总成`,
            `chevrolet_vehicle_database`.`上市时间`
        FROM `chevrolet_vehicle_database`
        ORDER BY `chevrolet_vehicle_database`.`车系`,`chevrolet_vehicle_database`.`动力总成`;
    '''
    cur.execute(sql)
    vehicle_list_result = cur.fetchall()

    # 查询规则状态，结果返回以整数类型元素组成的列表形式，方便前端判断车型ID是否存在于已有规则列表中，从而给出相应的匹配规则状态
    sql_rule_state = '''
        SELECT `ModelID` FROM `vin_rule`;
    '''
    cur.execute(sql_rule_state)
    rule_state_result = cur.fetchall()
    if rule_state_result:
        rule_state_result_list = [int(i[0]) for i in rule_state_result]
    else:
        rule_state_result_list = []

    conn.close()

    return vehicle_list_result, rule_state_result_list

# 获取指定车型ID基本信息/规则信息
def SQL_vehicle_id(ModelID):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE gm_chevrolet")

    # 查询基本信息
    sql_vehicle_database = '''
        SELECT 
            `chevrolet_vehicle_database`.`车型Id`,
            `chevrolet_vehicle_database`.`车型名称`,
            `chevrolet_vehicle_database`.`动力总成`,
            `chevrolet_vehicle_database`.`上市时间`
        FROM `chevrolet_vehicle_database`
        WHERE `chevrolet_vehicle_database`.`车型Id` = '%s';
    ''' % ModelID
    cur.execute(sql_vehicle_database)
    vehicle_id_result = cur.fetchall()

    # 查询规则信息
    sql_rule_view = '''
        SELECT * FROM `vin_rule`
        WHERE `ModelID` = '%s'
    ''' % ModelID
    cur.execute(sql_rule_view)
    rule_view_result = cur.fetchall()

    # 若规则存在，提取已选配置代码，不存在则返回空结果元组
    if rule_view_result:
        # 提取已选配置代码
        MatchCode = rule_view_result[0][12]
        # 若配置代码存在，处理为元组形式
        if MatchCode:
            MatchCode_list = MatchCode.split(',')
            MatchCode_tuple = tuple(MatchCode_list)

            # 当元组只有一个元素时，使用元组形式的查询语句会出现MySQL语法错误，故另行处理
            if len(MatchCode_tuple) == 1:
                sql_MatchCode_descriptionCN = '''
                    SELECT `optionCode`,`descriptionCN`
                    FROM `vin_codes`
                    WHERE `optionCode` = '%s'
                ''' % (MatchCode_tuple[0])
            else:
                sql_MatchCode_descriptionCN = '''
                    SELECT `optionCode`,`descriptionCN`
                    FROM `vin_codes`
                    WHERE `optionCode` IN {}
                '''.format(MatchCode_tuple)

            # 执行查询语句，返回所有配置代码及其相对应的中文描述元组对
            cur.execute(sql_MatchCode_descriptionCN)
            MatchCode_descriptionCN_result = cur.fetchall()

        else:
            MatchCode_descriptionCN_result = tuple()
    else:
        MatchCode_descriptionCN_result = tuple()

    # 关闭数据库连接
    conn.close()

    return vehicle_id_result, rule_view_result, MatchCode_descriptionCN_result

# 存入规则参数表（重置）
def SQL_vehicle_SaveRuleParam(rule_param):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE gm_chevrolet")

    # 入库或更新前先处理可能存在多值的字段属性进行排序，保证同样参数生成的hash一致
    rule_param_list = list(rule_param)
    maybe_more_param = rule_param_list[5:9]

    # 遍历可能出现多值的字段属性，若有多值则排序处理，若单值或空值则不做处理
    new_maybe_more_param = []  # 初始化新多值参数列表
    for param in maybe_more_param:
        if param and ',' in param:
            param_to_list = param.split(',')
            # 列表转集合去重再转为列表
            param_to_list = list(set(param_to_list))
            # 列表排序
            param_to_list.sort()
            # 排序后转为字符串
            new_param = ','.join(param_to_list)
            # 处理后参数存入新多值参数列表
            new_maybe_more_param.append(new_param)
        else:
            # 直接存入新多值参数列表
            new_maybe_more_param.append(param)

    # 更新参数列表
    rule_param_list[5] = new_maybe_more_param[0]
    rule_param_list[6] = new_maybe_more_param[1]
    rule_param_list[7] = new_maybe_more_param[2]
    rule_param_list[8] = new_maybe_more_param[3]

    # 新参数列表再转为元组
    new_rule_param = tuple(rule_param_list)

    # 判断车型ID是否存在规则表，若存在则更新参数，若不存在则插入
    sql_id_exist = '''
        SELECT ModelID FROM `vin_rule`
        WHERE ModelID = '%s'
    ''' % new_rule_param[0]
    cur.execute(sql_id_exist)
    id_exist_result = cur.fetchall()

    insert_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    insert_Data = new_rule_param + (insert_time,)  # 元组形式

    if id_exist_result:
        sql_update = '''
            UPDATE `vin_rule`
            SET
               `ExampleVIN` = '%s',
               `Model` = '%s',
               `Series` = '%s',
               `Body` = '%s',
               `VIN8` = '%s',
               `Trans` = '%s',
               `Engine` = '%s',
               `NotCode` = '%s',
               `StartTime` = '%s',
               `EndTime` = '%s',
               `InsertTime` = '%s'
            WHERE `ModelID` = '%s'
        ''' % (insert_Data[1],insert_Data[2],insert_Data[3],insert_Data[4],insert_Data[5],insert_Data[6],insert_Data[7],insert_Data[8],insert_Data[9],insert_Data[10],insert_Data[11],insert_Data[0])
        cur.execute(sql_update)
    else:
        sql_insert = '''
            INSERT INTO `vin_rule` (ModelID,ExampleVIN,Model,Series,Body,VIN8,Trans,Engine,NotCode,StartTime,EndTime,InsertTime)
            VALUES{};
        '''.format(insert_Data)
        cur.execute(sql_insert)

    conn.commit()
    conn.close()

# 单个配置代码入库
def SQL_vehicle_AddCode(ModelID, optionCode):
    '''
    先判断ModelID是否在规则表中，optionCode是否在配置表中（防止填入错误）
    若都存在则添加至规则表中的MatchCode字段
    '''
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE gm_chevrolet")

    # 判断车型ID是否存在规则表
    sql_id_exist = '''
        SELECT ModelID FROM `vin_rule`
        WHERE ModelID = '%s'
    ''' % ModelID
    cur.execute(sql_id_exist)
    id_exist_result = cur.fetchall()

    # 判断optionCode是否在配置表中
    sql_optionCode_exist = '''
        SELECT * FROM `vin_codes`
        WHERE optionCode = '%s'
    ''' % optionCode
    cur.execute(sql_optionCode_exist)
    optionCode_exist_result = cur.fetchall()


    # 车型ID和optionCode都存在，提取规则表中的MatchCode
    if id_exist_result and optionCode_exist_result:
        # 判断该配置代码在规则表中是否已经有值
        sql_MatchCode_in_rule = '''
            SELECT MatchCode FROM `vin_rule`
            WHERE ModelID = '%s'
        ''' % ModelID
        cur.execute(sql_MatchCode_in_rule)
        MatchCode_result = cur.fetchall()
        # 每个车型ID只会有一条规则，所以直接提取元组结果的第一条记录的第一个值即可得到字符串类型的MatchCode
        MatchCode_result_str = MatchCode_result[0][0]

        # 将MatchCode转为列表(MatchCode_result_str为空或Null时，转为空列表)
        if MatchCode_result_str:
            MatchCode_result_list = MatchCode_result_str.split(',')
        else:
            MatchCode_result_list = []

        # 新配置代码加入MatchCode列表(当该配置代码不存在于原先列表的时候添加，否则也不重复添加)
        if optionCode not in MatchCode_result_list:
            MatchCode_result_list.append(optionCode)

        # 排序，保证相同配置的配置列表生成的字符串一致
        MatchCode_result_list.sort()

        # 配置代码重新转为拼接后的字符串
        New_MatchCode_list = [str(i) for i in MatchCode_result_list]
        New_MatchCode_str = ','.join(New_MatchCode_list)

        # 更新至规则表
        sql_update = '''
            UPDATE `vin_rule` 
            SET MatchCode = '%s'
            WHERE ModelID = '%s'
        ''' % (New_MatchCode_str, ModelID)
        cur.execute(sql_update)
        conn.commit()
    else:
        pass

    conn.close()

# 单个配置代码移除（更新MatchCode字段）
def SQL_vehicle_RemoveCode(ModelID, optionCode):
    '''
    只要执行这个方法，必定ModelID,optionCode存在于规则表中，直接在MatchCode字段中移除即可
    '''
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE gm_chevrolet")

    sql_query_MatchCode = '''
        SELECT MatchCode FROM `vin_rule`
        WHERE `ModelID` = '%s'  
    ''' % ModelID
    cur.execute(sql_query_MatchCode)
    query_MatchCode_result = cur.fetchall()

    # 转为列表，方便移除
    query_MatchCode_str = query_MatchCode_result[0][0]
    query_MatchCode_list = query_MatchCode_str.split(',')
    query_MatchCode_list.remove(optionCode)

    # 配置代码重新转为拼接后的字符串
    New_MatchCode_list = [str(i) for i in query_MatchCode_list]
    New_MatchCode_str = ','.join(New_MatchCode_list)

    print(New_MatchCode_str)
    # 更新至规则表
    sql_update = '''
        UPDATE `vin_rule` 
        SET MatchCode = '%s'
        WHERE ModelID = '%s'
    ''' % (New_MatchCode_str, ModelID)
    cur.execute(sql_update)
    conn.commit()

    conn.close()

# 查询VIN基本信息
def SQL_vehicle_QueryVinCode(vin):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE gm_chevrolet")

    sql = '''
        SELECT model,series,body,LEFT(vin,8),productMonth,optionCodes
        FROM `vin_hash`
        WHERE vin = '%s'
    ''' % vin

    cur.execute(sql)
    vin_info_result = cur.fetchall()
    # 基本上每条VIN只有一条记录，就算重复刷EPC接口有重复，结果也是一致的，故取第一条记录元组即可
    if vin_info_result:
        vin_info_result = vin_info_result[0]

    conn.close()

    return vin_info_result

# 车架号匹配结果查询
def SQL_VIN_Query(vin_list):
    '''
    连接数据库；
    查VIN缓存中EPC信息；
    依据EPC中的信息，匹配已有规则：
        1.匹配Model,Series,Body,VIN8
        2.以第1步结果匹配发动机，变速箱
        3.以第2步结果排除反向配置
        4.以第3步结果匹配锁定配置
        5.以第4步结果处理限定时间
    最后返回 [[查询的VIN,查询VIN的生产日期，[查询的结果]，[查询的日志]],...]
    '''

    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE gm_chevrolet")

    vin_tuple = tuple(vin_list)

    # 当元组只有一个元素时，使用元组形式的查询语句会出现MySQL语法错误，故另行处理
    if len(vin_tuple) == 1:
        sql_vin_epc = '''
            SELECT `vin`,`model`,`series`,`body`,LEFT(`vin`,8) AS 'VIN8',`productMonth`,`optionCodes`
            FROM `vin_hash`
            WHERE `vin` = '%s'
        ''' % vin_tuple[0]
    else:
        sql_vin_epc = '''
            SELECT `vin`,`model`,`series`,`body`,LEFT(`vin`,8) AS 'VIN8',`productMonth`,`optionCodes`
            FROM `vin_hash`
            WHERE `vin` IN {}
        '''.format(vin_tuple)

    cur.execute(sql_vin_epc)
    vin_info_result = cur.fetchall()

    # 所有匹配结果初始化
    match_result = []

    # 1.匹配Model,Series,Body,VIN8
    for single_vin in vin_info_result:
        # 提取查询VIN在EPC中的基本信息
        vin = single_vin[0]
        vin_Model = single_vin[1]
        vin_Series = single_vin[2]
        vin_Body = single_vin[3]
        vin_VIN8 = single_vin[4]
        vin_productMonth = single_vin[5]
        vin_optionCodes = eval(single_vin[6])

        # 单个VIN结果初始化
        single_vin_result = []
        single_vin_result.append(vin)
        single_vin_result.append(vin_productMonth)

        # 单个VIN匹配日志初始化
        single_vin_log = []

        sql_rule_step1 = '''
        SELECT * FROM `vin_rule`
        WHERE 
            `Model` = '%s'
            AND `Series` = '%s'
            AND `Body` = '%s'
            AND `VIN8` LIKE '%s';
        ''' % (vin_Model, vin_Series, vin_Body, '%'+vin_VIN8+'%')
        cur.execute(sql_rule_step1)
        rule_result_step1 = cur.fetchall()
        # 查询结果为元组，转为列表方便后续删除等操作
        rule_result_step1_list = list(rule_result_step1)

        rule_result_step2_list = []
        # 2.以第1步结果匹配发动机，变速箱
        if rule_result_step1_list:
            tip = '[Step1-车型信息]：过滤车型信息，剩下%d条规则' % len(rule_result_step1_list)
            single_vin_log.append(tip)
            for step1 in rule_result_step1_list:
                # 变速箱,发动机字段转列表
                ModelID = step1[1]
                trans = step1[7].split(',')
                engine = step1[8].split(',')

                # 变速箱，发动机代码与vin所有配置代码列表合并后转集合去重
                # 若合并后集合长度等于合并前两集合的长度，则说明变速箱，发动机代码不在vin所有配置代码中，则不匹配，否则匹配
                if (len(set(vin_optionCodes+trans)) == len(set(vin_optionCodes)) + len(set(trans))) or (len(set(vin_optionCodes+engine)) == len(set(vin_optionCodes)) + len(set(engine))):
                    tip = '>>>规则[%s]动力总成 - %s;%s 不匹配' % (ModelID,trans,engine)
                    single_vin_log.append(tip)
                else:
                    rule_result_step2_list.append(step1)

            rule_result_step3_list = []
            # 3.以第2步结果排除反向配置MH8
            if rule_result_step2_list:
                tip = '[Step2-动力总成]：过滤动力总成，剩下%d条规则' % len(rule_result_step2_list)
                single_vin_log.append(tip)
                for step2 in rule_result_step2_list:
                    # 检查规则中是否有反向配置限制，存在则转为列表，不存在则略过该条规则，直接添加至下一步的结果中
                    ModelID = step2[1]
                    NotCode = step2[9]
                    if NotCode:
                        NotCode = NotCode.split(',')
                        # 反向配置与车架号所有配置的两个集合求交集，交集为空表示能匹配，否则表示有冲突，即不匹配
                        NotCode_intersection_optionCodes = set(NotCode) & set(vin_optionCodes)
                        if NotCode_intersection_optionCodes:
                            tip = '>>>规则[%s]反向配置 - %s 不匹配' % (ModelID, NotCode_intersection_optionCodes)
                            single_vin_log.append(tip)
                        else:
                            rule_result_step3_list.append(step2)
                    else:
                        rule_result_step3_list.append(step2)

                rule_result_step4_list = []
                # 4.以第3步结果匹配锁定配置
                if rule_result_step3_list:
                    tip = '[Step3-反向配置]：过滤反向配置，剩下%d条规则' % len(rule_result_step3_list)
                    single_vin_log.append(tip)
                    for step3 in rule_result_step3_list:
                        ModelID = step3[1]
                        MatchCode = step3[12]
                        # 判断锁定配置未选则不匹配
                        if MatchCode:
                            # 锁定配置与车架号所有配置的两个集合求差集，无差集则完全匹配，有差集则差集部分配置不匹配
                            MatchCode = MatchCode.split(',')
                            MatchCode_difference_optionCodes = set(MatchCode) - set(vin_optionCodes)
                            if not MatchCode_difference_optionCodes:
                                rule_result_step4_list.append(step3)
                            else:
                                tip = '>>>规则[%s]锁定配置 - %s 与规则存在冲突' % (ModelID,MatchCode_difference_optionCodes)
                                single_vin_log.append(tip)
                        else:
                            tip = '>>>规则[%s]锁定配置 - 未选择配置代码' % (ModelID)
                            single_vin_log.append(tip)

                    rule_result_step5_list = []
                    if rule_result_step4_list:
                        tip = '[Step4-锁定配置]：过滤锁定配置，剩下%d条规则' % len(rule_result_step4_list)
                        single_vin_log.append(tip)
                        for step4 in rule_result_step4_list:
                            ModelID = step4[1]
                            StartTime = step4[10]
                            EndTime = step4[11]

                            # python时间对比中，空字符串''最小，'None'值最大
                            if StartTime:
                                pass
                            else:
                                StartTime = ''
                            if EndTime:
                                pass
                            else:
                                EndTime = 'None'

                            # EPC中VIN生产时间除正常值外，还有None和1900-01-01附近的时间
                            if vin_productMonth >= StartTime and vin_productMonth <= EndTime:
                                rule_result_step5_list.append(step4)
                            else:
                                tip = '>>>规则[%s]限定时间 - 限定时间不匹配' % (ModelID)
                                single_vin_log.append(tip)
                        if rule_result_step5_list:
                            tip = '[Step5-限定时间]：过滤限定时间，剩下%d条规则' % len(rule_result_step5_list)
                            single_vin_log.append(tip)
                            match_id = []
                            for i in rule_result_step5_list:
                                match_id.append(i[1])
                            # 单个VIN匹配完成，加入总结果列表
                            single_vin_result.append(match_id)
                            single_vin_result.append(single_vin_log)
                            match_result.append(single_vin_result)
                        else:
                            tip = '[Step5-限定时间]：过滤限定时间，剩下%d条规则' % len(rule_result_step5_list)
                            single_vin_log.append(tip)
                            single_vin_result.append(list())
                            single_vin_result.append(single_vin_log)
                            match_result.append(single_vin_result)
                    else:
                        tip = '[Step4-锁定配置]：过滤锁定配置，剩下%d条规则' % len(rule_result_step4_list)
                        single_vin_log.append(tip)
                        single_vin_result.append(list())
                        single_vin_result.append(single_vin_log)
                        match_result.append(single_vin_result)
                else:
                    tip = '[Step3-反向配置]：过滤反向配置，剩下%d条规则' % len(rule_result_step3_list)
                    single_vin_log.append(tip)
                    single_vin_result.append(list())
                    single_vin_result.append(single_vin_log)
                    match_result.append(single_vin_result)
            else:
                tip = '[Step2-动力总成]：过滤动力总成，剩下%d条规则' % len(rule_result_step2_list)
                single_vin_log.append(tip)
                single_vin_result.append(list())
                single_vin_result.append(single_vin_log)
                match_result.append(single_vin_result)
        else:
            tip = '[Step1-车型信息]：过滤车型信息，剩下%d条规则' % len(rule_result_step1_list)
            single_vin_log.append(tip)
            single_vin_result.append(list())
            single_vin_result.append(single_vin_log)
            match_result.append(single_vin_result)

    conn.close()

    return match_result

# 车架号查询匹配结果展示处理
def SQL_VIN_Query_View(match_result):
    '''
    连接数据库；
    查询车型库，生成车型ID对应的车型名称字典
    遍历已经查询的车架号结果，处理为固定格式的字典形式
    :param match_result: [[查询的VIN,查询VIN的生产日期，[查询的结果]，[查询的日志]],...]
    :return:{'vin1':
                {'productTime': '',
                'ModelID': '',
                'ModelName': '',
                'remark': '',
                'log': ''},
            ...
            }
    '''
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE gm_chevrolet")
    sql = '''
        SELECT 
            `chevrolet_vehicle_database`.`车型Id`,
            `chevrolet_vehicle_database`.`车型名称`
        FROM `chevrolet_vehicle_database`;
        '''
    cur.execute(sql)
    vehicle_database = cur.fetchall()
    conn.close()

    vehicle_database_dict = {}
    for i in vehicle_database:
        vehicle_database_dict[str(i[0])] = i[1]

    view_result = {}

    for i in match_result:
        # 初始化单个VIN展示格式
        vin_single_view = {'productTime': '',
                           'ModelID': '',
                           'ModelName': '',
                           'remark': '',
                           'log': ''}
        vin = i[0]
        vin_productTime = i[1]
        vin_query_result = i[2]
        vin_query_log = i[3]

        # 车型ID查车型名称
        if len(vin_query_result) == 0:
            vin_remark = '无法匹配'
            vin_ModelName= []
        elif len(vin_query_result) == 1:
            vin_remark = '匹配成功'
            vin_ModelName = [vehicle_database_dict[vin_query_result[0]]]
        else:
            vin_remark = '匹配多款'
            vin_ModelName = [vehicle_database_dict[i] for i in vin_query_result]


        view_result[vin] = vin_single_view
        view_result[vin]['productTime'] = vin_productTime
        view_result[vin]['ModelID'] = vin_query_result
        view_result[vin]['ModelName'] = vin_ModelName
        view_result[vin]['remark'] = vin_remark
        view_result[vin]['log'] = vin_query_log
    print(view_result)

    return view_result


# 车型列表页面
@app.route('/Home/Chevrolet/vehicle_list')
def vehicle_list():

    vehicle_list_result, rule_state_result_list = SQL_vehicle_list()
    print(rule_state_result_list, vehicle_list_result)

    return render_template('vehicle_list.html',
                           vehicle_list_result=vehicle_list_result,
                           rule_state_result_list=rule_state_result_list)

# 配置填写页面
@app.route('/Home/Chevrolet/id=<ModelID>')
def vehicle_id(ModelID):

    vehicle_id_result, rule_view_result, MatchCode_descriptionCN_result = SQL_vehicle_id(ModelID)

    return render_template('vehicle_id.html',
                           ModelID=ModelID,
                           vehicle_id_result=vehicle_id_result,
                           rule_view_result=rule_view_result,
                           MatchCode_descriptionCN_result=MatchCode_descriptionCN_result)

    '''
    # 样例VIN展示配置代码数量部分
    optionCodes = []
    all_codes_count = ''
    results_descriptionCN_dict = {}
    if rule_view_result:
        example_vin = rule_view_result[0][2]
        print(example_vin)
        # 第一步，先查vin基本信息
        vin_info = SQL_vehicle_QueryVinCode(example_vin)
        if vin_info:
            model = vin_info[0]
            series = vin_info[1]
            body = vin_info[2]
            VIN8 = vin_info[3]
            optionCodes = eval(vin_info[5])
            # 第二步，依据vin基本信息，查同Model,Series,Body,VIN8情况下，全部已有vin配置代码数量分布，便于人工选取配置代码
            all_codes_count, results_descriptionCN_dict = SQL_MSBVS(model, series, body, VIN8)
        else:
            pass
        
    return render_template('vehicle_id.html',
                           ModelID=ModelID,
                           vehicle_id_result=vehicle_id_result,
                           rule_view_result=rule_view_result,
                           MatchCode_descriptionCN_result=MatchCode_descriptionCN_result,
                           optionCodes=optionCodes,
                           all_codes_count=all_codes_count,
                           results_descriptionCN_dict=results_descriptionCN_dict)
    '''

# 保存规则参数
@app.route("/Home/Chevrolet/SaveRuleParam", methods=['POST'])
def vehicle_SaveRuleParam():

    # POST提取规则参数
    rule_param = [v for k, v in request.values.items()]
    rule_param = tuple(rule_param)

    # 规则参数存入规则表
    SQL_vehicle_SaveRuleParam(rule_param)
    return '<h1>保存参数了吗？</h1>'

# 添加单个配置代码
@app.route("/Home/Chevrolet/AddCode", methods=['POST'])
def vehicle_AddCode():

    # POST提取要添加的配置代码
    ModelID = request.values['ModelID']
    optionCode = request.values['optionCode']

    SQL_vehicle_AddCode(ModelID, optionCode)

    return '<h1>添加配置代码</h1>'

# 移除单个配置代码
@app.route("/Home/Chevrolet/RemoveCode",methods=['POST'])
def vehicle_RemoveCode():

    # POST提取要删除的配置代码
    ModelID = request.values['ModelID']
    optionCode = request.values['optionCode']

    SQL_vehicle_RemoveCode(ModelID, optionCode)

    return '<h1>移除配置代码</h1>'

# 查询VIN配置及同车型条件的配置代码计数
@app.route("/Home/Chevrolet/QueryVinCodeUrl",methods=['GET', 'POST'])
def vehicle_QueryVinCodeUrl():
    vin = ''
    vin_info = tuple()
    optionCodes = []
    all_codes_count = ''
    results_descriptionCN_dict = {}
    results_table_display = tuple()
    if request.method == 'POST':
        # POST提取要查询的vin
        vin = request.values['vin']
        # 第一步，先查vin基本信息
        vin_info = SQL_vehicle_QueryVinCode(vin)

        if vin_info:
            model = vin_info[0]
            series = vin_info[1]
            body = vin_info[2]
            VIN8 = vin_info[3]
            optionCodes = eval(vin_info[5])
            # 第二步，依据vin基本信息，查同Model,Series,Body,VIN8情况下，全部已有vin配置代码数量分布，便于人工选取配置代码
            all_codes_count, results_descriptionCN_dict = SQL_MSBVS(model, series, body, VIN8)
            results_table_display = SQL_MSBVS_table_display(model, series, body, VIN8)
        else:
            pass
    else:
        pass

    return render_template('QueryVinCodeUrl.html',
                           vin=vin,
                           vin_info=vin_info,
                           optionCodes=optionCodes,
                           all_codes_count=all_codes_count,
                           results_descriptionCN_dict=results_descriptionCN_dict,
                           results_table_display=results_table_display)

# 查询匹配结果
@app.route("/Home/Chevrolet/VIN_Query",methods=['POST','GET'])
def VIN_Query():
    view_result = {}
    # POST请求时处理
    if request.method == 'POST':
        # 将要查询的车架号转为列表存储
        vin_list = eval([k for k in request.form.to_dict().keys()][0])
        # 将列表转为集合去重，删除空字符串元素（前端网页换行后为填写车架号导致）
        new_vin_list = list(set(vin_list))
        # 将列表中所有出现的小写字母转为大写
        new_vin_list = [i.upper() for i in new_vin_list]

        if '' in new_vin_list:
            new_vin_list.remove('')

        # 车架号列表处理后为空列表时
        if len(new_vin_list) == 0:
            view_result = {}
            return render_template('VIN_Query.html', view_result=view_result)
        else:
            # 查询出有缓存数据的结果
            match_result = SQL_VIN_Query(new_vin_list)
            # 有缓存数据的展示结果
            view_result = SQL_VIN_Query_View(match_result)

            # 无缓存数据提示加入展示结果
            vin_single_view = {'productTime': '',
                               'ModelID': '',
                               'ModelName': '',
                               'remark': '无缓存数据',
                               'log': ''}
            for i in new_vin_list:
                if i not in view_result.keys():
                    print('无缓存')
                    view_result[i] = vin_single_view
                else:
                    print('有缓存')

            return render_template('VIN_Query.html', view_result=view_result)
    else:
        return render_template('VIN_Query.html', view_result=view_result)




if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)





