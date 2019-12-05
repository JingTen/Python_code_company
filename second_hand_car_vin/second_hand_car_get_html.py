# coding=utf-8
import requests
from bs4 import BeautifulSoup
import time
import re


class GetHTML(object):
    '''获取指定网页数据的类'''
    def __init__(self):
        '''访问网页时的基本参数'''
        # 设置请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/49.0.2623.112 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "close",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        # 设置代理IP
        ip = '123.186.228.56'
        port = '4223'
        self.proxies = {
            'http': '%s:%s' % (ip, port),
            'https': '%s:%s' % (ip, port)
        }
        self.proxies = None
        self.session = requests.Session()
        # 省份直辖市级别字典(key:中文名，value:拼音)
        self.province_dict = {'安徽': 'anhui', '北京': 'beijing', '重庆': 'chongqing', '福建': 'fujian',
                              '广东': 'guangdong', '广西': 'guangxi', '贵州': 'guizhou', '甘肃': 'gansu', '海南': 'hainan',
                              '河南': 'henan', '湖北': 'hubei', '湖南': 'hunan', '河北': 'hebei', '黑龙江': 'heilongjiang',
                              '江苏': 'jiangsu', '江西': 'jiangxi', '吉林': 'jilin', '辽宁': 'liaoning',
                              '内蒙古': 'namenggu', '宁夏': 'ningxia', '青海': 'qinghai', '陕西': 'shan_xi',
                              '四川': 'sichuan', '上海': 'shanghai', '山西': 'shanxi', '山东': 'shandong',
                              '天津': 'tianjin', '新疆': 'xinjiang', '西藏': 'xizang', '云南': 'yunnan', '浙江': 'zhejiang'
                              }
        # 各省份下城市字典
        self.city_dict = {
            '安徽': {'合肥': 'hefei', '芜湖': 'wuhu', '蚌埠': 'bangbu', '淮南': 'huainan', '马鞍山': 'maanshan',
                   '淮北': 'huaibei', '铜陵': 'tongling', '安庆': 'anqing', '黄山': 'huangshan', '滁州': 'chuzhou',
                   '阜阳': 'fu_yang','宿州': 'su_zhou', '六安': 'liuan', '亳州': 'bozhou', '池州': 'chizhou',
                   '宣城': 'xuancheng'},
            '北京': {'北京': 'beijing'},
            '重庆': {'重庆': 'chongqing'},
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
            '贵州': {'贵阳': 'guiyang', '六盘水': 'liupanshui', '遵义': 'zunyi', '安顺': 'anshun', '毕节': 'bijie',
                   '铜仁': 'tongren', '黔西南': 'qianxinan', '黔东南': 'qiandongnan', '黔南': 'qiannan'},
            '甘肃': {'兰州': 'lanzhou', '嘉峪关': 'jiayuguan', '金昌': 'jinchang', '白银': 'baiyin', '天水': 'tianshui',
                   '武威': 'wuwei', '张掖': 'zhangye', '平凉': 'pingliang', '酒泉': 'jiuquan', '庆阳': 'qingyang',
                   '定西': 'dingxi', '陇南': 'longnan', '临夏': 'linxia', '甘南': 'gannan'},
            '海南': {'海口': 'haikou', '三亚': 'sanya', '三沙': 'sansha', '儋州': 'danzhou', '五指山': 'wuzhishan',
                   '琼海': 'qionghai', '文昌': 'wenchang', '万宁': 'wanning', '东方': 'dongfang', '定安': 'dingan',
                   '屯昌': 'tunchang', '澄迈': 'chengmai', '临高': 'lingao', '白沙': 'baisha', '昌江': 'changjiang',
                   '乐东': 'ledong', '陵水': 'lingshui', '保亭': 'baoting', '琼中': 'qiongzhong'},
            '河南': {'郑州': 'zhengzhou', '开封': 'kaifeng', '洛阳': 'luoyang', '平顶山': 'pingdingshan', '安阳': 'anyang',
                   '鹤壁': 'hebi', '新乡': 'xinxiang', '焦作': 'jiaozuo', '濮阳': 'puyang', '许昌': 'xuchang',
                   '漯河': 'luohe', '三门峡': 'sanmenxia', '南阳': 'nanyang', '商丘': 'shangqiu', '信阳': 'xinyang',
                   '周口': 'zhoukou', '驻马店': 'zhumadian', '济源': 'jiyuan'},
            '湖北': {'武汉': 'wuhan', '黄石': 'huangshi', '十堰': 'shiyan', '宜昌': 'yichang', '襄阳': 'xiangyang',
                   '鄂州': 'ezhou', '荆门': 'jingmen', '孝感': 'xiaogan', '荆州': 'jingzhou', '黄冈': 'huanggang',
                   '咸宁': 'xianning', '随州': 'suizhou', '恩施': 'enshi', '仙桃': 'xiantao', '潜江': 'qianjiang',
                   '天门': 'tianmen', '神农架': 'shennongjia'},
            '湖南': {'长沙': 'changsha', '株洲': 'zhuzhou', '湘潭': 'xiangtan', '衡阳': 'hengyang', '邵阳': 'shaoyang',
                   '岳阳': 'yueyang', '常德': 'changde', '张家界': 'zhangjiajie', '益阳': 'yiyang', '郴州': 'chenzhou',
                   '永州': 'yongzhou', '怀化': 'huaihua', '娄底': 'loudi', '湘西': 'xiangxi'},
            '河北': {'石家庄': 'shijiazhuang', '唐山': 'tangshan', '秦皇岛': 'qinhuangdao', '邯郸': 'handan',
                   '邢台': 'xingtai', '保定': 'baoding', '张家口': 'zhangjiakou', '承德': 'chengde', '沧州': 'cangzhou',
                   '廊坊': 'langfang', '衡水': 'hengshui'},
            '黑龙江': {'哈尔滨': 'haerbin', '齐齐哈尔': 'qiqihaer', '鸡西': 'jixi', '鹤岗': 'hegang',
                    '双鸭山': 'shuangyashan', '大庆': 'daqing', '伊春': 'yichun', '佳木斯': 'jiamusi', '七台河': 'qitaihe',
                    '牡丹江': 'mudanjiang', '黑河': 'heihe', '绥化': 'suihua', '大兴安岭': 'daxinganling'},
            '江苏': {'南京': 'nanjing', '无锡': 'wuxi', '徐州': 'xuzhou', '常州': 'changzhou', '苏州': 'suzhou',
                   '南通': 'nantong', '连云港': 'lianyungang', '淮安': 'huaian', '盐城': 'yancheng', '扬州': 'yangzhou',
                   '镇江': 'zhenjiang', '泰州': 'tai_zhou', '宿迁': 'suqian'},
            '江西': {'南昌': 'nanchang', '景德镇': 'jingdezhen', '萍乡': 'ping_xiang', '九江': 'jiujiang', '新余': 'xinyu',
                   '鹰潭': 'yingtan', '赣州': 'ganzhou', '吉安': 'jian', '宜春': 'yi_chun', '抚州': 'fu_zhou',
                   '上饶': 'shangrao'},
            '吉林': {'长春': 'changchun', '吉林': 'jilinshi', '四平': 'siping', '辽源': 'liaoyuan', '通化': 'tonghua',
                   '白山': 'baishan', '松原': 'songyuan', '白城': 'baicheng', '延边': 'yanbian'},
            '辽宁': {'沈阳': 'shenyang', '大连': 'dalian', '鞍山': 'anshan', '抚顺': 'fushun', '本溪': 'benxi',
                   '丹东': 'dandong', '锦州': 'jinzhou', '营口': 'yingkou', '阜新': 'fuxin', '辽阳': 'liaoyang',
                   '盘锦': 'panjin', '铁岭': 'tieling', '朝阳': 'chaoyang', '葫芦岛': 'huludao'},
            '内蒙古': {'呼和浩特': 'huhehaote', '包头': 'baotou', '乌海': 'wuhai', '赤峰': 'chifeng', '通辽': 'tongliao',
                    '鄂尔多斯': 'eerduosi', '呼伦贝尔': 'hulunbeier', '巴彦淖尔': 'bayannaoer', '乌兰察布': 'wulanchabu',
                    '兴安盟': 'xinganmeng', '锡林郭勒盟': 'xilinguolemeng', '阿拉善盟': 'alashanmeng'},
            '宁夏': {'银川': 'yinchuan', '石嘴山': 'shizuishan', '吴忠': 'wuzhong', '固原': 'guyuan', '中卫': 'zhongwei'},
            '青海': {'西宁': 'xining', '海东': 'haidong', '海北': 'haibei', '黄南': 'huangnan', '海南': 'hai_nan',
                   '果洛': 'guoluo', '玉树': 'yushu', '海西': 'haixi'},
            '陕西': {'西安': 'xian', '铜川': 'tongchuan', '宝鸡': 'baoji', '咸阳': 'xianyang', '渭南': 'weinan',
                   '延安': 'yanan', '汉中': 'hanzhong', '榆林': 'yulin', '安康': 'ankang', '商洛': 'shangluo',
                   '西咸新区': 'xixianxinqu'},
            '四川': {'成都': 'chengdu', '自贡': 'zigong', '攀枝花': 'panzhihua', '泸州': 'luzhou', '德阳': 'deyang',
                   '绵阳': 'mianyang', '广元': 'guangyuan', '遂宁': 'suining', '内江': 'neijiang', '乐山': 'leshan',
                   '南充': 'nanchong', '眉山': 'meishan', '宜宾': 'yibin', '广安': 'guangan', '达州': 'dazhou',
                   '雅安': 'yaan', '巴中': 'bazhong', '资阳': 'ziyang', '阿坝': 'aba', '甘孜': 'ganzi',  '凉山': 'liangshan'
                   },
            '上海': {'上海': 'shanghai'},
            '山西': {'太原': 'taiyuan', '大同': 'datong', '阳泉': 'yangquan', '长治': 'zhangzhi', '晋城': 'jincheng',
                   '朔州': 'shuozhou', '晋中': 'jinzhong', '运城': 'yuncheng', '忻州': 'xinzhou', '临汾': 'linfen',
                   '吕梁': 'lvliang'},
            '山东': {'济南': 'jinan', '青岛': 'qingdao', '淄博': 'zibo', '枣庄': 'zaozhuang', '东营': 'dongying',
                   '烟台': 'yantai', '潍坊': 'weifang', '济宁': 'jining', '泰安': 'taian', '威海': 'weihai',
                   '日照': 'rizhao', '莱芜': 'laiwu', '临沂': 'linyi', '德州': 'dezhou', '聊城': 'liaocheng',
                   '滨州': 'binzhou', '菏泽': 'heze'},
            '天津': {'天津': 'tianjin'},
            '新疆': {'乌鲁木齐': 'wulumuqi', '克拉玛依': 'kelamayi', '吐鲁番': 'turpan', '哈密': 'hami', '昌吉': 'changji',
                   '博尔塔拉': 'boertala', '巴音郭楞': 'bayinguoleng', '阿克苏': 'akesu', '克孜勒苏': 'kezilesu',
                   '喀什': 'kashen', '和田': 'hetian', '伊犁': 'yili', '塔城': 'tacheng', '阿勒泰': 'aletai',
                   '石河子': 'shihezi', '阿拉尔': 'aral', '图木舒克': 'tumxuk', '五家渠': 'wujiaqu', '北屯': 'beitun',
                   '铁门关': 'tiemenguan', '双河': 'shuanghe', '可克达拉': 'kokdala', '昆玉': 'kunyu'},
            '西藏': {'拉萨': 'lasa', '日喀则': 'rikaze', '昌都': 'qamdo', '林芝': 'nyingchi', '山南': 'shannan',
                   '那曲': 'naqu', '阿里': 'ali'},
            '云南': {'昆明': 'kunming', '曲靖': 'qujing', '玉溪': 'yuxi', '保山': 'baoshan', '昭通': 'zhaotong',
                   '丽江': 'lijiang', '普洱': 'puer', '临沧': 'lincang', '楚雄': 'chuxiong', '红河': 'honghe',
                   '文山': 'wenshan', '西双版纳': 'xishuangbanna', '大理': 'dali', '德宏': 'dehong', '怒江': 'nujiang',
                   '迪庆': 'diqing'},
            '浙江': {'杭州': 'hangzhou', '宁波': 'ningbo', '温州': 'wenzhou', '嘉兴': 'jiaxing', '湖州': 'huzhou',
                   '绍兴': 'shaoxing', '金华': 'jinhua', '衢州': 'quzhou', '舟山': 'zhoushan', '台州': 'taizhou',
                   '丽水': 'lishui', '舟山群岛新区': 'zhoushanxinqu'}
        }
        # 二手车所有品牌字典
        self.brand_dict = {
            '奥迪': 'aodi', '阿尔法·罗密欧': 'aerfaluomiou', '阿斯顿·马丁': 'asidunmading', 'AC Schnitzer': 'acschnitzer',
            '安凯客车': 'ankaikeche', 'ARCFOX': 'arcfox', 'ALPINA': 'alpina', '比速汽车': 'bisuqiche',
            '北汽道达': 'beiqidaoda', '宝沃': 'baowo', '北汽新能源': 'beiqixinnengyuan', '北汽幻速': 'beiqihuansu',
            '北京汽车': 'beijingqiche', '宝骏': 'baojun', '巴博斯': 'babosi', '北汽威旺': 'beiqiweiwang',
            '北汽制造': 'beiqizhizao', '奔驰': 'benchi', '布加迪': 'bujiadi', '别克': 'bieke', '宾利': 'binli',
            '保时捷': 'baoshijie', '比亚迪': 'biyadi', '北汽昌河': 'beiqichanghe', '奔腾': 'benteng', '标致': 'biaozhi',
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

    def get_TotalPage_and_TotalCarNum(self, brand, brand_py, address, address_py):
        '''
        获取指定地区，品牌的所有二手车页面总数及车辆总数
        :param address: 指定地区
        :param brand: 指定品牌
        :return: [总页数，车辆总数]
        '''
        choose_url = 'https://www.che168.com/%s/%s/a0_0msdgscncgpi1ltocsp%dex/' % (address_py, brand_py, 1)
        choose_html = self.session.get(choose_url, headers=self.headers, proxies=self.proxies, timeout=30)
        bsObj = BeautifulSoup(choose_html.content, 'lxml')
        choose_html.close()
        # 获取筛选条件列表，判断筛选条件与实际返回页面是否一致
        choose = bsObj.find_all('a', {'class': 'filter-btn'})
        choose_list = [i.get_text().replace('・', '·') for i in choose]
        if (address in choose_list) and (brand in choose_list):
            TotalPage = int(bsObj.find('input', {'id': 'TotalPage'})['value'])
            TotalCarNum = int(bsObj.find('input', {'id': 'firstcarnum'})['value'])
            return [TotalPage, TotalCarNum]
        else:
            print('筛选条件与实际返回页面不符：%s' % choose_url)
            return None

    def get_page_car_url(self, address, brand, page):
        '''
        获取指定地区、品牌及页面的所有车辆URL
        :param address:指定地区
        :param brand:指定品牌
        :param page:指定页码
        :return:整个页面的以车辆URL为元素的列表
        '''
        url = 'https://www.che168.com/%s/%s/a0_0msdgscncgpi1ltocsp%dex/' % (address, brand, page)
        car_url_list = []
        html = self.session.get(url, headers=self.headers, proxies=self.proxies, timeout=30)
        bsObj = BeautifulSoup(html.content, 'lxml')
        html.close()
        li = bsObj.find_all('li', {'class': 'cards-li list-photo-li'})
        for i in li:
            a_tag = i.find('a')
            a_tag_href = a_tag['href']
            car_url_list.append(a_tag_href)
        return car_url_list

    def get_CarInfo(self, url, no_format_url, area_dict):
        '''
        获取每辆二手车HTML中的车辆信息
        :param url: 手机端二手车URL
        :return: 该二手车的重要信息
        '''
        # 车辆手机端与PC端链接URL（手机端主要获取VIN及其他重要信息，PC端获取外观颜色）
        mobile_url = url
        if "https" not in no_format_url:
            pc_url = 'https://www.che168.com' + no_format_url
        else:
            pc_url = no_format_url
        # 一直访问单辆二手车信息网页，直到访问成功（最多10次）
        get_time = 0
        while get_time < 10:
            try:
                html = self.session.get(url, headers=self.headers, proxies=self.proxies, timeout=30)
                time.sleep(0.5)
                pc_html = self.session.get(pc_url, headers=self.headers, proxies=self.proxies, timeout=30)
                html.close()
                pc_html.close()
            except:
                get_time += 1
                time.sleep(10)
            else:
                bsObj = BeautifulSoup(html.text, 'lxml')
                pc_bsObj = BeautifulSoup(pc_html.content.decode('gb18030'), 'html.parser')
                script = bsObj.find('body').find('script', {'type': 'text/javascript'}).get_text()
                script = script.strip()
                get_time = 10
        try:
            # title
            title = bsObj.find('h5', {'class': 'car-title two-line'}).get_text()
            # infoid
            infoid = re.search(re.compile(r"infoId = parseInt\('[\d]*'"), script).group()
            infoid = re.search(re.compile(r"'[\d]*'"), infoid).group()[1:-1]
            # 二手信息公布时间
            publicdate = re.search(re.compile(r"publicdate: '[\d-]*'"), script).group()
            publicdate = re.search(re.compile(r"'[\d-]*'"), publicdate).group()[1:-1]
            # 地区-省份/直辖市 and 城市 id
            p_id = re.search(re.compile(r"pid: '\d*'"), script).group()
            p_id = re.search(re.compile(r"'\d*'"), p_id).group()[1:-1]
            province = area_dict[p_id]
            c_id = re.search(re.compile(r"cid: '\d*'"), script).group()
            c_id = re.search(re.compile(r"'\d*'"), c_id).group()[1:-1]
            city = area_dict[c_id]
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
            # 车辆档案
            base_data = bsObj.find('ul', {'class': 'base-data'}).find_all('li')
            # 车辆档案-首次上牌
            registedate = base_data[0].find('p', {'class': 'item-status'}).get_text()
            # 车辆档案-查询准迁地-国几
            how_much_guo = base_data[2].find('p', {'class': 'item-status'}).get_text()
            # 车辆档案-排量、变速箱
            power = base_data[3].find('p', {'class': 'item-status'}).get_text()
            trans = base_data[4].find('p', {'class': 'item-status'}).get_text()
            # 过户次数
            guo_hu = base_data[5].find('p', {'class': 'item-status'}).get_text()
            # 车辆档案-牌照地
            license_plate_area = base_data[6].find('p', {'class': 'item-status'}).get_text()
            vincode = re.search(re.compile(r"vincode: '\w*'"), script).group()
            vincode = re.search(re.compile(r"'\w*'"), vincode).group()[1:-1]
            # 车身颜色
            if ("/dealer/" in url) or ("/personal/" in url):
                color = pc_bsObj.find(text='车身颜色').parent.parent.get_text()
                color = color.replace('车身颜色', '')
            elif "/lianmeng/" in url:
                color = pc_bsObj.find(text='颜　　色：').parent.parent.get_text()
                color = color.replace('颜　　色：', '').strip()

            CarInfo_list = [infoid, mobile_url, publicdate, title, province, city, brandid, seriesid, specid, vincode,
                            price, mileage, carAge, trans, power, registedate, guo_hu, how_much_guo, color,
                            license_plate_area, html.text]
        except:
            print(url, '未正确获取二手车信息！')
            CarInfo_list = ["-", mobile_url, "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-",
                            "-", "-", "-", "-", html.text]
        return CarInfo_list

    def get_area_info(self, url='https://www.che168.com/china/'):
        '''
        获取地区及其ID、拼音信息
        :param url: 汽车之家二手车主页
        :return:
        '''
        r = self.session.get(url, headers=self.headers, timeout=30)
        bsObj = BeautifulSoup(r.content, 'lxml')
        r.close()
        div_Area = bsObj.find('div', {'id': 'div_Area'})
        # 获取省份（直辖市）及其ID，以及省份（直辖市）拼音，存入字典
        p_dict = {}
        dl = div_Area.find_all('dl')
        for ii in dl:
            # 获取首大写字母
            nu = ii['id']
            # 查找各大写字母下的所有省份（直辖市）并遍历
            dt = ii.find_all('dt')
            for jj in dt:
                p_info = jj.find('a')
                pid = p_info['pid']
                p_py = p_info['href']
                p_py = re.compile(r'^/[a-z_]*/').search(p_py).group().replace('/', '')
                p_dict[pid] = [p_py, nu]
        # 获取省份（直辖市）、城市及其ID，以及城市拼音，存入列表
        area_info = []
        dd = div_Area.find_all('dd')
        for i in dd:
            a = i.find_all('a')
            for j in a:
                pidname = j['pidname']
                pid = j['pid']
                cidname = j.get_text()
                cid = j['cid']
                c_py = j['href']
                c_py = re.compile(r'^/[a-z_]*/').search(c_py).group().replace('/', '')
                p_py = p_dict[pid][0]
                nu = p_dict[pid][1]
                area_info.append([nu, pidname, pid, p_py, cidname, cid, c_py])
        return area_info



class FormatURL(object):
    '''格式化或转化URL的类'''
    def __init__(self):
        '''设置请求头'''
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/49.0.2623.112 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "close",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        self.session = requests.Session()

    def long_url_change(self, url):
        '''每辆二手车信息URL为长链接时需要转化'''
        html = self.session.get(url, headers=self.headers, timeout=30)
        bsObj = BeautifulSoup(html.content.decode('gb18030'), 'html.parser')
        mobile_agent = str(bsObj.find('head').find('meta', {'http-equiv': 'mobile-agent'}))
        if "/dealer/" or "/lianmeng/" in mobile_agent:
            re_url = re.compile(r"/(dealer|lianmeng)/\d*/\d*\.html")
        elif "/personal/" in mobile_agent:
            re_url = re.compile(r"/personal/\d*\.html")
        else:
            print('长链接未成功转化：%s' % url)
            return None
        result_url = re.search(re_url, mobile_agent).group()
        # 判断是否为诚信联盟（mobile_agent结果不分dealer与lianmeng）
        lianmeng = bsObj.find('div', {'class': 'sincerity-subtitle'})
        if lianmeng:
            result_url = result_url.replace('dealer', 'lianmeng')
        return result_url

    def judge_and_format_url(self, url):
        '''
        判断每辆二手车的url地址类型并格式化为手机端url
        :param url: 车辆URL
        :return: 格式化后手机端URL
        '''
        # 手机端url前部
        mobile_url_head = "https://m.che168.com"
        # 长链接转化步骤
        if "https" in url:
            new_url = mobile_url_head + self.long_url_change(url)
        # 短链接转化步骤
        elif ("/dealer/" in url) or ("/lianmeng/" in url):
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
