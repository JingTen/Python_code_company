# coding=utf-8
'''二手车之家车架号采集主程序'''
import time
import random

# 导入自定义模块
from second_hand_car_vin import second_hand_car_get_html as gh
from second_hand_car_vin import second_hand_car_save_data as sd


def crawling_and_save(brand_py, area_py, total_page, area_dict):
    '''指定品牌、地区（省份/直辖市或城市）、总页数完成采集与入库'''
    get_html_ = gh.GetHTML()
    save_txt_ = sd.TipToTXT()
    format_url_ = gh.FormatURL()
    # 遍历每一个页面
    for page in range(1, total_page + 1):
        # 初始化每个页面所有二手车信息列表
        page_CarInfo_list = []
        # 获取每一个页面中所有车辆URL列表
        car_url_list = get_html_.get_page_car_url(area_py, brand_py, page)
        # 遍历车辆URL列表，格式化为手机端URL
        for no_format_url in car_url_list:
            # 格式化手机端格式URL
            format_url = format_url_.judge_and_format_url(no_format_url)
            # 获取每辆二手车信息
            CarInfo_list = get_html_.get_CarInfo(format_url, no_format_url, area_dict)
            # 每辆二手车信息存入每个页面车辆信息列表
            if CarInfo_list:
                page_CarInfo_list.append(CarInfo_list)
            time.sleep(random.random() + 1)
        # 每页所有二手车信息追加存入数据库
        sd.ConnectMysql().carinfo_insert_into_mysql(page_CarInfo_list)
        sd.ConnectMysql().html_insert_into_mysql(page_CarInfo_list)
        tips = "第%d页（共%d页）采集完成！" % (page, total_page)
        print(tips)
        save_txt_.records_txt(tips)





# 实例化网页采集类
get_html = gh.GetHTML()
# 品牌字典
brand_dict = get_html.brand_dict
# 省份字典
province_dict = get_html.province_dict
# 城市字典
city_dict = get_html.city_dict
# 地区信息（地区与id映射关系字典）
area_dict = sd.ConnectMysql().select_area_info()
# 实例化存储类
save_txt = sd.TipToTXT()


########################################
'''更新地区信息至数据库
area_lists = get_html.get_area_info()
print(area_lists)
sd.ConnectMysql().update_area_info(area_lists)
'''
########################################



########################################
# 手动更改地区
province_dict = {'广西': 'guangxi', '贵州': 'guizhou', '甘肃': 'gansu', '海南': 'hainan',
                              '河南': 'henan', '湖北': 'hubei', '湖南': 'hunan', '河北': 'hebei', '黑龙江': 'heilongjiang',
                              '江苏': 'jiangsu', '江西': 'jiangxi', '吉林': 'jilin', '辽宁': 'liaoning',
                              '内蒙古': 'namenggu', '宁夏': 'ningxia', '青海': 'qinghai', '陕西': 'shan_xi',
                              '四川': 'sichuan', '上海': 'shanghai', '山西': 'shanxi', '山东': 'shandong',
                              '天津': 'tianjin', '新疆': 'xinjiang', '西藏': 'xizang', '云南': 'yunnan', '浙江': 'zhejiang'
                              }
# 手动更改品牌
brand_dict = {
            '本田': 'bentian', '宝马': 'baoma', '北京': 'beijing', '长安': 'changan', '长城': 'changcheng',
            '长安欧尚': 'changanoushang', '成功汽车': 'chenggongqiche', '长安轻型车': 'changanqingxingche',
            '长安跨越': 'changankuayue', '电咖': 'dianka', '东风风光': 'dongfengfengguang', '东风风行': 'dongfengfengxing',
            'DS': 'ds', '东风风度': 'dongfengfengdu', '东风小康': 'dongfengxiaokang', '东风风神': 'dongfengfengshen',
            '东南': 'dongnan', '道奇': 'daoqi', '大发': 'dafa', '东风': 'dongfeng', '大众': 'dazhong', '丰田': 'fengtian',
            '福特': 'fute', '菲亚特': 'feiyate', '福田': 'futian', '法拉利': 'falali', '福迪': 'fudi',
            '福汽启腾': 'fuqiqiteng', '福田乘用车': 'futianchengyongche', '广汽新能源': 'guangqixinnengyuan',
            '国金汽车': 'guojinqiche', '观致': 'guanzhi', 'GMC': 'gmc', '广汽吉奥': 'guangqijiao', '光冈': 'guanggang',
            '广汽传祺': 'guangqichuanqi', '悍马': 'hanma', '黄海': 'huanghai', '红旗': 'hongqi', '华普': 'huapu',
            '海马': 'haima', '华泰': 'huatai', '哈飞': 'hafei', '海格': 'haige', '华骐': 'huaqi', '哈弗': 'hafu',
            '恒天': 'hengtian', '华凯': 'huakai', '华泰新能源': 'huataixinnengyuan', '汉腾汽车': 'hantengqiche',
            '华利': 'huali', '华颂': 'huasong', 'Icona': 'icona', '金旅': 'jinlv', '江铃集团轻汽': 'jianglingjituanqingqi',
            '九龙': 'jiulong', '金龙': 'jinlong', '江铃': 'jiangling', '吉利汽车': 'jiliqiche', 'Jeep': 'jeep',
            '捷豹': 'jiebao', '金杯': 'jinbei', '江淮': 'jianghuai', '江铃集团新能源': 'jianglingjituanxinnengyuan',
            '君马汽车': 'junmaqiche', '科尼赛克': 'kenisaike', '开瑞': 'kairui', '凯迪拉克': 'kaidilake',
            '克莱斯勒': 'kelaisile', 'KTM': 'ktm', '卡尔森': 'kaersen', '凯翼': 'kaiyi', '康迪全球鹰': 'kangdiquanqiuying',
            '卡升': 'kasheng', '卡威': 'kawei', '陆地方舟': 'ludifangzhou', 'Lorinser': 'lorinser', '理念': 'linian',
            '雷诺': 'leinuo', '兰博基尼': 'lanbojini', '路虎': 'luhu', '路特斯': 'lutesi', '林肯': 'linken',
            '雷克萨斯': 'leikesasi', '铃木': 'lingmu', '劳斯莱斯': 'laosilaisi', '陆风': 'lufeng', '莲花汽车': 'lianhuaqiche',
            '力帆汽车': 'lifanqiche', '猎豹汽车': 'liebaoqiche', '领克': 'lingke', 'LOCAL MOTORS': 'localmotors',
            '迈巴赫': 'maibahe', 'MINI': 'mini', '玛莎拉蒂': 'mashaladi', '马自达': 'mazida', '名爵': 'mingjue',
            '迈凯伦': 'maikailun', '摩根': 'mogen', '南京金龙': 'nanjingjinlong', '纳智捷': 'nazhijie', '欧朗': 'oulang',
            '欧宝': 'oubao', '讴歌': 'ouge', '帕加尼': 'pajiani', '起亚': 'qiya', '奇瑞': 'qirui', '启辰': 'qichen',
            '庆铃汽车': 'qinglingqiche', '广汽集团': 'guangqijituan', '瑞驰新能源': 'ruichixinnengyuan', '瑞麒': 'ruiqi',
            '如虎': 'ruhu', '荣威': 'rongwei', '日产': 'richan', '萨博': 'sabo', '斯巴鲁': 'sibalu', '世爵': 'shijue',
            '斯柯达': 'sikeda', '三菱': 'sanling', '双龙': 'shuanglong', 'smart': 'smart', '双环': 'shuanghuan',
            '思铭': 'siming', '赛麟': 'sailin', '陕汽通家': 'shanqitongjia', '上汽MAXUS': 'shangqimaxus',
            '斯达泰克': 'sidataike', 'SWM斯威汽车': 'swmsiweiqiche', '腾势': 'tengshi', '特斯拉': 'tesila',
            '泰卡特': 'taikate', '五十铃': 'wushiling', '潍柴英致': 'weichaiyingzhi', '五菱汽车': 'wulingqiche',
            '威麟': 'weilin', '威兹曼': 'weiziman', '沃尔沃': 'woerwo', 'WEY': 'wey', '蔚来': 'weilai', '鑫源': 'xinyuan',
            '雪佛兰': 'xuefolan', '雪铁龙': 'xuetielong', '现代': 'xiandai', '西雅特': 'xiyate', '新凯': 'xinkai',
            '御捷': 'yujie', '一汽': 'yiqi', '野马汽车': 'yemaqiche', '依维柯': 'yiweike', '永源': 'yongyuan',
            '英菲尼迪': 'yingfeinidi', '裕路': 'yulu', '宇通客车': 'yutongkeche', '云度': 'yundu', '驭胜': 'yusheng',
            '中兴': 'zhongxing', '中华': 'zhonghua', '众泰': 'zhongtai', '知豆': 'zhidou', '之诺': 'zhinuo',
            '全球鹰': 'quanqiuying', '骐铃汽车': "qilingqiche", '开沃汽车': 'kaiwoqiche', 'SRM鑫源': 'srmxinyuan'
        }
########################################


# 品牌遍历
for brand, brand_py in brand_dict.items():
    # 省份/直辖市遍历
    for province, province_py in province_dict.items():
        # 获取筛选页面总数及车辆总数
        TotalPage_and_TotalCarNum_list = get_html.get_TotalPage_and_TotalCarNum(brand, brand_py, province, province_py)
        if TotalPage_and_TotalCarNum_list:
            TotalPage = TotalPage_and_TotalCarNum_list[0]
            TotalCarNum = TotalPage_and_TotalCarNum_list[1]
            tip = "%s--%s--总页数：%s--维保可查车辆总数：%s" % (brand, province, TotalPage, TotalCarNum)
            # 判断页面总数，确定下步流程
            if TotalPage == 0:
                tips = "%s，无符合条件二手车！！！" % tip
                print(tips)
                save_txt.records_txt(tips)
            elif TotalPage < 101:
                print("%s，开始采集..." % tip)
                # 指定品牌、地区、总页数完成采集入库
                crawling_and_save(brand_py, province_py, TotalPage, area_dict)
                # 品牌地区下，全部采集完成记录
                tips = "%s，全部采集完成！" % tip
                print(tips)
                save_txt.records_txt(tips)
            else:
                tips = "%s，符合条件页面总数大于100页，正在细化选择..." % tip
                print(tips)
                save_txt.records_txt(tips)
                # 省份级别筛选页面总数大于100页，执行城市级别筛选采集
                # 获取特定省份下的所有城市字典
                province_city_dict = city_dict[province]
                # 城市遍历
                for city, city_py in province_city_dict.items():
                    # 获取筛选页面总数及车辆总数
                    TotalPage_and_TotalCarNum_list = get_html.get_TotalPage_and_TotalCarNum(brand, brand_py,
                                                                                            city, city_py)
                    if TotalPage_and_TotalCarNum_list:
                        TotalPage = TotalPage_and_TotalCarNum_list[0]
                        TotalCarNum = TotalPage_and_TotalCarNum_list[1]
                        tip = "%s--%s--总页数：%s--维保可查车辆总数：%s" % (brand, city, TotalPage, TotalCarNum)
                        # 判断页面总数，确定下步流程
                        if TotalPage == 0:
                            tips = "%s，无符合条件二手车！！！" % tip
                            print(tips)
                            save_txt.records_txt(tips)
                        elif TotalPage < 101:
                            print("%s，开始采集..." % tip)
                            # 指定品牌、地区、总页数完成采集入库
                            crawling_and_save(brand_py, city_py, TotalPage, area_dict)
                            # 品牌地区下，全部采集完成记录
                            tips = "%s，全部采集完成！" % tip
                            print(tips)
                            save_txt.records_txt(tips)
                        else:
                            tips = "%s，符合条件页面总数大于100页，Next One..." % tip
                            print(tips)
                            save_txt.records_txt(tips)
                    else:
                        tips = "%s--%s--筛选条件与实际返回页面不符！！！" % (brand, city)
                        print(tips)
                        save_txt.records_txt(tips)
                        continue
        else:
            tips = "%s--%s--筛选条件与实际返回页面不符！！！" % (brand, province)
            save_txt.records_txt(tips)
            continue




