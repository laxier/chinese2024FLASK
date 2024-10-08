# hsk_checker.py

from typing import Dict, Set, Optional, List
from sqlalchemy.orm import Session
from app.models import Card  # Assuming your Card model is named 'character'
from app import app, db
from app.models import Deck, character
import threading
from typing import Dict, Set, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models import character
from tqdm import tqdm
from sqlalchemy import exc

# HSK word lists (simplified for brevity, you should use complete lists)
hsk_levels: Dict[int, Set[str]] = {
    1: {"爱", "八", "爸爸", "杯子", "北京", "本", "不客气", "不", "菜", "茶", "吃", "出租车", "打电话", "大", "的",
        "点", "电脑", "电视", "电影", "东西", "都", "读", "对不起", "多", "多少", "儿子", "二", "饭店", "飞机", "分钟",
        "高兴", "个", "工作", "狗", "汉语", "好", "号", "喝", "和", "很", "后面", "回", "会", "几", "家", "叫", "今天",
        "九", "开", "看", "看见", "块", "来", "老师", "了", "冷", "里", "六", "吗", "妈妈", "买", "猫", "没关系",
        "没有", "米饭", "名字", "明天", "哪", "哪儿", "那", "呢", "能", "你", "年", "女儿", "朋友", "漂亮", "苹果",
        "七", "前面", "钱", "请", "去", "热", "人", "认识", "三", "商店", "上", "上午", "少", "谁", "什么", "十",
        "时候", "是", "书", "水", "水果", "睡觉", "说", "四", "岁", "他", "她", "太", "天气", "听", "同学", "喂", "我",
        "我们", "五", "喜欢", "下", "下午", "下雨", "先生", "现在", "想", "小", "小姐", "些", "写", "谢谢", "星期",
        "学生", "学习", "学校", "一", "一点儿", "医生", "医院", "衣服", "椅子", "有", "月", "再见", "在", "怎么",
        "怎么样", "这", "中国", "中午", "住", "桌子", "字", "昨天", "做", "坐", "你好"},
    2: {
        "吧", "白", "百", "帮助", "报纸", "比", "别", "宾馆", "长", "唱歌", "出",
        "穿", "次", "从", "错", "打篮球", "大家", "到", "得", "等", "弟弟",
        "第一", "懂", "对", "对", "房间", "非常", "服务员", "高", "告诉", "哥哥",
        "给", "公共汽车", "公司", "贵", "过", "孩子", "还", "好吃", "黑", "红",
        "火车站", "机场", "鸡蛋", "件", "教室", "姐姐", "介绍", "近", "进",
        "就", "觉得", "咖啡", "开始", "考试", "可能", "可以", "课", "快",
        "快乐", "累", "离", "两", "零", "路", "旅游", "卖", "慢", "忙", "每",
        "妹妹", "门", "面条", "男", "您", "牛奶", "女", "旁边", "跑步",
        "便宜", "票", "妻子", "起床", "千", "铅笔", "晴", "去年", "让", "日",
        "上班", "身体", "生病", "生日", "时间", "事情", "手表", "手机",
        "说话", "送", "虽然…但是…", "它", "踢足球", "题", "跳舞", "外",
        "完", "玩", "晚上", "往", "为什么", "问", "问题", "希望", "西瓜",
        "洗", "小时", "笑", "新", "姓", "休息", "雪", "颜色", "眼睛", "羊肉",
        "药", "要", "也", "一下", "已经", "一起", "意思", "因为…所以…",
        "阴", "游泳", "右边", "鱼", "远", "运动", "再", "早上", "丈夫",
        "找", "着", "真", "正在", "知道", "准备", "走", "最", "左边"
    },
    3: {
        "啊", "阿姨", "矮", "爱好", "安静", "把", "搬", "班", "办法", "办公室", "半", "帮忙", "包", "饱", "北方", "被",
        "鼻子", "比较", "比赛", "笔记本", "必须", "变化", "别人", "冰箱", "不但…而且…", "菜单", "参加", "草", "层",
        "差", "超市", "衬衫", "城市", "成绩", "迟到", "除了", "船", "春", "词典", "聪明", "打扫", "打算", "带", "担心",
        "蛋糕", "当然", "地", "灯", "地方", "地铁", "地图", "电梯", "电子邮件", "东", "冬", "动物", "短", "段", "锻炼",
        "多么", "饿", "耳朵", "发", "发烧", "发现", "方便", "放", "放心", "分", "复习", "附近", "干净", "感冒",
        "感兴趣", "刚才", "个子", "根据", "跟", "更", "公斤", "公园", "故事", "刮风", "关", "关系", "关心", "关于",
        "国家", "过", "过去", "还是", "害怕", "黑板", "后来", "护照", "花", "画", "坏", "欢迎", "环境", "还", "换",
        "黄河", "回答", "会议", "或者", "几乎", "机会", "极", "季节", "记得", "检查", "简单", "健康", "见面", "讲",
        "教", "脚", "角", "接", "街道", "结婚", "结束", "节目", "节日", "解决", "借", "经常", "经过", "经理", "久",
        "旧", "句子", "决定", "可爱", "渴", "刻", "客人", "空调", "口", "哭", "裤子", "筷子",
        "蓝", "老", "离开", "礼物", "历史", "脸", "练习", "辆", "聊天", "了解", "邻居", "留学", "楼", "绿", "马",
        "马上", "满意", "帽子", "啤酒", "米", "面包", "明白", "拿", "奶奶", "南", "难", "难过", "年级", "年轻", "鸟",
        "努力", "爬山", "盘子", "胖", "照顾", "照片", "照相机", "只", "只有…才…", "中间", "中文",
        "皮鞋", "瓶子", "其实", "其他", "奇怪", "骑", "起飞", "起来", "清楚", "请假", "秋", "裙子", "然后", "热情",
        "认为", "认真", "容易", "如果", "伞", "上网", "声音", "生气", "世界", "试", "瘦", "叔叔", "舒服", "数学", "树",
        "刷牙", "双", "水平", "司机", "太阳", "特别", "疼", "提高", "体育", "甜", "条", "同事", "同意", "头发", "突然",
        "图书馆", "腿", "完成", "碗", "万", "忘记", "为", "为了", "位", "文化", "西", "习惯", "洗手间", "洗澡", "夏",
        "先", "相信", "香蕉", "像", "向", "小心", "校长", "新闻", "新鲜", "信用卡", "行李箱", "熊猫", "需要", "选择",
        "要求", "爷爷", "一直", "一定", "一共", "一会儿", "一样", "以前", "一般", "一边", "音乐", "银行", "饮料",
        "应该", "影响", "用", "游戏", "有名", "又", "遇到", "元", "愿意", "月亮", "越", "站", "张", "长", "着急",
        "终于", "种", "重要", "周末", "主要", "注意", "自己", "自行车", "总是", "嘴", "最后", "最近", "作业"
    },
    4: {
        "爱情", "安排", "安全", "按时", "按照", "百分之", "棒", "包子", "保护", "保证", "报名", "抱", "抱歉", "倍",
        "本来", "笨",
        "比如", "毕业", "遍", "标准", "表格", "表示", "表演", "表扬", "饼干", "并且", "博士", "不过", "不得不", "不管",
        "不仅",
        "部分", "擦", "猜", "材料", "参观", "餐厅", "厕所", "差不多", "尝", "长城", "长江", "场", "超过", "乘坐",
        "成功", "成为",
        "诚实", "吃惊", "重新", "抽烟", "出差", "出发", "出生", "出现", "厨房", "传真", "窗户", "词语", "从来", "粗心",
        "存",
        "错误", "答案", "打扮", "打扰", "打印", "打招呼", "打折", "打针", "大概", "大使馆", "大约", "大夫", "戴", "当",
        "当时",
        "刀", "导游", "倒", "到处", "到底", "道歉", "得", "得意", "登机牌", "等", "低", "底", "地点", "地球", "地址",
        "掉",
        "调查", "丢", "动作", "堵车", "肚子", "短信", "对话", "对面", "对于", "儿童", "而", "发生", "发展", "法律",
        "翻译",
        "烦恼", "反对", "方法", "方面", "方向", "房东", "放弃", "放暑假", "放松", "份", "丰富", "否则", "符合", "付款",
        "复印",
        "复杂", "富", "父亲", "负责", "改变", "干杯", "感动", "感觉", "感情", "感谢", "敢", "赶", "干", "刚",
        "高速公路", "胳膊",
        "各", "公里", "功夫", "工资", "共同", "够", "购物", "估计", "鼓励", "故意", "顾客", "挂", "关键", "观众",
        "管理", "光",
        "广播", "广告", "逛", "规定", "国籍", "国际", "果汁", "过程", "海洋", "害羞", "寒假", "汗", "航班", "好处",
        "好像", "号码",
        "合格", "合适", "盒子", "厚", "后悔", "互联网", "互相", "护士", "怀疑", "回忆", "活动", "活泼", "火", "获得",
        "基础",
        "激动", "积极", "积累", "即使", "及时", "寄", "技术", "既然", "继续", "计划", "记者", "加班", "加油站", "家具",
        "假",
        "价格", "坚持", "减肥", "减少", "建议", "将来", "奖金", "降低", "降落", "交", "交流", "交通", "郊区", "骄傲",
        "饺子",
        "教授", "教育", "接受", "接着", "结果", "节", "节约", "解释", "尽管", "紧张", "禁止", "进行", "京剧", "精彩",
        "经济",
        "经历", "经验", "景色", "警察", "竞争", "竟然", "镜子", "究竟", "举", "举办", "举行", "拒绝", "聚会", "距离",
        "开玩笑",
        "开心", "看法", "烤鸭", "考虑", "棵", "科学", "咳嗽", "可怜", "可是", "可惜", "客厅", "肯定", "空", "空气",
        "恐怕",
        "苦", "矿泉水", "困", "困难", "垃圾桶", "拉", "辣", "来不及", "来得及", "来自", "懒", "浪费", "浪漫", "老虎",
        "冷静",
        "理发", "理解", "理想", "礼拜天", "礼貌", "例如", "力气", "厉害", "俩", "联系", "连", "凉快", "零钱", "另外",
        "流利",
        "流行", "留", "旅行", "乱", "律师", "麻烦", "马虎", "满", "毛", "毛巾", "美丽", "梦", "迷路", "密码", "免费",
        "秒",
        "民族", "母亲", "目的", "耐心", "难道", "难受", "内", "内容", "能力", "年龄", "弄", "暖和", "偶尔", "排队",
        "排列",
        "判断", "陪", "批评", "皮肤", "脾气", "篇", "骗", "乒乓球", "平时", "破", "葡萄", "普遍", "普通话", "其次",
        "其中",
        "气候", "千万", "签证", "敲", "桥", "巧克力", "亲戚", "轻", "轻松", "情况", "穷", "区别", "取", "全部", "缺点",
        "缺少",
        "却", "确实", "然而", "热闹", "任何", "任务", "扔", "仍然", "日记", "入口", "散步", "森林", "沙发", "伤心",
        "商量",
        "稍微", "勺子", "社会", "深", "申请", "甚至", "生活", "生命", "生意", "省", "剩", "失败", "失望", "师傅",
        "十分",
        "实际", "实在", "使", "使用", "世纪", "是否", "适合", "适应", "收", "收入", "收拾", "首都", "首先", "受不了",
        "受到",
        "售货员", "输", "熟悉", "数量", "数字", "帅", "顺便", "顺利", "顺序", "说明", "硕士", "死", "塑料袋", "速度",
        "酸",
        "随便", "随着", "孙子", "所有", "台", "抬", "态度", "弹钢琴", "谈", "汤", "糖", "躺", "趟", "讨论", "讨厌",
        "特点",
        "提", "提供", "提前", "提醒", "填空", "条件", "停", "挺", "通过", "通知", "同情", "同时", "推", "推迟", "脱",
        "袜子",
        "完全", "往往", "网球", "网站", "危险", "卫生间", "味道", "温度", "文章", "污染", "无", "无聊", "无论", "误会",
        "吸引",
        "西红柿", "咸", "现金", "羡慕", "相反", "相同", "香", "详细", "响", "橡皮", "消息", "小吃", "小伙子", "小说",
        "效果",
        "笑话", "心情", "辛苦", "信封", "信息", "信心", "兴奋", "行", "醒", "幸福", "性别", "性格", "修理", "许多",
        "学期",
        "呀", "压力", "牙膏", "亚洲", "严格", "严重", "盐", "研究", "演出", "演员", "眼镜", "阳光", "养成", "样子",
        "邀请",
        "要是", "钥匙", "也许", "叶子", "页", "一切", "以", "以为", "意见", "艺术", "因此", "引起", "印象", "赢",
        "应聘",
        "勇敢", "永远", "优点", "优秀", "幽默", "尤其", "由", "由于", "邮局", "友好", "友谊", "有趣", "于是", "愉快",
        "与",
        "羽毛球", "语法", "语言", "预习", "原来", "原谅", "原因", "约会", "阅读", "云", "允许", "杂志", "咱们", "暂时",
        "脏",
        "责任", "增加", "增长", "招聘", "整理", "正常", "正好", "正式", "证明", "之", "支持", "只好", "之一", "值得",
        "直接",
        "职业", "植物", "指", "只要", "质量", "至于", "重点", "重视", "周围", "猪", "逐渐", "主持", "主意", "祝",
        "专门",
        "专业", "赚", "准确", "准时", "仔细", "自然", "自由", "综合", "总结", "租", "最好", "尊重", "左右", "作家",
        "作用",
        "作者", "座", "座位", "做生意"
    },
    5: {'批评', '承认', '欣赏'},
    6: {'抽象', '具体', '分析', '综合', '评价'}
}


def get_hsk_level(word: str) -> Optional[int]:
    """
    Determine the HSK level of a given word.

    :param word: Chinese word to check
    :return: HSK level (1-6) or None if not found
    """
    for level, word_set in hsk_levels.items():
        if word in word_set:
            return level
    return None


def update_hsk_levels(db_session: Session, batch_size: int = 100) -> None:
    """
    Update HSK levels for all characters in the database.

    :param db_session: SQLAlchemy database session
    :param batch_size: Number of records to process in each batch
    """
    total_count = db_session.query(character).count()

    for offset in range(0, total_count, batch_size):
        characters = db_session.query(Card).offset(offset).limit(batch_size).all()
        for char in characters:
            hsk_level = get_hsk_level(char.chinese)
            if hsk_level is not None and char.hsk_level != hsk_level:
                char.hsk_level = hsk_level

        db_session.commit()
        print(f"Processed {min(offset + batch_size, total_count)} / {total_count} characters")


def get_characters_by_hsk_level(db_session: Session, level: int) -> List[character]:
    """
    Retrieve all characters of a specific HSK level from the database.

    :param db_session: SQLAlchemy database session
    :param level: HSK level to filter by (1-6)
    :return: List of character objects
    """
    return db_session.query(Card).filter_by(hsk_level=level).all()


# You can add more functions here as needed, such as:
# - Function to add new words to HSK levels
# - Function to export HSK words to a file
# - Function to import HSK words from a file
def process_all_words_to_hsk_level(db_session: Session, batch_size: int = 1000) -> Dict[str, int]:
    """
    Process all words in the database to assign HSK levels.

    :param db_session: SQLAlchemy database session
    :param batch_size: Number of records to process in each batch
    :return: Dictionary with statistics about the process
    """
    total_count = db_session.query(Card).count()
    processed_count = 0
    updated_count = 0
    error_count = 0

    progress_bar = tqdm(total=total_count, desc="Processing characters")

    try:
        for offset in range(0, total_count, batch_size):
            characters = db_session.query(Card).offset(offset).limit(batch_size).all()

            for char in characters:
                try:
                    hsk_level = get_hsk_level(char.chinese)
                    if hsk_level is not None and char.hsk_level != hsk_level:
                        char.hsk_level = hsk_level
                        updated_count += 1
                    processed_count += 1
                except Exception as e:
                    print(f"Error processing character {char.chinese}: {str(e)}")
                    error_count += 1

            db_session.commit()
            progress_bar.update(len(characters))

    except SQLAlchemyError as e:
        print(f"Database error occurred: {str(e)}")
        db_session.rollback()
    finally:
        progress_bar.close()

    return {
        "total_processed": processed_count,
        "updated": updated_count,
        "errors": error_count
    }


# main.py

from app import app, db
from app.models import Deck, character
import threading
from sqlalchemy import exc


def main():
    with app.app_context():
        try:
            # Process all words and assign HSK levels
            results = process_all_words_to_hsk_level(db.session)

            print("HSK Level Assignment Results:")
            print(f"Total processed: {results['total_processed']}")
            print(f"Updated: {results['updated']}")
            print(f"Errors: {results['errors']}")

        except exc.SQLAlchemyError as e:
            print(f"An error occurred: {str(e)}")
            db.session.rollback()
        finally:
            db.session.close()


if __name__ == "__main__":
    main()
