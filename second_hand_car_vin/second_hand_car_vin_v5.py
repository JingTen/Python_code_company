'''
------------------------------------------函数方法封装部分------------------------------------------
'''

from urllib.request import urlopen
from bs4 import BeautifulSoup
from lxml import etree

import re
import csv
import math
import time
import codecs
import random
import requests
import pymysql
import html

# 省份直辖市级别字典(key:中文名，value:拼音)
province_dict = {'安徽': 'anhui', '北京': 'beijing', '重庆': 'chongqing', '福建': 'fujian', '广东': 'guangdong', '广西': 'guangxi',
                 '贵州': 'guizhou', '甘肃': 'gansu', '海南': 'hainan', '河南': 'henan', '湖北': 'hubei', '湖南': 'hunan',
                 '河北': 'hebei', '黑龙江': 'heilongjiang', '江苏': 'jiangsu', '江西': 'jiangxi', '吉林': 'jilin',
                 '辽宁': 'liaoning', '内蒙古': 'namenggu', '宁夏': 'ningxia', '青海': 'qinghai', '陕西': 'shan_xi',
                 '四川': 'sichuan', '上海': 'shanghai', '山西': 'shanxi', '山东': 'shandong', '天津': 'tianjin', '新疆': 'xinjiang',
                 '西藏': 'xizang', '云南': 'yunnan', '浙江': 'zhejiang'}

# 各省份下城市字典
city_dict = {'安徽': {'合肥': 'hefei', '芜湖': 'wuhu', '蚌埠': 'bangbu', '淮南': 'huainan', '马鞍山': 'maanshan', '淮北': 'huaibei',
                    '铜陵': 'tongling', '安庆': 'anqing', '黄山': 'huangshan', '滁州': 'chuzhou', '阜阳': 'fu_yang',
                    '宿州': 'su_zhou', '六安': 'liuan', '亳州': 'bozhou', '池州': 'chizhou', '宣城': 'xuancheng'},
             '北京': {'北京': 'beijing'}, '重庆': {'重庆': 'chongqing'},
             '福建': {'福州': 'fuzhou', '厦门': 'xiamen', '莆田': 'putian', '三明': 'sanming', '泉州': 'quanzhou',
                    '漳州': 'zhangzhou', '南平': 'nanping', '龙岩': 'longyan', '宁德': 'ningde'},
             '广东': {'广州': 'guangzhou', '韶关': 'shaoguan', '深圳': 'shenzhen', '珠海': 'zhuhai', '汕头': 'shantou',
                    '佛山': 'foshan', '江门': 'jiangmen', '湛江': 'zhanjiang', '茂名': 'maoming', '肇庆': 'zhaoqing',
                    '惠州': 'huizhou', '梅州': 'meizhou', '汕尾': 'shanwei', '河源': 'heyuan', '阳江': 'yangjiang',
                    '清远': 'qingyuan', '东莞': 'dongguan', '中山': 'zhongshan', '潮州': 'chaozhou', '揭阳': 'jieyang',
                    '云浮': 'yunfu'},
             '广西': {'南宁': 'nanning', '柳州': 'liuzhou', '桂林': 'guilin', '梧州': 'wuzhou', '北海': 'beihai',
                    '防城港': 'fangchenggang', '钦州': 'qinzhou', '贵港': 'guigang', '玉林': 'yu_lin', '百色': 'baise',
                    '贺州': 'hezhou', '河池': 'hechi', '来宾': 'laibin', '崇左': 'chongzuo'},
             '贵州': {'贵阳': 'guiyang', '六盘水': 'liupanshui', '遵义': 'zunyi', '安顺': 'anshun', '毕节': 'bijie', '铜仁': 'tongren',
                    '黔西南': 'qianxinan', '黔东南': 'qiandongnan', '黔南': 'qiannan'},
             '甘肃': {'兰州': 'lanzhou', '嘉峪关': 'jiayuguan', '金昌': 'jinchang', '白银': 'baiyin', '天水': 'tianshui',
                    '武威': 'wuwei', '张掖': 'zhangye', '平凉': 'pingliang', '酒泉': 'jiuquan', '庆阳': 'qingyang',
                    '定西': 'dingxi', '陇南': 'longnan', '临夏': 'linxia', '甘南': 'gannan'},
             '海南': {'海口': 'haikou', '三亚': 'sanya', '三沙': 'sansha', '儋州': 'danzhou', '五指山': 'wuzhishan',
                    '琼海': 'qionghai', '文昌': 'wenchang', '万宁': 'wanning', '东方': 'dongfang', '定安': 'dingan',
                    '屯昌': 'tunchang', '澄迈': 'chengmai', '临高': 'lingao', '白沙': 'baisha', '昌江': 'changjiang',
                    '乐东': 'ledong', '陵水': 'lingshui', '保亭': 'baoting', '琼中': 'qiongzhong'},
             '河南': {'郑州': 'zhengzhou', '开封': 'kaifeng', '洛阳': 'luoyang', '平顶山': 'pingdingshan', '安阳': 'anyang',
                    '鹤壁': 'hebi', '新乡': 'xinxiang', '焦作': 'jiaozuo', '濮阳': 'puyang', '许昌': 'xuchang', '漯河': 'luohe',
                    '三门峡': 'sanmenxia', '南阳': 'nanyang', '商丘': 'shangqiu', '信阳': 'xinyang', '周口': 'zhoukou',
                    '驻马店': 'zhumadian', '济源': 'jiyuan'},
             '湖北': {'武汉': 'wuhan', '黄石': 'huangshi', '十堰': 'shiyan', '宜昌': 'yichang', '襄阳': 'xiangyang', '鄂州': 'ezhou',
                    '荆门': 'jingmen', '孝感': 'xiaogan', '荆州': 'jingzhou', '黄冈': 'huanggang', '咸宁': 'xianning',
                    '随州': 'suizhou', '恩施': 'enshi', '仙桃': 'xiantao', '潜江': 'qianjiang', '天门': 'tianmen',
                    '神农架': 'shennongjia'},
             '湖南': {'长沙': 'changsha', '株洲': 'zhuzhou', '湘潭': 'xiangtan', '衡阳': 'hengyang', '邵阳': 'shaoyang',
                    '岳阳': 'yueyang', '常德': 'changde', '张家界': 'zhangjiajie', '益阳': 'yiyang', '郴州': 'chenzhou',
                    '永州': 'yongzhou', '怀化': 'huaihua', '娄底': 'loudi', '湘西': 'xiangxi'},
             '河北': {'石家庄': 'shijiazhuang', '唐山': 'tangshan', '秦皇岛': 'qinhuangdao', '邯郸': 'handan', '邢台': 'xingtai',
                    '保定': 'baoding', '张家口': 'zhangjiakou', '承德': 'chengde', '沧州': 'cangzhou', '廊坊': 'langfang',
                    '衡水': 'hengshui'},
             '黑龙江': {'哈尔滨': 'haerbin', '齐齐哈尔': 'qiqihaer', '鸡西': 'jixi', '鹤岗': 'hegang', '双鸭山': 'shuangyashan',
                     '大庆': 'daqing', '伊春': 'yichun', '佳木斯': 'jiamusi', '七台河': 'qitaihe', '牡丹江': 'mudanjiang',
                     '黑河': 'heihe', '绥化': 'suihua', '大兴安岭': 'daxinganling'},
             '江苏': {'南京': 'nanjing', '无锡': 'wuxi', '徐州': 'xuzhou', '常州': 'changzhou', '苏州': 'suzhou', '南通': 'nantong',
                    '连云港': 'lianyungang', '淮安': 'huaian', '盐城': 'yancheng', '扬州': 'yangzhou', '镇江': 'zhenjiang',
                    '泰州': 'tai_zhou', '宿迁': 'suqian'},
             '江西': {'南昌': 'nanchang', '景德镇': 'jingdezhen', '萍乡': 'ping_xiang', '九江': 'jiujiang', '新余': 'xinyu',
                    '鹰潭': 'yingtan', '赣州': 'ganzhou', '吉安': 'jian', '宜春': 'yi_chun', '抚州': 'fu_zhou', '上饶': 'shangrao'},
             '吉林': {'长春': 'changchun', '吉林': 'jilinshi', '四平': 'siping', '辽源': 'liaoyuan', '通化': 'tonghua',
                    '白山': 'baishan', '松原': 'songyuan', '白城': 'baicheng', '延边': 'yanbian'},
             '辽宁': {'沈阳': 'shenyang', '大连': 'dalian', '鞍山': 'anshan', '抚顺': 'fushun', '本溪': 'benxi', '丹东': 'dandong',
                    '锦州': 'jinzhou', '营口': 'yingkou', '阜新': 'fuxin', '辽阳': 'liaoyang', '盘锦': 'panjin', '铁岭': 'tieling',
                    '朝阳': 'chaoyang', '葫芦岛': 'huludao'},
             '内蒙古': {'呼和浩特': 'huhehaote', '包头': 'baotou', '乌海': 'wuhai', '赤峰': 'chifeng', '通辽': 'tongliao',
                     '鄂尔多斯': 'eerduosi', '呼伦贝尔': 'hulunbeier', '巴彦淖尔': 'bayannaoer', '乌兰察布': 'wulanchabu',
                     '兴安盟': 'xinganmeng', '锡林郭勒盟': 'xilinguolemeng', '阿拉善盟': 'alashanmeng'},
             '宁夏': {'银川': 'yinchuan', '石嘴山': 'shizuishan', '吴忠': 'wuzhong', '固原': 'guyuan', '中卫': 'zhongwei'},
             '青海': {'西宁': 'xining', '海东': 'haidong', '海北': 'haibei', '黄南': 'huangnan', '海南': 'hai_nan', '果洛': 'guoluo',
                    '玉树': 'yushu', '海西': 'haixi'},
             '陕西': {'西安': 'xian', '铜川': 'tongchuan', '宝鸡': 'baoji', '咸阳': 'xianyang', '渭南': 'weinan', '延安': 'yanan',
                    '汉中': 'hanzhong', '榆林': 'yulin', '安康': 'ankang', '商洛': 'shangluo', '西咸新区': 'xixianxinqu'},
             '四川': {'成都': 'chengdu', '自贡': 'zigong', '攀枝花': 'panzhihua', '泸州': 'luzhou', '德阳': 'deyang',
                    '绵阳': 'mianyang', '广元': 'guangyuan', '遂宁': 'suining', '内江': 'neijiang', '乐山': 'leshan',
                    '南充': 'nanchong', '眉山': 'meishan', '宜宾': 'yibin', '广安': 'guangan', '达州': 'dazhou', '雅安': 'yaan',
                    '巴中': 'bazhong', '资阳': 'ziyang', '阿坝': 'aba', '甘孜': 'ganzi', '凉山': 'liangshan'},
             '上海': {'上海': 'shanghai'},
             '山西': {'太原': 'taiyuan', '大同': 'datong', '阳泉': 'yangquan', '长治': 'zhangzhi', '晋城': 'jincheng',
                    '朔州': 'shuozhou', '晋中': 'jinzhong', '运城': 'yuncheng', '忻州': 'xinzhou', '临汾': 'linfen',
                    '吕梁': 'lvliang'},
             '山东': {'济南': 'jinan', '青岛': 'qingdao', '淄博': 'zibo', '枣庄': 'zaozhuang', '东营': 'dongying', '烟台': 'yantai',
                    '潍坊': 'weifang', '济宁': 'jining', '泰安': 'taian', '威海': 'weihai', '日照': 'rizhao', '莱芜': 'laiwu',
                    '临沂': 'linyi', '德州': 'dezhou', '聊城': 'liaocheng', '滨州': 'binzhou', '菏泽': 'heze'},
             '天津': {'天津': 'tianjin'},
             '新疆': {'乌鲁木齐': 'wulumuqi', '克拉玛依': 'kelamayi', '吐鲁番': 'turpan', '哈密': 'hami', '昌吉': 'changji',
                    '博尔塔拉': 'boertala', '巴音郭楞': 'bayinguoleng', '阿克苏': 'akesu', '克孜勒苏': 'kezilesu', '喀什': 'kashen',
                    '和田': 'hetian', '伊犁': 'yili', '塔城': 'tacheng', '阿勒泰': 'aletai', '石河子': 'shihezi', '阿拉尔': 'aral',
                    '图木舒克': 'tumxuk', '五家渠': 'wujiaqu', '北屯': 'beitun', '铁门关': 'tiemenguan', '双河': 'shuanghe',
                    '可克达拉': 'kokdala', '昆玉': 'kunyu'},
             '西藏': {'拉萨': 'lasa', '日喀则': 'rikaze', '昌都': 'qamdo', '林芝': 'nyingchi', '山南': 'shannan', '那曲': 'naqu',
                    '阿里': 'ali'},
             '云南': {'昆明': 'kunming', '曲靖': 'qujing', '玉溪': 'yuxi', '保山': 'baoshan', '昭通': 'zhaotong', '丽江': 'lijiang',
                    '普洱': 'puer', '临沧': 'lincang', '楚雄': 'chuxiong', '红河': 'honghe', '文山': 'wenshan',
                    '西双版纳': 'xishuangbanna', '大理': 'dali', '德宏': 'dehong', '怒江': 'nujiang', '迪庆': 'diqing'},
             '浙江': {'杭州': 'hangzhou', '宁波': 'ningbo', '温州': 'wenzhou', '嘉兴': 'jiaxing', '湖州': 'huzhou',
                    '绍兴': 'shaoxing', '金华': 'jinhua', '衢州': 'quzhou', '舟山': 'zhoushan', '台州': 'taizhou', '丽水': 'lishui',
                    '舟山群岛新区': 'zhoushanxinqu'}}

# 二手车所有品牌字典
brand_dict = {'奥迪': 'aodi', '阿尔法·罗密欧': 'aerfaluomiou', '阿斯顿·马丁': 'asidunmading', 'AC Schnitzer': 'acschnitzer',
              '安凯客车': 'ankaikeche', 'ARCFOX': 'arcfox', 'ALPINA': 'alpina', '比速汽车': 'bisuqiche', '北汽道达': 'beiqidaoda',
              '宝沃': 'baowo', '北汽新能源': 'beiqixinnengyuan', '北汽幻速': 'beiqihuansu', '北京汽车': 'beijingqiche', '宝骏': 'baojun',
              '巴博斯': 'babosi', '北汽威旺': 'beiqiweiwang', '北汽制造': 'beiqizhizao', '奔驰': 'benchi', '布加迪': 'bujiadi',
              '别克': 'bieke', '宾利': 'binli', '保时捷': 'baoshijie', '比亚迪': 'biyadi', '北汽昌河': 'beiqichanghe',
              '奔腾': 'benteng', '标致': 'biaozhi', '本田': 'bentian', '宝马': 'baoma', '北京': 'beijing', '长安': 'changan',
              '长城': 'changcheng', '长安欧尚': 'changanoushang', '成功汽车': 'chenggongqiche', '长安轻型车': 'changanqingxingche',
              '长安跨越': 'changankuayue', '电咖': 'dianka', '东风风光': 'dongfengfengguang', '东风风行': 'dongfengfengxing',
              'DS': 'ds', '东风风度': 'dongfengfengdu', '东风小康': 'dongfengxiaokang', '东风风神': 'dongfengfengshen',
              '东南': 'dongnan', '道奇': 'daoqi', '大发': 'dafa', '东风': 'dongfeng', '大众': 'dazhong', '丰田': 'fengtian',
              '福特': 'fute', '菲亚特': 'feiyate', '福田': 'futian', '法拉利': 'falali', '福迪': 'fudi', '福汽启腾': 'fuqiqiteng',
              '福田乘用车': 'futianchengyongche', '广汽新能源': 'guangqixinnengyuan', '国金汽车': 'guojinqiche', '观致': 'guanzhi',
              'GMC': 'gmc', '广汽吉奥': 'guangqijiao', '光冈': 'guanggang', '广汽传祺': 'guangqichuanqi', '悍马': 'hanma',
              '黄海': 'huanghai', '红旗': 'hongqi', '华普': 'huapu', '海马': 'haima', '华泰': 'huatai', '哈飞': 'hafei',
              '海格': 'haige', '华骐': 'huaqi', '哈弗': 'hafu', '恒天': 'hengtian', '华凯': 'huakai',
              '华泰新能源': 'huataixinnengyuan', '汉腾汽车': 'hantengqiche', '华利': 'huali', '华颂': 'huasong', 'Icona': 'icona',
              '金旅': 'jinlv', '江铃集团轻汽': 'jianglingjituanqingqi', '九龙': 'jiulong', '金龙': 'jinlong', '江铃': 'jiangling',
              '吉利汽车': 'jiliqiche', 'Jeep': 'jeep', '捷豹': 'jiebao', '金杯': 'jinbei', '江淮': 'jianghuai',
              '江铃集团新能源': 'jianglingjituanxinnengyuan', '君马汽车': 'junmaqiche', '科尼赛克': 'kenisaike', '开瑞': 'kairui',
              '凯迪拉克': 'kaidilake', '克莱斯勒': 'kelaisile', 'KTM': 'ktm', '卡尔森': 'kaersen', '凯翼': 'kaiyi',
              '康迪全球鹰': 'kangdiquanqiuying', '卡升': 'kasheng', '卡威': 'kawei', '陆地方舟': 'ludifangzhou',
              'Lorinser': 'lorinser', '理念': 'linian', '雷诺': 'leinuo', '兰博基尼': 'lanbojini', '路虎': 'luhu',
              '路特斯': 'lutesi', '林肯': 'linken', '雷克萨斯': 'leikesasi', '铃木': 'lingmu', '劳斯莱斯': 'laosilaisi',
              '陆风': 'lufeng', '莲花汽车': 'lianhuaqiche', '力帆汽车': 'lifanqiche', '猎豹汽车': 'liebaoqiche', '领克': 'lingke',
              'LOCAL MOTORS': 'localmotors', '迈巴赫': 'maibahe', 'MINI': 'mini', '玛莎拉蒂': 'mashaladi', '马自达': 'mazida',
              '名爵': 'mingjue', '迈凯伦': 'maikailun', '摩根': 'mogen', '南京金龙': 'nanjingjinlong', '纳智捷': 'nazhijie',
              '欧朗': 'oulang', '欧宝': 'oubao', '讴歌': 'ouge', '帕加尼': 'pajiani', '起亚': 'qiya', '奇瑞': 'qirui',
              '启辰': 'qichen', '庆铃汽车': 'qinglingqiche', '广汽集团': 'guangqijituan', '瑞驰新能源': 'ruichixinnengyuan',
              '瑞麒': 'ruiqi', '如虎': 'ruhu', '荣威': 'rongwei', '日产': 'richan', '萨博': 'sabo', '斯巴鲁': 'sibalu',
              '世爵': 'shijue', '斯柯达': 'sikeda', '三菱': 'sanling', '双龙': 'shuanglong', 'smart': 'smart',
              '双环': 'shuanghuan', '思铭': 'siming', '赛麟': 'sailin', '陕汽通家': 'shanqitongjia',
              '上汽MAXUS': 'shangqimaxus', '斯达泰克': 'sidataike', 'SWM斯威汽车': 'swmsiweiqiche', '腾势': 'tengshi',
              '特斯拉': 'tesila', '泰卡特': 'taikate', '五十铃': 'wushiling', '潍柴英致': 'weichaiyingzhi', '五菱汽车': 'wulingqiche',
              '威麟': 'weilin', '威兹曼': 'weiziman', '沃尔沃': 'woerwo', 'WEY': 'wey', '蔚来': 'weilai', '鑫源': 'xinyuan',
              '雪佛兰': 'xuefolan', '雪铁龙': 'xuetielong', '现代': 'xiandai', '西雅特': 'xiyate', '新凯': 'xinkai', '御捷': 'yujie',
              '一汽': 'yiqi', '野马汽车': 'yemaqiche', '依维柯': 'yiweike', '永源': 'yongyuan', '英菲尼迪': 'yingfeinidi',
              '裕路': 'yulu', '宇通客车': 'yutongkeche', '云度': 'yundu', '驭胜': 'yusheng', '中兴': 'zhongxing', '中华': 'zhonghua',
              '众泰': 'zhongtai', '知豆': 'zhidou', '之诺': 'zhinuo', '全球鹰': 'quanqiuying', '骐铃汽车': "qilingqiche",
              '开沃汽车': 'kaiwoqiche', 'SRM鑫源':'srmxinyuan'}


# 品牌筛选条件与实际返回页面不符情况：
# 阿尔法·罗密欧 -
# 阿斯顿·马丁 -
# ARCFOX -
# 福田乘用车 - 同福田
# 江铃集团轻汽 - '骐铃汽车':"qilingqiche"
# 康迪全球鹰 - '全球鹰': 'quanqiuying'
# 南京金龙 - '开沃汽车':'kaiwoqiche'
# 上汽大通MAXUS - '上汽MAXUS':'shangqimaxus'
# 鑫源 - 'SRM鑫源':'srmxinyuan'

# 请求头设置
session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "close",
    "Accept-Language": "zh-CN,zh;q=0.9"}
# 1.1 获取页面总数、车辆总数
def get_TotalPage_and_TotalCarNum(address, brand):
    choose_url = 'https://www.che168.com/%s/%s/a0_0msdgscncgpi1ltocsp%dexv1/' % (address, brand, 1)
    choose_url = 'https://www.che168.com/%s/%s/a0_0msdgscncgpi1ltocsp%dex/' % (address, brand, 1)
    choose_html = session.get(choose_url, headers=headers, timeout=30)
    bsObj = BeautifulSoup(choose_html.content, 'lxml')
    choose = bsObj.find_all('a', {'class': 'filter-btn'})
    # 获取筛选条件列表，供后续判断筛选条件与实际返回页面是否一致
    choose_list = []
    for i in choose:
        choose_list.append(i.get_text())
    TotalPage = int(bsObj.find('input', {'id': 'TotalPage'})['value'])
    TotalCarNum = int(bsObj.find('input', {'id': 'firstcarnum'})['value'])
    return [TotalPage, TotalCarNum, choose_list]


# 2.2 获取每页车辆URL,添加至列表
def add_car_url_to_list(address, brand, page):
    url = 'https://www.che168.com/%s/%s/a0_0msdgscncgpi1ltocsp%dexv1/' % (address, brand, page)
    url = 'https://www.che168.com/%s/%s/a0_0msdgscncgpi1ltocsp%dex/' % (address, brand, page)
    car_url_list = []
    html = urlopen(url, timeout=30)
    bsObj = BeautifulSoup(html, 'lxml')
    li = bsObj.find_all('li', {'class': 'cards-li list-photo-li'})
    for i in li:
        a_tag = i.find('a')
        a_tag_href = a_tag['href']
        car_url_list.append(a_tag_href)
    return car_url_list

# 3.1.0 长链接转化
def long_url_change(url):
    html = session.get(url, headers=headers, timeout=30)
    time.sleep(random.random() + 1)
    bsObj = BeautifulSoup(html.text, 'lxml')
    mobile_agent = str(bsObj.find('head').find('meta', {'http-equiv': 'mobile-agent'}))
    if "/dealer/" or "/lianmeng/" in mobile_agent:
        re_url = re.compile(r"/(dealer|lianmeng)/\d*/\d*\.html")
    elif "/personal/" in mobile_agent:
        re_url = re.compile(r"/personal/\d*\.html")
    else:
        print('长链接未成功转化：%s' % url)
        return None
    result_url = re.search(re_url, mobile_agent).group()
    return result_url


# 3.1.1 判断每辆二手车的url地址类型并格式化为手机端url
def judge_and_format_url(url):
    # 手机端url前部
    mobile_url_head = "https://m.che168.com"
    # 长链接转化步骤
    if "https" in url:
        new_url = mobile_url_head + long_url_change(url)
    # 短链接转化步骤
    elif "/dealer/" or "/lianmeng/" in url:
        re_url = re.compile(r"/(dealer|lianmeng)/\d*/\d*\.html")
        url = re.search(re_url, url).group()
        new_url = mobile_url_head + url
    elif "/personal/" in url:
        re_url = re.compile(r"/personal/\d*\.html")
        url = re.search(re_url, url).group()
        new_url = mobile_url_head + url
    else:
        print('格式化为手机端URL时出错：%s' % url)
        return None
    return new_url



# 4.1 获取每辆二手车HTML中的车辆信息
def get_CarInfo(url):
    # 车辆手机端与PC端链接URL
    mobile_url = url
    pc_url = url.replace('https://m.che168.com', 'https://www.che168.com')
    print(pc_url)
    get_time = 0
    while get_time < 10:
        try:
            html = session.get(url, headers=headers, timeout=30)
            pc_html = session.get(pc_url, headers=headers, timeout=30)
        except:
            get_time += 1
            time.sleep(10)
        else:
            bsObj = BeautifulSoup(html.text, 'lxml')
            pc_bsObj = BeautifulSoup(pc_html.content, 'lxml')
            script = bsObj.find('body').find('script', {'type': 'text/javascript'}).get_text()
            script = script.strip()
            get_time = 10
    try:
        # 车身颜色
        color = pc_bsObj.find(text='车身颜色').parent.parent.get_text()
        color = color.replace('车身颜色', '')
        print(color)
        # 二手信息公布时间
        publicdate = re.search(re.compile(r"publicdate: '[\d-]*'"), script).group()
        publicdate = re.search(re.compile(r"'[\d-]*'"), publicdate).group()[1:-1]
        # 地区-省份/直辖市 and 城市
        location = bsObj.find('meta', {'name': 'location'})['content']
        location = re.search(re.compile(r"province=\S*;"), location).group()
        province = location[9:location.find(';')]
        city = location[location.find(';') + 6:-1]
        # 品牌id
        brandid = re.search(re.compile(r"brandid: '\d*'"), script).group()
        brandid = re.search(re.compile(r"'\d*'"), brandid).group()[1:-1]
        # 车系id
        seriesid = re.search(re.compile(r"seriesid: '\d*'"), script).group()
        seriesid = re.search(re.compile(r"'\d*'"), seriesid).group()[1:-1]
        # 车型id
        specid = re.search(re.compile(r"specid: '\d*'"), script).group()
        specid = re.search(re.compile(r"'\d*'"), specid).group()[1:-1]
        # 二手价格
        price = re.search(re.compile(r"price: '[0-9\.]*'"), script).group()
        price = re.search(re.compile(r"'[0-9\.]*'"), price).group()[1:-1]
        # 里程/万公里
        mileage = re.search(re.compile(r"mileage: '[0-9\.]*'"), script).group()
        mileage = re.search(re.compile(r"'[0-9\.]*'"), mileage).group()[1:-1]
        # 车龄
        carAge = re.search(re.compile(r"carAge: '[0-9\.]*'"), script).group()
        carAge = re.search(re.compile(r"'[0-9\.]*'"), carAge).group()[1:-1]
        # dealer 与 lianmeng 网站解析方式不一样
        if "/dealer/" in url or "/personal/" in url:
            # 标题-车型名称
            title = bsObj.find('h2', {'class': 'info-tt'}).get_text()
            # 档位/排量
            TransAndPower = bsObj.find(text='档位/排量').parent.previous_sibling.string
            # 首次上牌时间
            registedate = bsObj.find(text='首次上牌').parent.previous_sibling.string
            # 过户次数
            guo_hu = bsObj.find(text='过户次数').parent.previous_sibling.string
            # 查询准迁地-国几
            how_much_guo = bsObj.find(text='查询准迁地').parent.previous_sibling.string
            # 车架号-vincode
            if "/dealer/" in url:
                vincode = re.search(re.compile(r"vincode: '\w*'"), script).group()
                vincode = re.search(re.compile(r"'\w*'"), vincode).group()[1:-1]
            else:
                vincode = re.search(re.compile(r"vincode = '\w*'"), html.text).group()
                vincode = re.search(re.compile(r"'\w*'"), vincode).group()[1:-1]
        elif "/lianmeng/" in url:
            title = bsObj.find('h3').get_text()
            vincode = ''
            source_detail_text = bsObj.find('div', {'class': 'source-detail-text'}).find_all('dl')
            # 档位/排量
            Trans = source_detail_text[2].find('dd').get_text()
            Power = source_detail_text[4].find('dd').get_text()
            TransAndPower = "%s/%s" % (Trans, Power)
            # 首次上牌时间
            registedate = source_detail_text[1].find('dd').get_text()
            # 过户次数
            guo_hu = source_detail_text[5].find('dd').get_text()
            # 查询准迁地-国几
            how_much_guo = source_detail_text[3].find('dd').get_text()
        CarInfo_list = [mobile_url, publicdate, title, province, city, brandid, seriesid, specid, vincode, price,
                        mileage, carAge, TransAndPower, registedate, guo_hu, how_much_guo, html.text, color]
    except:
        CarInfo_list = [mobile_url, "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"]
    return CarInfo_list

def write_csvfile(lists):
    csvfile = open('SecondHandCarVincode.csv', 'a+', newline='', encoding='utf-8')
    writer = csv.writer(csvfile)
    # 遍历每页所有车辆信息列表
    for every_carinfo in lists:
        writer.writerow(every_carinfo)
    csvfile.close()

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

# 采集成功与否记录写入txt文件
def records_txt(tips):
    with open('SecondHandCarVincode.txt', 'a+') as f:
        f.write(tips + '\n')

# 写入数据库
def insert_into_mysql(lists):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='MySQL', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE second_hand_car_info")
    try:
        for i in lists:
            sql = """INSERT INTO 
            second_hand_car 
            (mobile_url,publicdate,title,province,city,brandid,seriesid,specid,vincode,price,mileage,carAge,TransAndPower,registedate,guo_hu,how_much_guo) 
            VALUES 
            ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');""" % (
            i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9], i[10], i[11], i[12], i[13], i[14], i[15])
            # print(sql)
            cur.execute(sql)
            conn.commit()
            sql = """INSERT INTO 
            second_hand_car_html
            (mobile_url,html) 
            VALUES 
            ('%s','''%s''');""" % (i[0], pymysql.escape_string(i[16]))
            cur.execute(sql)
            conn.commit()
    finally:
        cur.close()
        conn.close()

# 省份级别筛选页面总数大于100页时，执行城市级别筛选采集
def city_crawling(province, brand, brand_py):
    # 获取特定省份下的所有城市字典
    province_city_dict = city_dict[province]
    # 城市遍历
    for city, city_py in province_city_dict.items():
        city = city
        city_py = city_py
        # 获取筛选页面总数及车辆总数
        TotalPage_and_TotalCarNum_list = get_TotalPage_and_TotalCarNum(city_py, brand_py)
        # 判断筛选条件与实际返回页面是否一致，一致则继续执行，否则跳出本次循环
        if (brand in TotalPage_and_TotalCarNum_list[2]) and (city in TotalPage_and_TotalCarNum_list[2]):
            pass
        else:
            tips = "%s--%s--筛选条件与实际返回页面不符！！！" % (brand, city)
            print(tips)
            records_txt(tips)
            continue
        TotalPage = TotalPage_and_TotalCarNum_list[0]
        TotalCarNum = TotalPage_and_TotalCarNum_list[1]
        tip = "%s--%s--总页数：%s--维保可查车辆总数：%s" % (brand, city, TotalPage, TotalCarNum)
        # 判断页面总数，确定下步流程
        if TotalPage == 0:
            tips = "%s，无符合条件二手车！！！" % tip
            print(tips)
            records_txt(tips)
        elif TotalPage < 101:
            print("%s，开始采集..." % tip)
            # 遍历每一个页面
            for page in range(1, TotalPage + 1):
                # 初始化每个页面所有二手车信息列表
                page_CarInfo_list = []
                # 获取每一个页面中所有车辆URL列表
                car_url_list = add_car_url_to_list(city_py, brand_py, page)
                time.sleep((random.random() + 1) * 2)
                # 遍历车辆URL列表，格式化为手机端URL
                for no_format_url in car_url_list:
                    # 格式化手机端格式URL
                    format_url = judge_and_format_url(no_format_url)
                    # 获取每辆二手车信息
                    CarInfo_list = get_CarInfo(format_url)
                    # 每辆二手车信息存入每个页面车辆信息列表
                    page_CarInfo_list.append(CarInfo_list)
                    time.sleep(random.random() + 1.5)
                # 每页所有二手车信息追加写入csv文件
                # write_csvfile(page_CarInfo_list)
                # 每页所有二手车信息追加存入数据库
                insert_into_mysql(page_CarInfo_list)
                # 当页采集完成记录
                tips = "%s，第%d页（共%d页）采集完成！" % (tip, page, TotalPage)
                print(tips)
                records_txt(tips)
            # 品牌地区下，全部采集完成记录
            tips = "%s，全部采集完成！" % tip
            print(tips)
            records_txt(tips)
        else:
            tips = "%s，符合条件页面总数大于100页，Next One..." % tip
            print(tips)
            records_txt(tips)

'''
---------------------------------------------采集部分---------------------------------------------
'''
# 手动更改地区
province_dict = {'北京': 'beijing'}
# 手动更改品牌

brand_dict = {'雷克萨斯': 'leikesasi'}

try:
    # 品牌遍历
    for brand, brand_py in brand_dict.items():
        brand = brand
        brand_py = brand_py
        # 省份/直辖市遍历
        for province, province_py in province_dict.items():
            province = province
            province_py = province_py
            # 获取筛选页面总数及车辆总数
            TotalPage_and_TotalCarNum_list = get_TotalPage_and_TotalCarNum(province_py, brand_py)
            time.sleep(random.random() + 1)
            # 判断筛选条件与实际返回页面是否一致，一致则继续执行，否则跳出本次循环
            if (brand in TotalPage_and_TotalCarNum_list[2]) and (province in TotalPage_and_TotalCarNum_list[2]):
                pass
            else:
                tips = "%s--%s--筛选条件与实际返回页面不符！！！" % (brand, province)
                print(tips)
                records_txt(tips)
                continue
            TotalPage = TotalPage_and_TotalCarNum_list[0]
            TotalCarNum = TotalPage_and_TotalCarNum_list[1]
            tip = "%s--%s--总页数：%s--维保可查车辆总数：%s" % (brand, province, TotalPage, TotalCarNum)
            # 判断页面总数，确定下步流程
            if TotalPage == 0:
                tips = "%s，无符合条件二手车！！！" % tip
                print(tips)
                records_txt(tips)
            elif TotalPage < 101:
                print("%s，开始采集..." % tip)
                # 遍历每一个页面
                for page in range(1, TotalPage + 1):
                    # 初始化每个页面所有二手车信息列表
                    page_CarInfo_list = []
                    # 获取每一个页面中所有车辆URL列表
                    car_url_list = add_car_url_to_list(province_py, brand_py, page)
                    time.sleep((random.random() + 1) * 2)
                    # 遍历车辆URL列表，格式化为手机端URL
                    for no_format_url in car_url_list:
                        # 格式化手机端格式URL
                        format_url = judge_and_format_url(no_format_url)
                        # 获取每辆二手车信息
                        CarInfo_list = get_CarInfo(format_url)
                        # 每辆二手车信息存入每个页面车辆信息列表
                        page_CarInfo_list.append(CarInfo_list)
                        time.sleep(random.random() + 1.5)
                    # 每页所有二手车信息追加写入csv文件
                    # write_csvfile(page_CarInfo_list)
                    # 每页所有二手车信息追加存入数据库
                    insert_into_mysql(page_CarInfo_list)
                    # 当页采集完成记录
                    tips = "%s，第%d页（共%d页）采集完成！" % (tip, page, TotalPage)
                    print(tips)
                    records_txt(tips)
                # 品牌地区下，全部采集完成记录
                tips = "%s，全部采集完成！" % tip
                print(tips)
                records_txt(tips)
            else:
                tips = "%s，符合条件页面总数大于100页，正在细化选择..." % tip
                print(tips)
                records_txt(tips)
                # 省份级别筛选页面总数大于100页时，执行城市级别筛选采集
                city_crawling(province, brand, brand_py)
    print("正常退出!")
finally:
    print("程序退出")