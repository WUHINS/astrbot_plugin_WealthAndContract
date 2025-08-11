from astrbot.api.all import *
from astrbot.api.message_components import Image, Plain
from datetime import datetime, timedelta
import yaml
import os
import requests
import pytz
import re
import random
import logging
import shutil
from PIL import ImageColor, Image as PILImage
from PIL import ImageDraw, ImageFont, ImageOps
from io import BytesIO
from typing import Dict, Any, Optional, List, Tuple

#region ==================== 插件配置 ====================
# 路径配置
PLUGIN_DIR = os.path.join('data', 'plugins', 'astrbot_plugin_wealthandcontract')
DATA_FILE = os.path.join('data', 'plugins_WealthAndContract_data', 'WAC_data.yml')
PROP_DATA_FILE = os.path.join('data', 'plugins_WealthAndContract_data', 'WAC_propdata.yml')
SOCIAL_DATA_FILE = os.path.join('data', 'plugins_WealthAndContract_data', 'WAC_social_data.yml')  # 社交数据文件
TIME_DATA_FILE = os.path.join('data', 'plugins_WealthAndContract_data', 'WAC_time_data.yml')  # 时间数据文件
LOG_FILE = os.path.join('data', 'plugins_WealthAndContract_data', 'WAC_operations.log')  # 操作日志文件
IMAGE_DIR = os.path.join(PLUGIN_DIR, 'images')
FONT_PATH = os.path.join(PLUGIN_DIR, '请以你的名字呼唤我.ttf')

# API配置
AVATAR_API = "http://q.qlogo.cn/headimg_dl?dst_uin={}&spec=640&img_type=jpg"
BG_API = "https://api.fuchenboke.cn/api/dongman.php"

# 经济系统配置
WEALTH_LEVELS = [
    (0,    "平民", 0.25),
    (500,  "小资", 0.5),
    (2000, "富豪", 0.75),
    (5000, "巨擘", 1.0),
    (10000, "成功人士", 1.25)
]
WEALTH_BASE_VALUES = {
    "平民": 100,
    "小资": 500,
    "富豪": 2000,
    "巨擘": 5000,
    "成功人士": 10000
}
## 彩票配置
LOTTERY_PRICE = 5.0  # 彩票价格
LOTTERY_WIN_RATE = 0.02  # 中奖概率
LOTTERY_MIN_PRIZE = 1500.0  # 最小奖金
LOTTERY_MAX_PRIZE = 7000.0  # 最大奖金
MAX_ASSETS_FOR_LOTTERY = 500.0  # 允许购买彩票的最大总资产

BASE_INCOME = 100.0 #基础值

# 工作配置
JOBS = {
    "搬砖": {
        "reward": (15.0, 20.0),      # 收益范围
        "success_rate": 1.0,
        "risk_cost": (0.0, 0.0),     # 失败惩罚范围
        "success_msg": "⛏️ {worker_name} 去工地搬了一天砖，累得筋疲力尽。你获得了 {reward:.2f} 金币！",
        "failure_msg": ""
    },
    "送外卖": {
        "reward": (20.0, 25.0),
        "success_rate": 0.9,
        "risk_cost": (1.0, 3.0),
        "success_msg": "🚴 {worker_name} 一天骑车狂奔送外卖，终于赚到 {reward:.2f} 金币！",
        "failure_msg": "🍔 {worker_name} 在送餐路上摔了一跤，赔了客户的订单，损失 {risk_cost:.2f} 金币。"
    },
    "送快递": {
        "reward": (25.0, 30.0),
        "success_rate": 0.8,
        "risk_cost": (3.0, 6.0),
        "success_msg": "📦 {worker_name} 风里雨里送快递，终于赚到了 {reward:.2f} 金币。",
        "failure_msg": "📭 {worker_name} 快递丢件，被客户投诉，赔了 {risk_cost:.2f} 金币。"
    },
    "家教": {
        "reward": (30.0, 35.0),
        "success_rate": 0.7,
        "risk_cost": (6.0, 9.0),
        "success_msg": "📚 {worker_name} 耐心辅导学生，家长满意，赚得 {reward:.2f} 金币。",
        "failure_msg": "😵 {worker_name} 学生成绩没提高，被辞退，损失 {risk_cost:.2f} 金币。"
    },
    "挖矿": {
        "reward": (35.0, 40.0),
        "success_rate": 0.6,
        "risk_cost": (9.0, 12.0),
        "success_msg": "⛏️ {worker_name} 在地下挖矿一整天，挖到了珍贵矿石，获得 {reward:.2f} 金币！",
        "failure_msg": "💥 {worker_name} 不小心引发了塌方事故，受伤并损失 {risk_cost:.2f} 金币。"
    },
    "代写作业": {
        "reward": (40.0, 45.0),
        "success_rate": 0.5,
        "risk_cost": (12.0, 15.0),
        "success_msg": "📘 {worker_name} 偷偷帮人代写作业，轻松赚到 {reward:.2f} 金币。",
        "failure_msg": "📚 {worker_name} 被老师发现代写，被罚 {risk_cost:.2f} 金币。"
    },
    "奶茶店": {
        "reward": (45.0, 50.0),
        "success_rate": 0.4,
        "risk_cost": (15.0, 18.0),
        "success_msg": "🧋 {worker_name} 在奶茶店忙了一天，挣了 {reward:.2f} 金币。",
        "failure_msg": "🥤 {worker_name} 手滑打翻整桶奶茶，赔了 {risk_cost:.2f} 金币。"
    },
    "偷窃苏特尔的宝库": {
        "reward": (500.0, 500.0),          # 固定奖励
        "success_rate": 0.02,      # 5%的成功率
        "risk_cost": (10.0, 10.0),         # 固定惩罚
        "success_msg": "🌟 {worker_name} 偷窃成功，从苏特尔的钱包中获得了难以置信的 {reward:.2f} 金币！",
        "failure_msg": "💫 {worker_name} 偷窃失败，被苏特尔当场抓获，幕后黑手的你赔付了{risk_cost:.2f} 金币了。"
    },
    "卖淫": {
        "reward": (80.0, 350.0),  # 高报酬
        "success_rate": 0.35,     # 65%失败率
        "risk_cost": (30.0, 50.0), # 高额风险
        "success_msg": "💄 {worker_name} 整整卖淫了一整夜，赚取了 {reward:.1f} 金币！",
        "failure_msg": "🩹 {worker_name} 不慎怀孕了，打胎花销 {risk_cost:.1f} 金币。"
    }
}

# 道具系统配置
SHOP_ITEMS = {
    "驯服贴": {
        "price": 1000,
        "description": "永久绑定性奴，防止被制裁/赎身/强制购买",
        "max_per_user": 3,
        "command": "驯服贴"
    },
    "强制购买符": {
        "price": 500,
        "description": "强制购买已有主人的性奴",
        "command": "强制购买"
    },
    "自由身保险": {
        "price": 800,
        "description": "24小时内不被购买为性奴",
        "duration_hours": 24,
        "command": "自由身保险"
    },
    "红星制裁": {
        "price": 5,
        "description": "对全群满足条件的用户进行制裁（每人每天限用1次）",
        "command": "红星制裁"
    },
    "市场侵袭": {
        "price": 400,
        "description": "对指定用户发起侵袭（每人每小时限用1次）",
        "command": "市场侵袭"
    },
    "卡天亚戒指": {
        "price": 1500,
        "description": "缔结恋人关系所需的道具",
        "command": "卡天亚戒指"
    },
    "一壶烈酒": {
        "price": 800,
        "description": "缔结兄弟关系所需的道具",
        "command": "一壶烈酒"
    },
    "黑金卡": {
        "price": 3000,
        "description": "缔结包养关系所需的道具",
        "command": "黑金卡"
    },
    "玫瑰花束": {
        "price": 300,
        "description": "赠送可增加5-10点好感度",
        "command": "赠送玫瑰花束"
    },
    "定制蛋糕": {
        "price": 500,
        "description": "赠送可增加8-15点好感度",
        "command": "赠送定制蛋糕"
    }
}

# 社交系统配置
DATE_EVENTS = [
    {
        "id": "movie",
        "name": "电影院约会",
        "description": "你们在电影院看了一场感人的电影，相视一笑。",
        "favorability_change": (3, 5)
    },
    {
        "id": "rain",
        "name": "被雨淋湿",
        "description": "约会途中突然下雨，两人被淋湿，气氛有些尴尬。",
        "favorability_change": (-2, 0)
    },
    {
        "id": "restaurant",
        "name": "共进晚餐",
        "description": "你们在一家浪漫的餐厅共进晚餐，氛围很好。",
        "favorability_change": (2, 4)
    },
    {
        "id": "amusement_park",
        "name": "游乐园",
        "description": "在游乐园里，你们勇敢地尝试了各种刺激的项目，留下了美好的回忆。",
        "favorability_change": (2, 5)
    },
    {
        "id": "cooking",
        "name": "一起做饭",
        "description": "你们一起在家做饭，虽然过程有些混乱，但最终做出了美味的菜肴。",
        "favorability_change": (2, 5)
    },
    {
        "id": "star_gazing",
        "name": "观星",
        "description": "在郊外的草地上，你们一起观星，聊着各自的梦想和未来。",
        "favorability_change": (3, 5)
    },
    {
        "id": "argument",
        "name": "争吵",
        "description": "约会过程中，因为一些小事，你们发生了争执，气氛有些紧张。",
        "favorability_change": (-3, -1)
    }
]

RELATION_LEVELS = {
    "0-19": "陌生人",
    "20-49": "熟人",
    "50-89": "朋友",
    "90-99": "挚友", 
    "100": "唯一的你",
    "101+": "灵魂伴侣"
}

SPECIAL_RELATION_TYPES = {
    "恋人": "lover",
    "兄弟": "brother",
    "包养": "patron"
}

RELATION_TYPE_NAMES = {
    "lover": "恋人",
    "brother": "兄弟", 
    "patron": "包养关系"
}

SPECIAL_RELATION_ITEMS = {
    "恋人": "卡天亚戒指",
    "兄弟": "一壶烈酒",
    "包养": "黑金卡"
}

# 时区配置
SHANGHAI_TZ = pytz.timezone('Asia/Shanghai')

# 配置日志
def setup_logger():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logger = logging.getLogger('WAC_operations')
    logger.setLevel(logging.INFO)
    
    # 创建文件处理器
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # 添加处理器到日志器
    logger.addHandler(file_handler)
    return logger

# 创建全局日志对象
WAC_LOGGER = setup_logger()

@register(
    "astrbot_plugin_WealthAndContract",
    "HINS(原长安某)",
    "集签到、契约、经济与社交系统于一体的群聊插件",
    "1.0",
    "https://github.com/WUHINS/astrbot_plugin_WealthAndContract"
)
#endregion

#region ==================== 数据系统 ====================
class ContractSystem(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self._init_env()
        self.active_invitations = {}  # 存储活跃的约会邀请

    def _init_env(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        os.makedirs(os.path.dirname(PROP_DATA_FILE), exist_ok=True)
        os.makedirs(os.path.dirname(SOCIAL_DATA_FILE), exist_ok=True)  # 社交数据目录
        os.makedirs(os.path.dirname(TIME_DATA_FILE), exist_ok=True)  # 时间数据目录
        os.makedirs(PLUGIN_DIR, exist_ok=True)
        os.makedirs(IMAGE_DIR, exist_ok=True)
        
        # 清空图片目录
        self._clean_image_dir()
        
        # 初始化数据文件
        for file_path in [DATA_FILE, PROP_DATA_FILE, SOCIAL_DATA_FILE, TIME_DATA_FILE]:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump({}, f)
                    
        if not os.path.exists(FONT_PATH):
            raise FileNotFoundError(f"字体文件缺失: {FONT_PATH}")

    def _clean_image_dir(self):
        """清空图片目录"""
        if os.path.exists(IMAGE_DIR):
            for filename in os.listdir(IMAGE_DIR):
                file_path = os.path.join(IMAGE_DIR, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    WAC_LOGGER.error(f"删除图片失败: {file_path} - {str(e)}")

    def _log_operation(self, level: str, message: str):
        """记录操作日志"""
        WAC_LOGGER.log(getattr(logging, level.upper(), logging.INFO), message)

    def _load_data(self):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self._log_operation("error", f"加载主数据失败: {str(e)}")
            return {}

    def _save_data(self, data):
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
        except Exception as e:
            self._log_operation("error", f"保存主数据失败: {str(e)}")

    def _load_time_data(self):
        """加载时间数据"""
        try:
            with open(TIME_DATA_FILE, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self._log_operation("error", f"加载时间数据失败: {str(e)}")
            return {}

    def _save_time_data(self, data):
        """保存时间数据"""
        try:
            with open(TIME_DATA_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
        except Exception as e:
            self._log_operation("error", f"保存时间数据失败: {str(e)}")

    def _load_prop_data(self):
        """加载道具数据"""
        try:
            with open(PROP_DATA_FILE, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self._log_operation("error", f"加载道具数据失败: {str(e)}")
            return {}

    def _save_prop_data(self, data):
        """保存道具数据"""
        try:
            with open(PROP_DATA_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
        except Exception as e:
            self._log_operation("error", f"保存道具数据失败: {str(e)}")

    def _load_social_data(self) -> dict:
        """加载社交数据"""
        try:
            with open(SOCIAL_DATA_FILE, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self._log_operation("error", f"加载社交数据失败: {str(e)}")
            return {}
    
    def _save_social_data(self, data):
        """保存社交数据"""
        try:
            with open(SOCIAL_DATA_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
        except Exception as e:
            self._log_operation("error", f"保存社交数据失败: {str(e)}")
    
    def _get_user_time_data(self, group_id: str, user_id: str) -> dict:
        """获取用户时间数据"""
        time_data = self._load_time_data()
        group_time = time_data.setdefault(group_id, {})
        return group_time.setdefault(user_id, {
            "last_sign": None,
            "last_robbery": None,
            "last_work": None,
            "last_red_star_use": None,
            "last_market_invasion_use": None,
            "free_insurance_until": None
        })

    def _save_user_time_data(self, group_id: str, user_id: str, time_data: dict):
        """保存用户时间数据"""
        all_time_data = self._load_time_data()
        group_time = all_time_data.setdefault(group_id, {})
        group_time[user_id] = time_data
        self._save_time_data(all_time_data)

    def _get_user_data(self, group_id: str, user_id: str) -> dict:
        """获取用户主数据（不含时间数据）"""
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            self._log_operation("error", f"加载用户数据失败: {str(e)}")
            data = {}

        user_data = data.setdefault(group_id, {}).setdefault(user_id, {
            "coins": 0.0,
            "bank": 0.0,
            "contractors": [],
            "contracted_by": None,
            "consecutive": 0,
            "permanent_contractors": [],  # 永久绑定性奴
            "is_permanent": False         # 是否被永久绑定
        })
        
        # 加载牛牛插件数据
        niuniu_data_path = os.path.join('data', 'niuniu_lengths.yml')
        if os.path.exists(niuniu_data_path):
            try:
                with open(niuniu_data_path, 'r', encoding='utf-8') as f:
                    niuniu_data = yaml.safe_load(f) or {}
                niuniu_coins = niuniu_data.get(group_id, {}).get(user_id, {}).get('coins', 0.0)
                user_data['niuniu_coins'] = niuniu_coins
            except Exception as e:
                self._log_operation("error", f"加载牛牛数据失败: {str(e)}")
                user_data['niuniu_coins'] = 0.0
        else:
            user_data['niuniu_coins'] = 0.0
        
        return user_data

    def _get_user_props(self, group_id: str, user_id: str) -> dict:
        """获取用户道具"""
        prop_data = self._load_prop_data()
        group_props = prop_data.setdefault(group_id, {})
        return group_props.setdefault(user_id, {})

    def _update_user_props(self, group_id: str, user_id: str, props: dict):
        """更新用户道具"""
        prop_data = self._load_prop_data()
        prop_data.setdefault(group_id, {})[user_id] = props
        self._save_prop_data(prop_data)

    def _get_wealth_info(self, user_data: dict) -> tuple:
        total = user_data["coins"] + user_data.get("niuniu_coins", 0.0) + user_data["bank"]
        for min_coin, name, rate in reversed(WEALTH_LEVELS):
            if total >= min_coin:
                return (name, rate)
        return ("平民", 0.25)

    def _calculate_wealth(self, user_data: dict) -> float:
        level_name, _ = self._get_wealth_info(user_data)
        return WEALTH_BASE_VALUES.get(level_name, 100)

    def _get_group_social_data(self, group_id: str) -> dict:
        """获取群组的社交数据"""
        data = self._load_social_data()
        return data.setdefault(str(group_id), {})
    
    def _get_user_social_data(self, group_id: str, user_id: str) -> dict:
        """获取用户的社交数据"""
        group_data = self._get_group_social_data(group_id)
        user_id_str = str(user_id)
        
        if user_id_str not in group_data:
            group_data[user_id_str] = {
                "special_relations": {
                    "lover": None,
                    "brother": None,
                    "patron": None
                },
                "favorability": {},
                "daily_date_count": 0,
                "last_date_date": ""
            }
        
        return group_data[user_id_str]
    
    # 社交系统核心方法
    def _get_relation_level(self, favorability: int) -> str:
        """根据好感度获取关系等级"""
        if favorability <= 19:
            return "陌生人"
        elif favorability <= 49:
            return "熟人"
        elif favorability <= 89:
            return "朋友"
        elif favorability <= 99:
            return "挚友"
        elif favorability == 100:
            return "唯一的你"
        else:
            return "灵魂伴侣"
    
    def get_favorability(self, group_id: str, user_a_id: str, user_b_id: str) -> int:
        """获取用户A对用户B的好感度"""
        user_a_data = self._get_user_social_data(group_id, user_a_id)
        return user_a_data["favorability"].get(str(user_b_id), 0)
    
    def _update_favorability(self, group_id: str, user_a_id: str, user_b_id: str, change: int) -> int:
        """更新好感度"""
        user_a_data = self._get_user_social_data(group_id, user_a_id)
        current = user_a_data["favorability"].get(str(user_b_id), 0)
        new_value = max(0, current + change)
        user_a_data["favorability"][str(user_b_id)] = new_value
        
        # 保存数据
        social_data = self._load_social_data()
        social_data.setdefault(str(group_id), {})[str(user_a_id)] = user_a_data
        self._save_social_data(social_data)
        
        # 记录日志
        self._log_operation("info", 
            f"更新好感度: group={group_id}, from={user_a_id}, to={user_b_id}, "
            f"change={change}, new={new_value}"
        )
        
        return new_value
    
    def get_special_relation(self, group_id: str, user_id: str, target_id: str) -> Optional[str]:
        """获取两个用户之间的特殊关系"""
        user_data = self._get_user_social_data(group_id, user_id)
        for relation_type, related_id in user_data["special_relations"].items():
            if related_id == str(target_id):
                return RELATION_TYPE_NAMES.get(relation_type, relation_type)
        return None
#endregion

#region ==================== 契约系统 ====================
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        msg = event.message_str.strip()
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())

        if msg.startswith("购买"):
            target_id = self._parse_at_target(event)
            if not target_id:
                yield event.plain_result("❌ 请@要购买的对象")
                return
            async for result in self._handle_hire(event, group_id, user_id, target_id):
                yield result
            return

        elif msg.startswith("出售"):
            target_id = self._parse_at_target(event)
            if not target_id:
                yield event.plain_result("❌ 请@要出售的对象")
                return
            async for result in self._handle_sell(event, group_id, user_id, target_id):
                yield result
            return

    def _parse_at_target(self, event):
        for comp in event.message_obj.message:
            if isinstance(comp, At):
                return str(comp.qq)
        return None

    async def _handle_hire(self, event, group_id, employer_id, target_id):
        employer = self._get_user_data(group_id, employer_id)
        target_user = self._get_user_data(group_id, target_id)
        
        # 获取时间数据
        time_data = self._get_user_time_data(group_id, target_id)
        
        # 新增：检查目标是否有自由身保险
        insurance_until = time_data.get("free_insurance_until")
        if insurance_until:
            insurance_time = SHANGHAI_TZ.localize(datetime.fromisoformat(insurance_until))
            if insurance_time > datetime.now(SHANGHAI_TZ):
                target_name = await self._get_at_user_name(event, target_id)
                remaining = insurance_time - datetime.now(SHANGHAI_TZ)
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                yield event.plain_result(f"❌ {target_name} 有自由身保险，剩余 {hours}小时{minutes}分钟 内不可购买")
                return
        
        # 检查目标是否是用户自己
        if employer_id == target_id:
            yield event.plain_result("不能购买自己哦~")
            return

        # 检查目标是否是机器人本身
        if target_id == event.get_self_id():
            yield event.plain_result("妹妹是天，妹妹最大，妹妹不能买")
            return
            
        # 检查目标用户是否有主人
        if target_user["contracted_by"] is not None:
            target_name = await self._get_at_user_name(event, target_id)
            yield event.plain_result(f"❌ {target_name} 已有主人，无法购买")
            return

        # 检查目标用户是否是自己的主人
        if employer.get("contracted_by") == target_id:
            target_name = await self._get_at_user_name(event, target_id)
            yield event.plain_result(f"❌ 你不能购买自己的主人 {target_name}")
            return
    
        # 原有检查...
        if len(employer["contractors"]) >= 100:
            yield event.plain_result("❌ 已达最大购买数量（100人）")
            return
        
        cost = self._calculate_wealth(target_user)
        if employer["coins"] < cost:
            yield event.plain_result(f"❌ 需要支付目标身价：{cost}金币")
            return

        employer["coins"] -= cost
        employer["contractors"].append(target_id)
        target_user["contracted_by"] = employer_id
        
        # 保存数据
        try:
            # 保存主数据
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            group_data = data.setdefault(group_id, {})
            group_data[employer_id] = employer
            group_data[target_id] = target_user
            self._save_data(data)
            
            # 记录日志
            self._log_operation("info", 
                f"购买性奴: group={group_id}, employer={employer_id}, "
                f"target={target_id}, cost={cost}"
            )
        except Exception as e:
            self._log_operation("error", f"购买性奴保存数据失败: {str(e)}")
        
        target_name = await self._get_at_user_name(event, target_id)
        yield event.plain_result(f"✅ 成功购买 {target_name}，消耗{cost}金币")

    async def _handle_sell(self, event, group_id, employer_id, target_id):
        employer = self._get_user_data(group_id, employer_id)
        target_user = self._get_user_data(group_id, target_id)

        if target_id not in employer["contractors"]:
            yield event.plain_result("❌ 目标不在你的性奴列表中")
            return

        sell_price = self._calculate_wealth(target_user) * 0.2
        employer["coins"] += sell_price
        employer["contractors"].remove(target_id)
        target_user["contracted_by"] = None
        
        # 新增：检查是否为永久绑定
        permanent_contractors = employer.get("permanent_contractors", [])
        is_permanent = target_id in permanent_contractors
        
        # 如果出售永久绑定的性奴，解除绑定
        if is_permanent:
            permanent_contractors.remove(target_id)
            employer["permanent_contractors"] = permanent_contractors
            target_user["is_permanent"] = False
        
        # 保存数据
        try:
            # 保存主数据
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            group_data = data.setdefault(group_id, {})
            group_data[employer_id] = employer
            group_data[target_id] = target_user
            self._save_data(data)
            
            # 记录日志
            self._log_operation("info", 
                f"出售性奴: group={group_id}, employer={employer_id}, "
                f"target={target_id}, price={sell_price}, permanent={is_permanent}"
            )
        except Exception as e:
            self._log_operation("error", f"出售性奴保存数据失败: {str(e)}")
        
        # 在结果中添加提示
        target_name = await self._get_at_user_name(event, target_id)
        result = f"✅ 成功出售性奴，获得{sell_price:.1f}金币"
        if is_permanent:
            result += "\n⚠️ 注意: 已解除永久绑定关系"
        yield event.plain_result(result)

    async def _get_at_user_name(self, event, target_id: str) -> str:
        try:
            from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
            if isinstance(event, AiocqhttpMessageEvent):
                client = event.bot
                resp = await client.api.call_action(
                    'get_group_member_info',
                    group_id=event.message_obj.group_id,
                    user_id=int(target_id),
                    no_cache=True
                )
                return resp.get('card') or resp.get('nickname', f'用户{target_id[-4:]}')
                
            raw_msg = event.message_str
            if match := re.search(r'\$CQ:at,qq=(\d+)\$', raw_msg):
                return f'用户{match.group(1)[-4:]}'
            return f'用户{target_id[-4:]}'
        except Exception as e:
            self._log_operation("warning", f"获取用户名失败: {target_id} - {str(e)}")
            return "神秘用户"

    # 新增打劫命令
    @command("打劫")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def robbery(self, event: AstrMessageEvent):
        """打劫其他用户"""
        # 解析@的目标用户
        target_id = self._parse_at_target(event)
        if not target_id:
            yield event.plain_result("❌ 请@要打劫的对象")
            return
            
        group_id = str(event.message_obj.group_id)
        robber_id = str(event.get_sender_id())
        robber_data = self._get_user_data(group_id, robber_id)
        target_data = self._get_user_data(group_id, target_id)
        
        # 获取时间数据
        time_data = self._get_user_time_data(group_id, robber_id)
        
        # 检查打劫者金币是否足够
        if robber_data["coins"] < 100:
            yield event.plain_result("❌ 你连100金币都没有，还学人打劫？")
            return
            
        # 检查目标金币是否足够
        if target_data["coins"] < 100:
            target_name = await self._get_at_user_name(event, target_id)
            yield event.plain_result(f"❌ {target_name} 还是个穷光蛋，放过他吧")
            return
            
        # 检查冷却时间
        now = datetime.now(SHANGHAI_TZ)
        if time_data["last_robbery"]:
            last_robbery = SHANGHAI_TZ.localize(datetime.fromisoformat(time_data["last_robbery"]))
            if (now - last_robbery) < timedelta(minutes=60):
                remaining = 60 - int((now - last_robbery).total_seconds() / 60)
                yield event.plain_result(f"❌ 打劫太频繁了，请等待{remaining}分钟后再试")
                return
                
        # 检查是否是自己的性奴
        is_contractor = target_id in robber_data["contractors"]
        
        # 打劫金额随机1-100
        amount = random.randint(1, 100)
        
        # 25%失败率（除非是自己的性奴）
        success = True
        if not is_contractor and random.random() < 0.25:
            success = False
            
        robber_name = event.get_sender_name()
        target_name = await self._get_at_user_name(event, target_id)
        
        if success:
            # 打劫成功
            # 确保目标有足够的金币
            if target_data["coins"] < amount:
                amount = target_data["coins"]  # 有多少抢多少
                
            target_data["coins"] -= amount
            robber_data["coins"] += amount
            
            # 更新打劫时间
            time_data["last_robbery"] = now.replace(tzinfo=None).isoformat()
            
            # 保存数据
            try:
                # 保存主数据
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                group_data = data.setdefault(group_id, {})
                group_data[robber_id] = robber_data
                group_data[target_id] = target_data
                self._save_data(data)
                
                # 保存时间数据
                self._save_user_time_data(group_id, robber_id, time_data)
                
                # 记录日志
                self._log_operation("info", 
                    f"打劫成功: group={group_id}, robber={robber_id}, "
                    f"target={target_id}, amount={amount}"
                )
            except Exception as e:
                self._log_operation("error", f"打劫保存数据失败: {str(e)}")
                
            yield event.plain_result(f"✅ 打劫成功！{robber_name} 从 {target_name} 那里抢到了 {amount} 金币")
        else:
            # 打劫失败
            # 随机扣除1-100金币
            penalty = random.randint(1, 100)
            # 确保打劫者有足够的金币支付罚金
            if robber_data["coins"] < penalty:
                penalty = robber_data["coins"]  # 有多少扣多少
                
            robber_data["coins"] -= penalty
            
            # 更新打劫时间
            time_data["last_robbery"] = now.replace(tzinfo=None).isoformat()
            
            # 保存数据
            try:
                # 保存主数据
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                group_data = data.setdefault(group_id, {})
                group_data[robber_id] = robber_data
                self._save_data(data)
                
                # 保存时间数据
                self._save_user_time_data(group_id, robber_id, time_data)
                
                # 记录日志
                self._log_operation("info", 
                    f"打劫失败: group={group_id}, robber={robber_id}, "
                    f"target={target_id}, penalty={penalty}"
                )
            except Exception as e:
                self._log_operation("error", f"打劫保存数据失败: {str(e)}")
                
            yield event.plain_result(f"❌ 打劫失败！{robber_name} 被警察抓住，罚款 {penalty} 金币")

    @command("赎身")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def terminate_contract(self, event: AstrMessageEvent):
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        user_data = self._get_user_data(group_id, user_id)
    
        # 新增：检查是否为永久绑定
        if user_data.get("is_permanent", False):
            yield event.chain_result([Plain(text="❌ 您已被主人永久绑定，无法赎身")])
            return
    
        if not user_data["contracted_by"]:
            yield event.chain_result([Plain(text="❌ 您暂无契约在身")])
            return

        # 计算基础身价
        base_cost = self._calculate_wealth(user_data)
        # 赎身费用 = 1.5倍身价
        cost = base_cost * 1.5
    
        if user_data["coins"] < cost:
            yield event.chain_result([Plain(text=f"❌ 需要支付赎身费用：{cost:.1f}金币 (1.5倍身价)")])
            return

        employer_id = user_data["contracted_by"]
        employer = self._get_user_data(group_id, employer_id)
        if user_id in employer["contractors"]:
            employer["contractors"].remove(user_id)
    
        user_data["contracted_by"] = None
        user_data["coins"] -= cost
    
        # 保存数据
        try:
            # 保存主数据
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            group_data = data.setdefault(group_id, {})
            group_data[user_id] = user_data
            group_data[employer_id] = employer
            self._save_data(data)
            
            # 记录日志
            self._log_operation("info", 
                f"赎身: group={group_id}, user={user_id}, "
                f"employer={employer_id}, cost={cost}"
            )
        except Exception as e:
            self._log_operation("error", f"赎身保存数据失败: {str(e)}")
    
        # 显示基础身价和实际支付金额
        yield event.chain_result([Plain(
            text=f"✅ 赎身成功！\n"
                f"- 基础身价: {base_cost:.1f}金币\n"
                f"- 赎身费用: {cost:.1f}金币 (1.5倍)\n"
                f"- 剩余金币: {user_data['coins']:.1f}"
        )])
#endregion

#region ==================== 资产系统 ====================
    @command("转账")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def transfer(self, event: AstrMessageEvent):
        """转账给其他用户"""
        msg_parts = event.message_str.strip().split()
        if len(msg_parts) < 3:
            yield event.chain_result([Plain(text="❌ 格式错误，请使用：/转账 <金额> @对方")])
            return

        try:
            amount = float(msg_parts[1])
        except ValueError:
            yield event.chain_result([Plain(text="❌ 请输入有效的数字金额")])
            return

        if amount <= 0:
            yield event.chain_result([Plain(text="❌ 转账金额必须大于0")])
            return

        # 获取转账目标
        target_id = self._parse_at_target(event)
        if not target_id:
            yield event.chain_result([Plain(text="❌ 请@转账对象")])
            return

        group_id = str(event.message_obj.group_id)
        sender_id = str(event.get_sender_id())

        if sender_id == target_id:
            yield event.chain_result([Plain(text="❌ 不能转账给自己")])
            return

        # 获取双方数据
        sender_data = self._get_user_data(group_id, sender_id)
        receiver_data = self._get_user_data(group_id, target_id)

        # 添加转账手续费（10%）
        fee = amount * 0.10
        total_deduct = amount + fee

        # 检查发送方是否有足够资金（包括手续费）
        if sender_data["coins"] < total_deduct:
            yield event.chain_result([Plain(text=f"❌ 现金不足（含手续费），需要 {total_deduct:.1f}金币，当前现金: {sender_data['coins']:.1f}金币")])
            return

        # 执行转账（扣除金额+手续费）
        sender_data["coins"] -= total_deduct
        receiver_data["coins"] += amount

        # 保存数据
        try:
            # 保存主数据
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            group_data = data.setdefault(group_id, {})
            group_data[sender_id] = sender_data
            group_data[target_id] = receiver_data
            self._save_data(data)
            
            # 记录日志
            self._log_operation("info", 
                f"转账: group={group_id}, from={sender_id}, "
                f"to={target_id}, amount={amount}, fee={fee}"
            )
        except Exception as e:
            self._log_operation("error", f"转账保存数据失败: {str(e)}")
            yield event.chain_result([Plain(text="❌ 转账失败，数据保存异常")])
            return

        # 获取目标用户的名字
        target_name = await self._get_at_user_name(event, target_id)
        sender_name = event.get_sender_name()

        # 通知双方
        yield event.chain_result([Plain(
            text=f"✅ 转账成功！\n"
                 f"- {sender_name} → {target_name}\n"
                 f"- 金额: {amount:.1f}金币\n"
                 f"- 手续费: {fee:.1f}金币\n"
                 f"- 你的现金余额: {sender_data['coins']:.1f}金币"
        )])

    @command("签到买彩票")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def buy_lottery(self, event: AstrMessageEvent):
        """购买彩票"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        user_data = self._get_user_data(group_id, user_id)
    
        # 检查性奴数量是否超过限制
        if len(user_data["contractors"]) >= 3:
            yield event.chain_result([Plain(text="❌ 拥有3个或以上性奴的用户禁止购买彩票")])
            return
    
        # 计算总资产（现金+银行+牛牛金币）
        total_assets = user_data["coins"] + user_data["bank"] + user_data.get("niuniu_coins", 0.0)
    
        # 检查总资产是否超过限制
        if total_assets > MAX_ASSETS_FOR_LOTTERY:
            yield event.chain_result([Plain(text=f"❌ 总资产超过{MAX_ASSETS_FOR_LOTTERY}金币，禁止购买彩票")])
            return
    
        # 检查现金是否足够
        if user_data["coins"] < LOTTERY_PRICE:
            yield event.chain_result([Plain(text=f"❌ 现金不足，需要{LOTTERY_PRICE}金币购买彩票")])
            return
    
        # 扣除彩票费用
        user_data["coins"] -= LOTTERY_PRICE
    
        # 随机决定是否中奖
        if random.random() < LOTTERY_WIN_RATE:
            # 中奖，随机生成奖金金额
            prize = random.uniform(LOTTERY_MIN_PRIZE, LOTTERY_MAX_PRIZE)
            user_data["coins"] += prize
            result_msg = f"🎉 恭喜中奖！获得 {prize:.1f} 金币！"
        else:
            result_msg = "😢 很遗憾，没有中奖"
    
        # 保存数据
        try:
            # 保存主数据
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            group_data = data.setdefault(group_id, {})
            group_data[user_id] = user_data
            self._save_data(data)
            
            # 记录日志
            self._log_operation("info", 
                f"购买彩票: group={group_id}, user={user_id}, "
                f"prize={prize if '中奖' in result_msg else 0}"
            )
        except Exception as e:
            self._log_operation("error", f"彩票保存数据失败: {str(e)}")
    
        yield event.chain_result([Plain(text=f"✅ 购买彩票成功（花费{LOTTERY_PRICE}金币）\n{result_msg}")])

    @command("存款")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def deposit(self, event: AstrMessageEvent):
        msg_parts = event.message_str.strip().split()
        if len(msg_parts) < 2:
            yield event.chain_result([Plain(text="❌ 格式错误，请使用：/存款 <金额>")])
            return
        
        try:
            amount = float(msg_parts[1])
        except ValueError:
            yield event.chain_result([Plain(text="❌ 请输入有效的数字金额")])
            return

        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        user_data = self._get_user_data(group_id, user_id)
        
        if amount <= 0:
            yield event.chain_result([Plain(text="❌ 存款金额必须大于0")])
            return
        
        # 计算可用总额（本插件金币 + 牛牛插件金币）
        total_available = user_data["coins"] + user_data.get("niuniu_coins", 0.0)
        
        if amount > total_available:
            yield event.chain_result([Plain(text="❌ 可用金币不足")])
            return
        
        # 优先使用本插件的金币
        if user_data["coins"] >= amount:
            user_data["coins"] -= amount
        else:
            remaining = amount - user_data["coins"]
            user_data["coins"] = 0.0
            # 从牛牛插件的金币中扣除剩余部分
            niuniu_data_path = os.path.join('data', 'niuniu_lengths.yml')
            if os.path.exists(niuniu_data_path):
                try:
                    with open(niuniu_data_path, 'r', encoding='utf-8') as f:
                        niuniu_data = yaml.safe_load(f) or {}
                    # 确保群组和用户数据存在
                    if group_id not in niuniu_data:
                        niuniu_data[group_id] = {}
                    if user_id not in niuniu_data[group_id]:
                        niuniu_data[group_id][user_id] = {}
                    niuniu_data[group_id][user_id]['coins'] = niuniu_data[group_id][user_id].get('coins', 0.0) - remaining
                    with open(niuniu_data_path, 'w', encoding='utf-8') as f:
                        yaml.dump(niuniu_data, f, allow_unicode=True)
                except Exception as e:
                    self._log_operation("error", f"更新牛牛数据失败: {str(e)}")
                    yield event.chain_result([Plain(text="❌ 更新牛牛插件数据失败")])
                    return
        
        user_data["bank"] += amount
        
        # 保存数据
        try:
            # 保存主数据
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            group_data = data.setdefault(group_id, {})
            group_data[user_id] = user_data
            self._save_data(data)
            
            # 记录日志
            self._log_operation("info", 
                f"存款: group={group_id}, user={user_id}, "
                f"amount={amount}"
            )
        except Exception as e:
            self._log_operation("error", f"存款保存数据失败: {str(e)}")
        
        yield event.chain_result([Plain(text=f"✅ 成功存入 {amount:.1f} 金币")])

    @command("取款")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def withdraw(self, event: AstrMessageEvent):
        msg_parts = event.message_str.strip().split()
        if len(msg_parts) < 2:
            yield event.chain_result([Plain(text="❌ 格式错误，请使用：/取款 <金额>")])
            return
        
        try:
            amount = float(msg_parts[1])
        except ValueError:
            yield event.chain_result([Plain(text="❌ 请输入有效的数字金额")])
            return

        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        user_data = self._get_user_data(group_id, user_id)
        
        if amount <= 0:
            yield event.chain_result([Plain(text="❌ 取款金额必须大于0")])
            return
        
        if amount > user_data["bank"]:
            yield event.chain_result([Plain(text="❌ 银行存款不足")])
            return
        
        user_data["bank"] -= amount
        user_data["coins"] += amount
        
        # 保存数据
        try:
            # 保存主数据
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            group_data = data.setdefault(group_id, {})
            group_data[user_id] = user_data
            self._save_data(data)
            
            # 记录日志
            self._log_operation("info", 
                f"取款: group={group_id}, user={user_id}, "
                f"amount={amount}"
            )
        except Exception as e:
            self._log_operation("error", f"取款保存数据失败: {str(e)}")
        
        yield event.chain_result([Plain(text=f"✅ 成功取出 {amount:.1f} 金币")])

    @command("资产核查")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def asset_check(self, event: AstrMessageEvent):
        """查询指定用户的资产情况"""
        # 解析@的目标用户
        target_id = self._parse_at_target(event)
        if not target_id:
            yield event.plain_result("❌ 请@要查询的用户")
            return
    
        group_id = str(event.message_obj.group_id)
    
        # 获取目标用户数据
        target_data = self._get_user_data(group_id, target_id)
    
        # 获取牛牛插件金币
        niuniu_coins = target_data.get("niuniu_coins", 0.0)
    
        # 计算总资产
        total_assets = target_data["coins"] + target_data["bank"] + niuniu_coins
    
        # 获取财富等级信息
        wealth_level, wealth_rate = self._get_wealth_info({
            "coins": target_data["coins"],
            "bank": target_data["bank"],
            "niuniu_coins": niuniu_coins
        })
    
        # 获取目标用户名称
        target_name = await self._get_at_user_name(event, target_id)
    
        # 生成资产核查卡片
        card_path = await self._generate_asset_card(
            event=event,
            user_id=target_id,
            user_name=target_name,
            coins=target_data["coins"],
            bank=target_data["bank"],
            niuniu_coins=niuniu_coins,
            total_assets=total_assets,
            wealth_level=wealth_level,
            wealth_rate=wealth_rate
        )
        yield event.chain_result([Image.fromFileSystem(card_path)])

    async def _generate_asset_card(self, **data):
        """生成资产核查卡片"""
        # 背景图处理
        try:
            bg_response = requests.get(BG_API, timeout=10)
            bg = PILImage.open(BytesIO(bg_response.content)).resize((1080, 720))
        except Exception:
            bg = PILImage.new("RGB", (1080, 720), color="#F0F8FF")  # 浅蓝色背景

        def create_rounded_panel(size, color, radius=20):
            """创建圆角面板"""
            panel = PILImage.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(panel)
            draw.rounded_rectangle([(0, 0), (size[0]-1, size[1]-1)], radius=radius, fill=color)
            return panel

        canvas = PILImage.new("RGBA", bg.size)
        canvas.paste(bg, (0, 0))
        draw = ImageDraw.Draw(canvas)

        # 主标题
        title_font = ImageFont.truetype(FONT_PATH, 48)
        title = f"{data['user_name']}的资产核查"
        text_bbox = title_font.getbbox(title)
        title_width = text_bbox[2] - text_bbox[0]
        draw.text(
            ((1080 - title_width) // 2, 30), 
            title, 
            font=title_font, 
            fill="#4169E1",  # 皇家蓝
            stroke_width=2,
            stroke_fill="#FFFFFF"
        )

        # 用户信息
        user_font = ImageFont.truetype(FONT_PATH, 36)
        user_info = f"QQ: {data['user_id']}"
        draw.text(
            (100, 100), 
            user_info, 
            font=user_font, 
            fill="#000080"  # 深蓝色
        )
    
        # 财富等级信息
        wealth_font = ImageFont.truetype(FONT_PATH, 32)
        wealth_text = f"财富等级: {data['wealth_level']} (加成率: {data['wealth_rate']*100:.0f}%)"
        draw.text(
            (100, 150), 
            wealth_text, 
            font=wealth_font, 
            fill="#8B4513"  # 深棕色
        )

        # 头像处理
        avatar = await self._get_avatar(data["user_id"])
        if avatar:
            canvas.paste(avatar, (800, 100), avatar)

        # 资产面板
        asset_panel = create_rounded_panel((900, 450), (255, 255, 255, 200))  # 半透明白色
        canvas.paste(asset_panel, (90, 200), asset_panel)

        # 资产标题
        title_font = ImageFont.truetype(FONT_PATH, 36)
        draw.text((120, 220), "资产类型", font=title_font, fill="#8B0000")  # 深红色
        draw.text((550, 220), "金额", font=title_font, fill="#8B0000")
    
        # 绘制分隔线
        draw.line([(100, 260), (980, 260)], fill="#8B0000", width=2)
    
        # 资产项目
        asset_items = [
            ("💰 钱包现金", data["coins"]),
            ("🏦 银行存款", data["bank"]),
            ("🐮 牛牛金币", data["niuniu_coins"]),
            ("💎 总资产", data["total_assets"])
        ]
    
        # 显示资产项目
        entry_font = ImageFont.truetype(FONT_PATH, 32)
        y_position = 290
        for i, (name, amount) in enumerate(asset_items):
            # 交替行颜色
            bg_color = (220, 240, 255, 150) if i % 2 == 0 else (240, 255, 240, 150)
            item_panel = create_rounded_panel((860, 60), bg_color, radius=10)
            canvas.paste(item_panel, (110, y_position), item_panel)
        
            # 资产名称
            draw.text((130, y_position + 15), name, font=entry_font, fill="#00008B")  # 深蓝色
        
            # 资产金额（总资产特殊显示）
            if name == "💎 总资产":
                amount_color = "#FF4500"  # 橙红色
                amount_font = ImageFont.truetype(FONT_PATH, 36)
            else:
                amount_color = "#228B22"  # 森林绿
                amount_font = entry_font
        
            amount_text = f"{amount:.1f} 金币"
            text_bbox = amount_font.getbbox(amount_text)
            text_width = text_bbox[2] - text_bbox[0]
            draw.text(
                (860 - text_width + 110 - 20, y_position + 15), 
                amount_text, 
                font=amount_font, 
                fill=amount_color
            )
        
            y_position += 70
    
        # 财富等级描述
        level_desc = ""
        for min_coin, name, rate in WEALTH_LEVELS:
            if data["total_assets"] >= min_coin:
                level_desc = f"达到{name}等级需要资产 ≥ {min_coin}金币"
    
        draw.text(
            (120, y_position + 20), 
            level_desc, 
            font=entry_font, 
            fill="#8B4513"  # 深棕色
        )
    
        # 底部信息
        footer_font = ImageFont.truetype(FONT_PATH, 24)
        draw.text((100, 670), "查询个人资产: /签到查询", font=footer_font, fill="#666666")
        draw.text((400, 670), "金币排行榜: /金币排行榜", font=footer_font, fill="#666666")
        draw.text((700, 670), "性奴排行榜: /性奴排行榜", font=footer_font, fill="#666666")

        # 版权信息
        copyright_font = ImageFont.truetype(FONT_PATH, 20)
        copyright_text = "by HINS"
        text_bbox = copyright_font.getbbox(copyright_text)
        draw.text(
            (1080 - text_bbox[2] - 20, 720 - text_bbox[3] - 10),
            copyright_text,
            font=copyright_font,
            fill="#666666"
        )

        # 保存图片
        filename = f"asset_check_{data['user_id']}.png"
        save_path = os.path.join(IMAGE_DIR, filename)
        canvas.save(save_path)

        return save_path
#endregion

#region ==================== 帮助系统 ====================
    @command("签到帮助")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def show_help(self, event: AstrMessageEvent):
        """显示财富与契约插件帮助菜单"""
        help_text = """
📊 财富与契约插件使用帮助 📊

【核心功能】
/签到
- 每日签到获得金币奖励
- 连续签到有额外奖励
- 银行利息每日1%

/签到查询
- 查看当前签到状态
- 显示预计收益详情

【经济系统】
/存款 <金额>
- 将现金存入银行获得利息
- 示例: /存款 100

/取款 <金额>
- 从银行取出金币到现金
- 示例: /取款 50

/转账 <金额> @对方
- 转账给其他用户
- 收取10%手续费
- 示例: /转账 200 @用户

/签到买彩票
- 花费5金币购买彩票
- 2%中奖概率，奖金1500-7000金币
- 总资产超过500金币禁止购买
- 拥有3个或以上性奴禁止购买

/金币排行榜
- 显示本群金币总资产前10名用户

/性奴排行榜
- 显示本群拥有性奴数量前10名用户

【契约系统】
购买@用户
- 购买其他用户作为性奴
- 示例: 购买@用户

出售@用户
- 出售你拥有的性奴
- 示例: 出售@用户

/我的契约
- 查看当前契约关系（主人和性奴）

/看看你的契约@用户
- 查看指定用户的契约关系（主人和性奴）
- 示例: /看看你的契约@用户

/看看详细契约@用户
- 查看用户的详细契约信息（文本形式）
- 示例: /看看详细契约@用户
- 示例: /看看详细契约

/赎身
- 支付1.5倍身价解除契约关系

【打工系统】
/打工 工作名 @用户
- 让性奴打工赚钱
- 示例: /打工 卖银 @用户

/一键打工 工作名
- 让所有性奴同时进行指定工作
- 示例: /一键打工 送外卖

/打工列表
- 显示可用的工作列表

【打劫系统】
/打劫@用户
- 打劫其他用户的金币
- 25%失败率，失败会被罚款
- 打劫自己的性奴100%成功
- 60分钟冷却时间

【资产核查】
/资产核查@用户
- 查询用户的资产详情（现金、银行、牛牛金币）
- 显示财富等级信息

【道具系统】
/签到商店
- 查看可购买的道具列表

/签到背包
- 查看自己拥有的道具

/签到商店购买 <道具名> [数量]
- 购买道具

/道具驯服贴 @用户
- 永久绑定性奴（需拥有该性奴）

/道具强制购买 @用户
- 强制购买已有主人的性奴

/道具自由身保险
- 激活24小时自由身保护

/道具红星制裁
- 对全群高资产/多性奴用户进行制裁（每天限用1次）
- 效果：75%概率使目标损失10-50%资产并出逃1-5个非永久性奴
- 使用条件：自身资产≤2000且性奴≤5

/道具市场侵袭 @用户
- 对指定用户发起侵袭掠夺（每小时限用1次）
- 效果：60%胜率，获胜掠夺10-30%资产+1-3个非永久性奴
- 失败则损失15-35%资产并失去1-3个非永久性奴
- 使用条件：双方资产>2000或性奴>5

【社交系统】  # 新增社交系统
/约会@对方
- 向其他用户发起约会邀请
- 每日最多可发起3次约会

/同意约会
- 同意对方的约会邀请
- 约会过程中会触发随机事件影响双方好感度

/缔结关系@对方 关系类型
- 与对方缔结特殊关系（恋人、兄弟、包养）
- 需要双方好感度达到100点
- 需要特定道具：
  - 恋人：卡天亚戒指
  - 兄弟：一壶烈酒
  - 包养：黑金卡

/解除关系@对方
- 解除与对方的特殊关系
- 解除后双方好感度重置为50点

/查看关系@对方
- 查看你与对方的关系状态

/社交网络
- 查看你的社交关系网络（按好感度排序）

/赠送礼物@对方 礼物名
- 赠送礼物增加好感度
- 可用礼物：
  - 玫瑰花束：增加5-10点好感度
  - 定制蛋糕：增加8-15点好感度

【其他命令】
/签到帮助
- 显示此帮助菜单

/牛牛菜单
-牛牛插件帮助菜单
        """.strip()
    
        yield event.chain_result([Plain(text=help_text)])
#endregion

#region ==================== 排行榜系统 ====================
    @command("金币排行榜")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def wealth_leaderboard(self, event: AstrMessageEvent):
        """显示金币排行榜（总资产前10名）"""
        group_id = str(event.message_obj.group_id)
        
        # 加载数据
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            self._log_operation("error", f"加载排行榜数据失败: {str(e)}")
            data = {}
        
        group_data = data.get(group_id, {})
        
        # 加载牛牛插件数据
        niuniu_data = {}
        niuniu_data_path = os.path.join('data', 'niuniu_lengths.yml')
        if os.path.exists(niuniu_data_path):
            try:
                with open(niuniu_data_path, 'r', encoding='utf-8') as f:
                    niuniu_data = yaml.safe_load(f) or {}
            except Exception as e:
                self._log_operation("error", f"加载牛牛排行榜数据失败: {str(e)}")
                pass
        
        # 计算每个用户的总资产
        user_wealth = []
        for user_id, user_data in group_data.items():
            niuniu_coins = niuniu_data.get(group_id, {}).get(user_id, {}).get('coins', 0.0)
            total_wealth = user_data.get('coins', 0.0) + user_data.get('bank', 0.0) + niuniu_coins
            user_wealth.append((user_id, total_wealth))
        
        # 按总资产排序（降序）
        user_wealth.sort(key=lambda x: x[1], reverse=True)
        
        # 只取前10名
        top_users = user_wealth[:10]
        
        # 获取用户名
        leaderboard = []
        for rank, (user_id, wealth) in enumerate(top_users, start=1):
            try:
                user_name = await self._get_at_user_name(event, user_id)
            except:
                user_name = f"用户{user_id[-4:]}"
            leaderboard.append((rank, user_name, wealth))
        
        # 生成排行榜图片
        card_path = await self._generate_wealth_leaderboard(
            event=event,
            group_id=group_id,
            leaderboard=leaderboard
        )
        yield event.chain_result([Image.fromFileSystem(card_path)])

    async def _generate_wealth_leaderboard(self, **data):
        """生成金币排行榜卡片"""
        # 背景图处理
        try:
            bg_response = requests.get(BG_API, timeout=10)
            bg = PILImage.open(BytesIO(bg_response.content)).resize((1080, 720))
        except Exception:
            bg = PILImage.new("RGB", (1080, 720), color="#F0F8FF")  # 浅蓝色背景
        
        def create_rounded_panel(size, color, radius=20):
            """创建圆角面板"""
            panel = PILImage.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(panel)
            draw.rounded_rectangle([(0, 0), (size[0]-1, size[1]-1)], radius=radius, fill=color)
            return panel
        
        canvas = PILImage.new("RGBA", bg.size)
        canvas.paste(bg, (0, 0))
        draw = ImageDraw.Draw(canvas)
        
        # 主标题
        title_font = ImageFont.truetype(FONT_PATH, 48)
        title = "金币排行榜"
        text_bbox = title_font.getbbox(title)
        title_width = text_bbox[2] - text_bbox[0]
        draw.text(
            ((1080 - title_width) // 2, 30), 
            title, 
            font=title_font, 
            fill="#FFD700",  # 金色
            stroke_width=2,
            stroke_fill="#000000"
        )
        
        # 副标题
        subtitle_font = ImageFont.truetype(FONT_PATH, 32)
        subtitle = "总资产（现金+银行+牛牛金币）"
        text_bbox = subtitle_font.getbbox(subtitle)
        subtitle_width = text_bbox[2] - text_bbox[0]
        draw.text(
            ((1080 - subtitle_width) // 2, 90), 
            subtitle, 
            font=subtitle_font, 
            fill="#FFFFFF",
            stroke_width=1,
            stroke_fill="#000000"
        )
        
        # 排行榜面板
        list_panel = create_rounded_panel((900, 500), (255, 255, 255, 180))  # 半透明白色
        canvas.paste(list_panel, (90, 150), list_panel)
        
        # 表头
        header_font = ImageFont.truetype(FONT_PATH, 28)
        draw.text((120, 170), "排名", font=header_font, fill="#8B0000")  # 深红色
        draw.text((220, 170), "用户", font=header_font, fill="#8B0000")
        draw.text((700, 170), "总资产", font=header_font, fill="#8B0000")
        
        # 绘制分隔线
        draw.line([(100, 200), (980, 200)], fill="#8B0000", width=2)
        
        # 显示排行榜条目
        entry_font = ImageFont.truetype(FONT_PATH, 28)
        y_position = 220
        for rank, user_name, wealth in data['leaderboard']:
            # 排名颜色（前三名特殊颜色）
            if rank == 1:
                rank_color = "#FFD700"  # 金色
                wealth_color = "#FF4500"  # 橙红色
            elif rank == 2:
                rank_color = "#C0C0C0"  # 银色
                wealth_color = "#FF6347"  # 番茄红
            elif rank == 3:
                rank_color = "#CD7F32"  # 古铜色
                wealth_color = "#FF8C00"  # 深橙色
            else:
                rank_color = "#000000"  # 黑色
                wealth_color = "#228B22"  # 森林绿
            
            # 绘制条目
            draw.text((120, y_position), f"{rank}", font=entry_font, fill=rank_color)
            draw.text((220, y_position), user_name, font=entry_font, fill="#00008B")  # 深蓝色
            draw.text((700, y_position), f"{wealth:.1f} 金币", font=entry_font, fill=wealth_color)
            
            y_position += 45
        
        # 底部信息
        footer_font = ImageFont.truetype(FONT_PATH, 24)
        draw.text((100, 670), "查看个人资产: /签到查询", font=footer_font, fill="#666666")
        
        # 版权信息
        copyright_font = ImageFont.truetype(FONT_PATH, 20)
        copyright_text = "by HINS"
        text_bbox = copyright_font.getbbox(copyright_text)
        draw.text(
            (1080 - text_bbox[2] - 20, 720 - text_bbox[3] - 10),
            copyright_text,
            font=copyright_font,
            fill="#666666"
        )

        # 保存图片
        filename = f"wealth_leaderboard_{data['group_id']}.png"
        save_path = os.path.join(IMAGE_DIR, filename)
        canvas.save(save_path)
        
        return save_path

    @command("性奴排行榜")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def contractor_leaderboard(self, event: AstrMessageEvent):
        """显示性奴排行榜（拥有性奴数量前10名）"""
        group_id = str(event.message_obj.group_id)
        
        # 加载数据
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            self._log_operation("error", f"加载性奴排行榜数据失败: {str(e)}")
            data = {}
        
        group_data = data.get(group_id, {})
        
        # 计算每个用户的性奴数量
        user_contractors = []
        for user_id, user_data in group_data.items():
            contractor_count = len(user_data.get('contractors', []))
            user_contractors.append((user_id, contractor_count))
        
        # 按性奴数量排序（降序）
        user_contractors.sort(key=lambda x: x[1], reverse=True)
        
        # 只取前10名
        top_users = user_contractors[:10]
        
        # 获取用户名
        leaderboard = []
        for rank, (user_id, count) in enumerate(top_users, start=1):
            try:
                user_name = await self._get_at_user_name(event, user_id)
            except:
                user_name = f"用户{user_id[-4:]}"
            leaderboard.append((rank, user_name, count))
        
        # 生成排行榜图片
        card_path = await self._generate_contractor_leaderboard(
            event=event,
            group_id=group_id,
            leaderboard=leaderboard
        )
        yield event.chain_result([Image.fromFileSystem(card_path)])

    async def _generate_contractor_leaderboard(self, **data):
        """生成性奴排行榜卡片"""
        # 背景图处理
        try:
            bg_response = requests.get(BG_API, timeout=10)
            bg = PILImage.open(BytesIO(bg_response.content)).resize((1080, 720))
        except Exception:
            bg = PILImage.new("RGB", (1080, 720), color="#F0F8FF")  # 浅蓝色背景
        
        def create_rounded_panel(size, color, radius=20):
            """创建圆角面板"""
            panel = PILImage.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(panel)
            draw.rounded_rectangle([(0, 0), (size[0]-1, size[1]-1)], radius=radius, fill=color)
            return panel
        
        canvas = PILImage.new("RGBA", bg.size)
        canvas.paste(bg, (0, 0))
        draw = ImageDraw.Draw(canvas)
        
        # 主标题
        title_font = ImageFont.truetype(FONT_PATH, 48)
        title = "性奴排行榜"
        text_bbox = title_font.getbbox(title)
        title_width = text_bbox[2] - text_bbox[0]
        draw.text(
            ((1080 - title_width) // 2, 30), 
            title, 
            font=title_font, 
            fill="#FF69B4",  # 粉红色
            stroke_width=2,
            stroke_fill="#000000"
        )
        
        # 副标题
        subtitle_font = ImageFont.truetype(FONT_PATH, 32)
        subtitle = "拥有性奴数量"
        text_bbox = subtitle_font.getbbox(subtitle)
        subtitle_width = text_bbox[2] - text_bbox[0]
        draw.text(
            ((1080 - subtitle_width) // 2, 90), 
            subtitle, 
            font=subtitle_font, 
            fill="#FFFFFF",
            stroke_width=1,
            stroke_fill="#000000"
        )
        
        # 排行榜面板
        list_panel = create_rounded_panel((900, 500), (255, 255, 255, 180))  # 半透明白色
        canvas.paste(list_panel, (90, 150), list_panel)
        
        # 表头
        header_font = ImageFont.truetype(FONT_PATH, 28)
        draw.text((120, 170), "排名", font=header_font, fill="#8B0000")  # 深红色
        draw.text((220, 170), "用户", font=header_font, fill="#8B0000")
        draw.text((700, 170), "性奴数量", font=header_font, fill="#8B0000")
        
        # 绘制分隔线
        draw.line([(100, 200), (980, 200)], fill="#8B0000", width=2)
        
        # 显示排行榜条目
        entry_font = ImageFont.truetype(FONT_PATH, 28)
        y_position = 220
        for rank, user_name, count in data['leaderboard']:
            # 排名颜色（前三名特殊颜色）
            if rank == 1:
                rank_color = "#FFD700"  # 金色
                count_color = "#FF4500"  # 橙红色
            elif rank == 2:
                rank_color = "#C0C0C0"  # 银色
                count_color = "#FF6347"  # 番茄红
            elif rank == 3:
                rank_color = "#CD7F32"  # 古铜色
                count_color = "#FF8C00"  # 深橙色
            else:
                rank_color = "#000000"  # 黑色
                count_color = "#228B22"  # 森林绿
            
            # 绘制条目
            draw.text((120, y_position), f"{rank}", font=entry_font, fill=rank_color)
            draw.text((220, y_position), user_name, font=entry_font, fill="#00008B")  # 深蓝色
            draw.text((700, y_position), f"{count} 人", font=entry_font, fill=count_color)
            
            y_position += 45
        
        # 底部信息
        footer_font = ImageFont.truetype(FONT_PATH, 24)
        draw.text((100, 670), "管理契约: /我的契约", font=footer_font, fill="#666666")
        
        # 版权信息
        copyright_font = ImageFont.truetype(FONT_PATH, 20)
        copyright_text = "by HINS"
        text_bbox = copyright_font.getbbox(copyright_text)
        draw.text(
            (1080 - text_bbox[2] - 20, 720 - text_bbox[3] - 10),
            copyright_text,
            font=copyright_font,
            fill="#666666"
        )

        # 保存图片
        filename = f"contractor_leaderboard_{data['group_id']}.png"
        save_path = os.path.join(IMAGE_DIR, filename)
        canvas.save(save_path)
        
        return save_path
#endregion

#region ==================== 打工系统 ====================
    # 新增打工命令
    @command("打工")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def work_command(self, event: AstrMessageEvent):
        """让性奴打工赚钱"""
        # 解析消息：/打工 工作类型 @目标
        parts = event.message_str.strip().split()
        if len(parts) < 2:
            yield event.plain_result("❌ 格式错误，请使用：/打工 工作类型 @目标")
            return
        
        # 解析目标用户
        target_id = self._parse_at_target(event)
        if not target_id:
            yield event.plain_result("❌ 请@要打工的对象")
            return
        
        job_name = parts[1]
        if job_name not in JOBS:
            yield event.plain_result(f"❌ 未知工作类型，可用工作：{', '.join(JOBS.keys())}")
            return
        
        group_id = str(event.message_obj.group_id)
        employer_id = str(event.get_sender_id())
        
        # 获取用户数据
        employer_data = self._get_user_data(group_id, employer_id)
        target_data = self._get_user_data(group_id, target_id)
        
        # 获取时间数据
        time_data = self._get_user_time_data(group_id, target_id)
        
        # 检查是否是自己的性奴
        if target_id not in employer_data["contractors"]:
            target_name = await self._get_at_user_name(event, target_id)
            yield event.plain_result(f"❌ {target_name} 不是你的性奴，无法让其打工")
            return
        
        # 检查冷却时间（每小时只能打工一次）
        now = datetime.now(SHANGHAI_TZ)
        if time_data.get("last_work"):
            last_work = SHANGHAI_TZ.localize(datetime.fromisoformat(time_data["last_work"]))
            if (now - last_work) < timedelta(hours=1):
                remaining_minutes = 60 - int((now - last_work).total_seconds() / 60)
                target_name = await self._get_at_user_name(event, target_id)
                yield event.plain_result(f"❌ {target_name} 需要休息，请等待{remaining_minutes}分钟后再来打工")
                return
        
        # 获取工作信息
        job = JOBS[job_name]
        
        # 检查雇主是否有足够金币支付可能的最大惩罚（如果工作有失败惩罚）
        if job["risk_cost"][1] > 0:  # 有失败惩罚的工作
            max_risk = job["risk_cost"][1]
            if employer_data["coins"] < max_risk:
                yield event.plain_result(f"❌ 雇主金币不足，无法支付可能的最大惩罚（{max_risk}金币）")
                return
        
        # 执行打工
        is_success = random.random() < job["success_rate"]
        
        if is_success:
            # 打工成功
            min_reward, max_reward = job["reward"]
            reward = random.uniform(min_reward, max_reward)
            employer_data["coins"] += reward
            
            # 更新消息
            target_name = await self._get_at_user_name(event, target_id)
            msg = job["success_msg"].format(
                worker_name=target_name,
                reward=reward
            )
        else:
            # 打工失败
            min_risk, max_risk = job["risk_cost"]
            risk_cost = random.uniform(min_risk, max_risk)
            
            # 确保有足够的金币支付风险
            if employer_data["coins"] < risk_cost:
                # 如果余额不足，不允许打工
                yield event.plain_result(f"❌ 雇主金币不足，无法支付可能的惩罚（{risk_cost:.1f}金币）")
                return
            
            employer_data["coins"] -= risk_cost
            
            # 更新消息
            target_name = await self._get_at_user_name(event, target_id)
            msg = job["failure_msg"].format(
                worker_name=target_name,
                risk_cost=risk_cost
            )
        
        # 更新打工时间
        time_data["last_work"] = now.replace(tzinfo=None).isoformat()
        
        # 保存数据
        try:
            # 保存主数据
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            group_data = data.setdefault(group_id, {})
            group_data[employer_id] = employer_data
            group_data[target_id] = target_data
            self._save_data(data)
            
            # 保存时间数据
            self._save_user_time_data(group_id, target_id, time_data)
            
            # 记录日志
            self._log_operation("info", 
                f"打工: group={group_id}, employer={employer_id}, "
                f"worker={target_id}, job={job_name}, "
                f"success={is_success}, reward={reward if is_success else -risk_cost}"
            )
        except Exception as e:
            self._log_operation("error", f"打工保存数据失败: {str(e)}")
        
        yield event.plain_result(f"✅ {msg}")

    @command("打工列表")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def work_list_command(self, event: AstrMessageEvent):
        """显示可用的工作列表"""
        # 生成工作列表文本
        job_list = []
        for name, details in JOBS.items():
            min_reward, max_reward = details["reward"]
            success_rate = details["success_rate"] * 100
            
            if details["risk_cost"][0] > 0:
                min_risk, max_risk = details["risk_cost"]
                risk_info = f"失败惩罚: {min_risk}-{max_risk}金币"
            else:
                risk_info = "无失败惩罚"
            
            job_list.append(
                f"【{name}】\n"
                f"- 报酬: {min_reward}-{max_reward}金币\n"
                f"- 成功率: {success_rate:.1f}%\n"
                f"- {risk_info}"
            )
        
        response = "📋 可用工作列表：\n\n" + "\n\n".join(job_list)
        yield event.plain_result(response)

    @command("一键打工")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def batch_work_command(self, event: AstrMessageEvent):
        """让所有性奴同时进行指定的工作"""
        # 解析消息：/一键打工 工作名
        parts = event.message_str.strip().split()
        if len(parts) < 2:
            yield event.plain_result("❌ 格式错误，请使用：/一键打工 工作名")
            return
        
        job_name = parts[1]
        if job_name not in JOBS:
            yield event.plain_result(f"❌ 未知工作类型，可用工作：{', '.join(JOBS.keys())}")
            return
        
        group_id = str(event.message_obj.group_id)
        employer_id = str(event.get_sender_id())
        
        # 获取用户数据
        employer_data = self._get_user_data(group_id, employer_id)
        
        # 检查是否有性奴
        if not employer_data["contractors"]:
            yield event.plain_result("❌ 您还没有性奴，无法使用一键打工")
            return
        
        # 获取工作信息
        job = JOBS[job_name]
        
        # 检查雇主是否有足够金币支付可能的最大惩罚（如果工作有失败惩罚）
        max_risk = job["risk_cost"][1] if job["risk_cost"][1] > 0 else 0
        if max_risk > 0 and employer_data["coins"] < max_risk * len(employer_data["contractors"]):
            yield event.plain_result(f"❌ 雇主金币不足，无法支付所有性奴可能的最大惩罚（{max_risk * len(employer_data['contractors'])}金币）")
            return
        
        # 执行批量打工
        results = []
        total_reward = 0
        total_risk = 0
        now = datetime.now(SHANGHAI_TZ)
        
        for target_id in employer_data["contractors"]:
            target_data = self._get_user_data(group_id, target_id)
            time_data = self._get_user_time_data(group_id, target_id)
            
            # 检查冷却时间
            if time_data.get("last_work"):
                last_work = SHANGHAI_TZ.localize(datetime.fromisoformat(time_data["last_work"]))
                if (now - last_work) < timedelta(hours=1):
                    # 跳过冷却中的性奴
                    target_name = await self._get_at_user_name(event, target_id)
                    results.append(f"⏳ {target_name} 需要休息，跳过")
                    continue
            
            # 执行打工
            is_success = random.random() < job["success_rate"]
            
            if is_success:
                # 打工成功
                min_reward, max_reward = job["reward"]
                reward = random.uniform(min_reward, max_reward)
                total_reward += reward
                
                # 更新消息
                target_name = await self._get_at_user_name(event, target_id)
                results.append(job["success_msg"].format(
                    worker_name=target_name,
                    reward=reward
                ))
            else:
                # 打工失败
                min_risk, max_risk = job["risk_cost"]
                risk_cost = random.uniform(min_risk, max_risk)
                total_risk += risk_cost
                
                # 更新消息
                target_name = await self._get_at_user_name(event, target_id)
                results.append(job["failure_msg"].format(
                    worker_name=target_name,
                    risk_cost=risk_cost
                ))
            
            # 更新打工时间
            time_data["last_work"] = now.replace(tzinfo=None).isoformat()
            
            # 保存目标用户数据
            try:
                # 保存时间数据
                self._save_user_time_data(group_id, target_id, time_data)
            except Exception as e:
                self._log_operation("error", f"保存性奴时间数据失败: {str(e)}")
        
        # 更新雇主金币
        employer_data["coins"] += total_reward
        employer_data["coins"] -= total_risk
        
        # 保存雇主数据
        try:
            # 保存主数据
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            group_data = data.setdefault(group_id, {})
            group_data[employer_id] = employer_data
            self._save_data(data)
            
            # 记录日志
            self._log_operation("info", 
                f"一键打工: group={group_id}, employer={employer_id}, "
                f"job={job_name}, reward={total_reward}, risk={total_risk}"
            )
        except Exception as e:
            self._log_operation("error", f"一键打工保存数据失败: {str(e)}")
        
        # 构建响应消息
        response = f"📊 一键打工结果（{job_name}）\n\n"
        response += "\n".join(results)
        response += f"\n\n💰 总收入: {total_reward:.1f}金币"
        response += f"\n💸 总损失: {total_risk:.1f}金币"
        response += f"\n💼 净收益: {(total_reward - total_risk):.1f}金币"
        response += f"\n💳 当前现金: {employer_data['coins']:.1f}金币"
        
        yield event.plain_result(response)
#endregion

#region ==================== 契约查询系统 ====================
    @command("我的契约")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def my_contracts(self, event: AstrMessageEvent):
        """显示用户的契约关系（主人和性奴）"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        user_data = self._get_user_data(group_id, user_id)
    
        # 获取主人信息（如果有）
        master_info = None
        if user_data["contracted_by"]:
            master_id = user_data["contracted_by"]
            master_name = await self._get_at_user_name(event, master_id)
            master_info = (master_id, master_name)
    
        # 获取性奴列表（最多显示8个）
        contractors = []
        for cid in user_data["contractors"]:
            try:
                cname = await self._get_at_user_name(event, cid)
                contractors.append((cid, cname))
            except:
                contractors.append((cid, f"用户{cid[-4:]}"))
    
        # 生成契约关系卡片
        card_path = await self._generate_contract_card(
            event=event,
            user_id=user_id,
            user_name=event.get_sender_name(),
            master_info=master_info,
            contractors=contractors,
            group_id=group_id,
            is_permanent=user_data.get("is_permanent", False)  # 新增永久状态参数
        )
        yield event.chain_result([Image.fromFileSystem(card_path)])

    async def _generate_contract_card(self, **data):
        """生成契约关系卡片"""
        # 背景图处理
        try:
            bg_response = requests.get(BG_API, timeout=10)
            bg = PILImage.open(BytesIO(bg_response.content)).resize((1080, 720))
        except Exception:
            bg = PILImage.new("RGB", (1080, 720), color="#F0F8FF")  # 浅蓝色背景
    
        def create_rounded_panel(size, color, radius=20):
            """创建圆角面板"""
            panel = PILImage.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(panel)
            draw.rounded_rectangle([(0, 0), (size[0]-1, size[1]-1)], radius=radius, fill=color)
            return panel
    
        canvas = PILImage.new("RGBA", bg.size)
        canvas.paste(bg, (0, 0))
        draw = ImageDraw.Draw(canvas)
    
        # 主标题
        title_font = ImageFont.truetype(FONT_PATH, 48)
        title = "契约关系"
        text_bbox = title_font.getbbox(title)
        title_width = text_bbox[2] - text_bbox[0]
        draw.text(
            ((1080 - title_width) // 2, 30), 
            title, 
            font=title_font, 
            fill="#8B4513",  # 深棕色
            stroke_width=2,
            stroke_fill="#FFFFFF"
        )
    
        # 用户信息
        user_font = ImageFont.truetype(FONT_PATH, 36)
        user_info = f"{data['user_name']} ({data['user_id']})"
        draw.text(
            (100, 100), 
            user_info, 
            font=user_font, 
            fill="#000080"  # 深蓝色
        )
        
        # 新增：显示永久绑定状态
        status_font = ImageFont.truetype(FONT_PATH, 28)
        if data.get('is_permanent', False):
            status_text = "永久性奴"
            status_color = "#FF0000"  # 红色
        elif data['master_info']:
            status_text = "性奴"
            status_color = "#8B0000"  # 深红色
        else:
            status_text = "自由民"
            status_color = "#228B22"  # 森林绿
            
        draw.text((100, 140), f"状态: {status_text}", font=status_font, fill=status_color)
    
        # 主人信息面板
        master_panel = create_rounded_panel((900, 80), (255, 240, 245, 200))  # 浅粉色
        canvas.paste(master_panel, (90, 160), master_panel)
    
        master_font = ImageFont.truetype(FONT_PATH, 32)
        if data['master_info']:
            master_id, master_name = data['master_info']
            master_text = f"主人: {master_name} ({master_id})"
            draw.text((120, 180), "👑", font=master_font, fill="#FFD700")  # 金色皇冠
            draw.text((160, 180), master_text, font=master_font, fill="#8B0000")  # 深红色
        else:
            draw.text((120, 180), "自由之身，暂无主人", font=master_font, fill="#228B22")  # 森林绿
    
        # 性奴标题
        contractor_title = f"性奴列表 ({len(data['contractors'])}人)"
        draw.text((100, 260), contractor_title, font=user_font, fill="#800080")  # 紫色
    
        # 性奴列表面板
        list_panel = create_rounded_panel((900, 350), (240, 255, 240, 200))  # 浅绿色
        canvas.paste(list_panel, (90, 300), list_panel)
    
        # 显示性奴列表（最多8个）
        list_font = ImageFont.truetype(FONT_PATH, 28)
        y_position = 320
        for i, (cid, cname) in enumerate(data['contractors']):
            if i >= 8:  # 最多显示8个
                break
        
            # 交替行颜色
            bg_color = (220, 240, 255, 150) if i % 2 == 0 else (240, 255, 240, 150)
            item_panel = create_rounded_panel((860, 40), bg_color, radius=10)
            canvas.paste(item_panel, (110, y_position), item_panel)
        
            # 序号和用户信息
            draw.text((130, y_position + 8), f"{i+1}.", font=list_font, fill="#333333")
            draw.text((170, y_position + 8), f"{cname} ({cid})", font=list_font, fill="#00008B")  # 深蓝色
            
            # 检查是否为永久绑定
            is_permanent = False
            try:
                # 加载用户数据检查永久绑定
                user_data = self._get_user_data(data['group_id'], cid)
                is_permanent = user_data.get("is_permanent", False)
            except:
                pass
            
            # 添加永久绑定标记
            if is_permanent:
                draw.text((700, y_position + 8), "🔒永久", font=list_font, fill="#FF0000")  # 红色永久标记
        
            y_position += 45
    
        # 如果超过8个，显示更多提示
        if len(data['contractors']) > 8:
            more_text = f"...等{len(data['contractors'])-8}位未显示"
            draw.text((130, y_position + 10), more_text, font=list_font, fill="#666666")
    
        # 底部信息
        footer_font = ImageFont.truetype(FONT_PATH, 24)
        draw.text((100, 670), "购买性奴: 购买@用户", font=footer_font, fill="#666666")  # 橄榄绿
        draw.text((400, 670), "出售性奴: 出售@用户", font=footer_font, fill="#666666")
        draw.text((700, 670), "解除契约: /赎身", font=footer_font, fill="#666666")
    
        # 版权信息
        copyright_font = ImageFont.truetype(FONT_PATH, 20)
        copyright_text = "by HINS"
        text_bbox = copyright_font.getbbox(copyright_text)
        draw.text(
            (1080 - text_bbox[2] - 20, 720 - text_bbox[3] - 10),
            copyright_text,
            font=copyright_font,
            fill="#666666"
        )

        # 保存图片
        filename = f"contract_{data['user_id']}.png"
        save_path = os.path.join(IMAGE_DIR, filename)
        canvas.save(save_path)
    
        return save_path

    @command("看看你的契约")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def view_contract(self, event: AstrMessageEvent):
        """查看指定用户的契约关系"""
        # 解析@的目标用户
        target_id = self._parse_at_target(event)
        if not target_id:
            yield event.plain_result("❌ 请@要查看的用户")
            return
        
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        
        # 获取目标用户数据
        target_data = self._get_user_data(group_id, target_id)
        
        # 获取主人信息（如果有）
        master_info = None
        if target_data["contracted_by"]:
            master_id = target_data["contracted_by"]
            master_name = await self._get_at_user_name(event, master_id)
            master_info = (master_id, master_name)
    
        # 获取性奴列表
        contractors = []
        for cid in target_data["contractors"]:
            try:
                cname = await self._get_at_user_name(event, cid)
                contractors.append((cid, cname))
            except:
                contractors.append((cid, f"用户{cid[-4:]}"))
        
        # 获取目标用户名称
        target_name = await self._get_at_user_name(event, target_id)
        
        # 生成契约关系卡片
        card_path = await self._generate_contract_card(
            event=event,
            user_id=target_id,
            user_name=target_name,
            master_info=master_info,
            contractors=contractors,
            group_id=group_id,
            is_permanent=target_data.get("is_permanent", False)  # 新增永久状态参数
        )
        yield event.chain_result([Image.fromFileSystem(card_path)])

    @command("看看详细契约")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def detailed_contract(self, event: AstrMessageEvent):
        """显示用户及其契约关系的详细信息"""
        # 解析@的目标用户
        target_id = self._parse_at_target(event)
        group_id = str(event.message_obj.group_id)
    
        # 如果没有@用户，则使用发送者自己的ID
        if not target_id:
            target_id = str(event.get_sender_id())
    
        # 获取目标用户数据
        target_data = self._get_user_data(group_id, target_id)
    
        # 获取目标用户名称
        target_name = await self._get_at_user_name(event, target_id)
    
        # 获取主人信息（如果有）
        master_info = None
        if target_data["contracted_by"]:
            master_id = target_data["contracted_by"]
            try:
                master_name = await self._get_at_user_name(event, master_id)
                master_info = f"{master_name} ({master_id})"
            except:
                master_info = f"用户{master_id[-4:]}"
    
        # 获取性奴列表
        contractors = []
        for cid in target_data["contractors"]:
            try:
                cname = await self._get_at_user_name(event, cid)
                contractors.append(f"{cname} ({cid})")
            except:
                contractors.append(f"用户{cid[-4:]}")
    
        # 计算财富等级
        total_wealth = target_data["coins"] + target_data["bank"] + target_data.get("niuniu_coins", 0.0)
        wealth_level, wealth_rate = self._get_wealth_info({
            "coins": target_data["coins"],
            "bank": target_data["bank"],
            "niuniu_coins": target_data.get("niuniu_coins", 0.0)
        })
    
        # 构建响应消息
        response = f"📋 {target_name} 的详细契约信息：\n\n"
        response += f"- QQ: {target_id}\n"
        response += f"- 财富等级: {wealth_level} (加成率: {wealth_rate*100:.0f}%)\n"
        response += f"- 总资产: {total_wealth:.1f}金币\n"
        response += f"- 现金: {target_data['coins']:.1f}金币\n"
        response += f"- 银行存款: {target_data['bank']:.1f}金币\n"
        response += f"- 牛牛金币: {target_data.get('niuniu_coins', 0.0):.1f}金币\n\n"
    
        if master_info:
            response += f"👑 主人: {master_info}\n\n"
        else:
            response += "🎗️ 自由之身，暂无主人\n\n"
    
        if contractors:
            response += f"🧑 性奴列表 ({len(contractors)}人):\n"
            for i, contractor in enumerate(contractors, start=1):
                response += f"  {i}. {contractor}\n"
        else:
            response += "📭 暂无性奴"
    
        yield event.chain_result([Plain(text=response)])
#endregion

#region ==================== 签到系统 ====================
    @command("签到")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def sign_in(self, event: AstrMessageEvent):
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        user_data = self._get_user_data(group_id, user_id)
        time_data = self._get_user_time_data(group_id, user_id)
    
        now = datetime.now(SHANGHAI_TZ)
        today = now.date()
    
        if time_data["last_sign"]:
            last_sign = SHANGHAI_TZ.localize(datetime.fromisoformat(time_data["last_sign"]))
            if last_sign.date() == today:
                yield event.chain_result([Plain(text="❌ 今日已签到，请明天再来！")])
                return

        interest = user_data["bank"] * 0.01
        user_data["bank"] += interest

        if time_data["last_sign"]:
            last_sign = SHANGHAI_TZ.localize(datetime.fromisoformat(time_data["last_sign"]))
            delta = today - last_sign.date()
            user_data["consecutive"] = 1 if delta.days > 1 else user_data["consecutive"] + 1
        else:
            user_data["consecutive"] = 1

        # 获取用户自身身份的加成
        user_wealth_level, user_wealth_rate = self._get_wealth_info(user_data)
    
        # 计算契约收益加成
        contractor_rates = sum(
            self._get_wealth_info(self._get_user_data(group_id, c))[1]
            for c in user_data["contractors"]
        )
    
        # 计算连签奖励
        consecutive_bonus = 10 * (user_data["consecutive"] - 1)  
    
        # 计算签到收益
        earned = BASE_INCOME * (1 + user_wealth_rate) * (1 + contractor_rates) + consecutive_bonus

        user_data["coins"] += earned
        time_data["last_sign"] = now.replace(tzinfo=None).isoformat()
    
        # 保存数据
        try:
            # 保存主数据
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            group_data = data.setdefault(group_id, {})
            group_data[user_id] = user_data
            self._save_data(data)
            
            # 保存时间数据
            self._save_user_time_data(group_id, user_id, time_data)
            
            # 记录日志
            self._log_operation("info", 
                f"签到: group={group_id}, user={user_id}, "
                f"earned={earned}, consecutive={user_data['consecutive']}"
            )
        except Exception as e:
            self._log_operation("error", f"签到保存数据失败: {str(e)}")
    
        # 生成签到卡片（不再检查制裁）
        card_path = await self._generate_card(
            event=event,
            user_id=user_id,
            user_name=event.get_sender_name(),
            coins=user_data["coins"] + user_data.get("niuniu_coins", 0.0),  # 显示总额
            bank=user_data["bank"],
            consecutive=user_data["consecutive"],
            contractors=user_data["contractors"],
            is_contracted=bool(user_data["contracted_by"]),
            interest=interest,
            earned=earned,
            group_id=group_id,
            is_query=False
        )
        yield event.chain_result([Image.fromFileSystem(card_path)])

    @command("签到查询")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def sign_query(self, event: AstrMessageEvent):
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        user_data = self._get_user_data(group_id, user_id)
        
        # 获取用户自身身份的加成
        user_wealth_level, user_wealth_rate = self._get_wealth_info(user_data)
        
        # 计算契约收益加成
        contractor_rates = sum(
            self._get_wealth_info(self._get_user_data(group_id, c))[1]
            for c in user_data["contractors"]
        )
        
        # 计算连签奖励
        consecutive_bonus = 10 * user_data["consecutive"]
        
        # 计算预期收益
        earned = BASE_INCOME * (1 + user_wealth_rate) * (1 + contractor_rates) + consecutive_bonus

        card_path = await self._generate_card(
            event=event,
            user_id=user_id,
            user_name=event.get_sender_name(),
            coins=user_data["coins"] + user_data.get("niuniu_coins", 0.0),  # 显示总额
            bank=user_data["bank"],
            consecutive=user_data["consecutive"],
            contractors=user_data["contractors"],
            is_contracted=bool(user_data["contracted_by"]),
            interest=user_data["bank"] * 0.01,
            earned=earned,
            group_id=group_id,
            is_query=True,
            user_wealth_rate=user_wealth_rate
        )
        yield event.chain_result([Image.fromFileSystem(card_path)])

    async def _generate_card(self, **data):
        try:
            bg_response = requests.get(BG_API, timeout=10)
            bg = PILImage.open(BytesIO(bg_response.content)).resize((1080, 720))
        except Exception:
            bg = PILImage.new("RGB", (1080, 720), color="#FFFFFF")

        def create_rounded_panel(size, color):
            panel = PILImage.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(panel)
            draw.rounded_rectangle([(0, 0), (size[0]-1, size[1]-1)], radius=20, fill=color)
            return panel

        canvas = PILImage.new("RGBA", bg.size)
        canvas.paste(bg, (0, 0))
        draw = ImageDraw.Draw(canvas)
        avatar_y = 200
        info_start_y = 230
        # 头像处理
        avatar = await self._get_avatar(data["user_id"])
        if avatar:
            canvas.paste(avatar, (60, avatar_y), avatar)

        # 基础信息
        info_font = ImageFont.truetype(FONT_PATH, 28)
        name_font = ImageFont.truetype(FONT_PATH, 36)
        
        draw.text(
        (260, info_start_y), 
        f"QQ：{data['user_id']}", 
        font=info_font, 
        fill="#000000",
        stroke_width=1,      
        stroke_fill="#FFFFFF"
    )
        draw.text(
        (260, info_start_y + 40), 
        data["user_name"], 
        font=name_font, 
        fill="#FFA500",
        stroke_width=1,
        stroke_fill="#000000"
    )
        
        # 身份显示 - 添加永久性奴状态
        if data["is_contracted"]:
            # 获取用户数据检查永久绑定
            is_permanent = False
            try:
                user_data = self._get_user_data(data['group_id'], data['user_id'])
                is_permanent = user_data.get("is_permanent", False)
            except:
                pass
            
            status = "永久性奴" if is_permanent else "性奴"
        else:
            status = "自由民"
            
        wealth_level, _ = self._get_wealth_info({
            "coins": data["coins"], 
            "bank": data["bank"]
        })
        draw.text(
            (260, info_start_y + 80),
            f"身份：{status} | 等级：{wealth_level}", 
            font=info_font, 
            fill="#333333",
            stroke_width=1,       
            stroke_fill="#FFFFFF"  
        )

        # 左侧时间面板
        PANEL_WIDTH = 510
        PANEL_HEIGHT = 120
        SIDE_MARGIN = 20
        panel_y = 400

        left_panel = create_rounded_panel((PANEL_WIDTH, PANEL_HEIGHT), (255,255,255,150))
        canvas.paste(left_panel, (SIDE_MARGIN, panel_y), left_panel)
        
        time_font = ImageFont.truetype(FONT_PATH, 28)
        time_title = "查询时间" if data.get('is_query') else "签到时间"
        draw.text((SIDE_MARGIN+20, panel_y+20), time_title, font=time_font, fill="#333333")
        
        current_time = datetime.now(SHANGHAI_TZ).strftime("%Y-%m-%d %H:%M:%S")
        draw.text((SIDE_MARGIN+20, panel_y+60), current_time, font=time_font, fill="#333333")

        # 右侧收益面板
        right_panel_x = SIDE_MARGIN + PANEL_WIDTH + 20
        right_panel = create_rounded_panel((PANEL_WIDTH, PANEL_HEIGHT), (255,255,255,150))
        canvas.paste(right_panel, (right_panel_x, panel_y), right_panel)
        
        title_font = ImageFont.truetype(FONT_PATH, 32)
        title_text = "预计收入" if data.get('is_query') else "今日收益"
        draw.text((right_panel_x+20, panel_y+20), title_text, font=title_font, fill="#333333")

        detail_font = ImageFont.truetype(FONT_PATH, 24)
        line_height = 35
        
        if data.get('is_query'):
            # 计算加成后的基础收益
            base_with_bonus = BASE_INCOME * (1 + data['user_wealth_rate'])
            contract_bonus = sum(
                self._get_wealth_info(
                    self._get_user_data(data['group_id'], c)
                )[1] * base_with_bonus  # 使用加成后的基础收益计算契约加成
                for c in data['contractors']
            )
            consecutive_bonus = 10 * data['consecutive']  # 显示明日可得的连签奖励
            tomorrow_interest = data["bank"] * 0.01
            
            total = base_with_bonus + contract_bonus + consecutive_bonus + tomorrow_interest
            lines = [
                f"{total:.1f} 金币",
                f"基础{base_with_bonus:.1f}+契约{contract_bonus:.1f}+连签{consecutive_bonus:.1f}+利息{tomorrow_interest:.1f}"
            ]
        else:
            lines = [f"{data['earned']:.1f}（含利息{data['interest']:.1f}）"]
        start_y = panel_y + 50
        for i, line in enumerate(lines):
            text_bbox = detail_font.getbbox(line)
            text_width = text_bbox[2] - text_bbox[0]
            
            y_position = start_y + i*line_height
            if i == 0:
                draw.text(
                    (right_panel_x + PANEL_WIDTH//2 - text_width//2, y_position),
                    line,
                    font=ImageFont.truetype(FONT_PATH, 28),
                    fill="#FF4500"
                )
            else:
                draw.text(
                    (right_panel_x + PANEL_WIDTH//2 - text_width//2, y_position),
                    line,
                    font=detail_font,
                    fill="#333333"
                )

        # 底部数据面板 - 重点优化性奴信息显示
        BOTTOM_HEIGHT = 150
        BOTTOM_TOP = 720 - BOTTOM_HEIGHT - 20
        bottom_panel = create_rounded_panel((1040, BOTTOM_HEIGHT), (255,255,255,150))
        canvas.paste(bottom_panel, (20, BOTTOM_TOP), bottom_panel)

        # 获取性奴信息 - 优化显示方式
        contractors_count = len(data['contractors'])
        
        # 如果用户被契约，显示主人信息
        master_info = ""
        if data["is_contracted"]:
            try:
                master_id = data["user_data"]["contracted_by"]
                master_name = await self._get_at_user_name(data['event'], master_id)
                master_info = f"主人: {master_name}"
            except:
                master_info = "主人: 未知"
        else:
            master_info = "自由身"

        # 优化后的指标布局
        metrics = [
            ("现金", f"{data['coins']:.1f}", 60),
            ("银行", f"{data['bank']:.1f}", 300),
            ("性奴", f"{contractors_count}人", 560),
            ("连续签到", str(data['consecutive']), 820)
        ]
        
        # 绘制指标 - 使用统一的简洁方式
        for title, value, x in metrics:
            # 标题
            draw.text(
                (x, BOTTOM_TOP+30), 
                title, 
                font=ImageFont.truetype(FONT_PATH, 28), 
                fill="#333333"
            )
            
            # 值 - 统一绘制方式
            draw.text(
                (x, BOTTOM_TOP+80), 
                value, 
                font=ImageFont.truetype(FONT_PATH, 28), 
                fill="#000000"
            )
        copyright_font = ImageFont.truetype(FONT_PATH, 24)
        copyright_text = "by HINS"
        text_bbox = copyright_font.getbbox(copyright_text)
        draw.text(
            (1080 - text_bbox[2] - 20, 720 - text_bbox[3] - 20),
            copyright_text,
            font=copyright_font,
            fill="#666666"
        )

        # 保存图片
        filename = f"sign_{data['user_id']}.png"
        save_path = os.path.join(IMAGE_DIR, filename)
        canvas.save(save_path)
        
        return save_path

    async def _get_avatar(self, user_id: str):
        try:
            response = requests.get(AVATAR_API.format(user_id), timeout=5)
            img = PILImage.open(BytesIO(response.content))
            
            mask = PILImage.new('L', (160, 160), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 160, 160), fill=255)
            
            bordered = PILImage.new("RGBA", (166, 166), (255,255,255,0))
            bordered.paste(img.resize((160,160)), (3,3), mask)
            return bordered
        except Exception as e:
            self._log_operation("warning", f"获取头像失败: {user_id} - {str(e)}")
            return None
#endregion

#region ==================== 道具系统 ====================
    @command("签到商店")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def shop(self, event: AstrMessageEvent):
        """显示签到商店"""
        shop_text = "🛒 签到商店 🛒\n\n"
        for item, details in SHOP_ITEMS.items():
            shop_text += f"【{item}】\n"
            shop_text += f"- 价格: {details['price']}金币\n"
            shop_text += f"- 描述: {details['description']}\n"
            shop_text += f"- 购买命令: /签到商店购买 {item} [数量]\n\n"
        
        shop_text += "📦 查看背包: /签到背包"
        yield event.chain_result([Plain(text=shop_text)])

    @command("签到商店购买")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def buy_item(self, event: AstrMessageEvent):
        """购买商店道具"""
        parts = event.message_str.strip().split()
        if len(parts) < 2:
            yield event.chain_result([Plain(text="❌ 格式错误，请使用: /签到商店购买 道具名 [数量]")])
            return
        
        item_name = parts[1]
        quantity = 1
        if len(parts) >= 3:
            try:
                quantity = int(parts[2])
                if quantity <= 0:
                    yield event.chain_result([Plain(text="❌ 购买数量必须大于0")])
                    return
            except ValueError:
                yield event.chain_result([Plain(text="❌ 无效的数量")])
                return
        
        if item_name not in SHOP_ITEMS:
            yield event.chain_result([Plain(text=f"❌ 未知道具: {item_name}")])
            return
        
        item_info = SHOP_ITEMS[item_name]
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        user_data = self._get_user_data(group_id, user_id)
        total_cost = item_info["price"] * quantity
        
        # 检查金币是否足够
        if user_data["coins"] < total_cost:
            yield event.chain_result([Plain(
                text=f"❌ 金币不足! 需要 {total_cost} 金币, 当前金币: {user_data['coins']:.1f}"
            )])
            return
        
        # 检查特殊限制 (如驯服贴最多3个)
        if item_name == "驯服贴":
            # 检查永久绑定数量限制
            permanent_count = len(user_data.get("permanent_contractors", []))
            if permanent_count >= SHOP_ITEMS["驯服贴"]["max_per_user"]:
                yield event.chain_result([Plain(
                    text=f"❌ 已达最大永久绑定数量 ({SHOP_ITEMS['驯服贴']['max_per_user']}个)"
                )])
                return
        
        # 扣除金币
        user_data["coins"] -= total_cost
        
        # 更新道具数量
        user_props = self._get_user_props(group_id, user_id)
        current_count = user_props.get(item_name, 0)
        user_props[item_name] = current_count + quantity
        self._update_user_props(group_id, user_id, user_props)
        
        # 保存金币数据
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            group_data = data.setdefault(group_id, {})
            group_data[user_id] = user_data
            self._save_data(data)
            
            # 记录日志
            self._log_operation("info", 
                f"购买道具: group={group_id}, user={user_id}, "
                f"item={item_name}, quantity={quantity}, cost={total_cost}"
            )
        except Exception as e:
            self._log_operation("error", f"购买道具保存数据失败: {str(e)}")
            return
        
        yield event.chain_result([Plain(
            text=f"✅ 购买成功! 获得 {quantity} 个 {item_name}\n"
                 f"- 花费: {total_cost} 金币\n"
                 f"- 当前拥有: {user_props[item_name]} 个\n"
                 f"- 使用命令: /道具{item_info['command']} [@目标]"
        )])

    @command("签到背包")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def backpack(self, event: AstrMessageEvent):
        """查看用户背包"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        user_props = self._get_user_props(group_id, user_id)
        
        if not user_props:
            yield event.chain_result([Plain(text="🎒 您的背包空空如也")])
            return
        
        prop_text = "🎒 背包物品:\n\n"
        for item, quantity in user_props.items():
            if item in SHOP_ITEMS:
                prop_text += f"- {item}: {quantity} 个\n"
                prop_text += f"  使用命令: /道具{SHOP_ITEMS[item]['command']} [@目标]\n"
        
        yield event.chain_result([Plain(text=prop_text)])

    # 道具使用命令
    @command("道具驯服贴")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def use_tame_sticker(self, event: AstrMessageEvent):
        """使用驯服贴永久绑定性奴"""
        # 解析@的目标用户
        target_id = self._parse_at_target(event)
        if not target_id:
            yield event.plain_result("❌ 请@要绑定的对象")
            return
            
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        
        # 获取用户道具
        user_props = self._get_user_props(group_id, user_id)
        if "驯服贴" not in user_props or user_props["驯服贴"] < 1:
            yield event.plain_result("❌ 您没有驯服贴")
            return
        
        # 获取用户数据
        user_data = self._get_user_data(group_id, user_id)
        target_data = self._get_user_data(group_id, target_id)
        
        # 检查目标是否已经是自己的性奴
        if target_id not in user_data["contractors"]:
            target_name = await self._get_at_user_name(event, target_id)
            yield event.plain_result(f"❌ {target_name} 不是你的性奴")
            return
        
        # 检查永久绑定数量限制
        permanent_contractors = user_data.get("permanent_contractors", [])
        if len(permanent_contractors) >= SHOP_ITEMS["驯服贴"]["max_per_user"]:
            yield event.plain_result(f"❌ 已达最大永久绑定数量 ({SHOP_ITEMS['驯服贴']['max_per_user']}个)")
            return
        
        # 检查目标是否已被永久绑定
        if target_id in permanent_contractors:
            target_name = await self._get_at_user_name(event, target_id)
            yield event.plain_result(f"❌ {target_name} 已被永久绑定")
            return
        
        # 添加永久绑定
        permanent_contractors.append(target_id)
        user_data["permanent_contractors"] = permanent_contractors
        
        # 标记目标已被永久绑定
        target_data["is_permanent"] = True
        
        # 扣除道具
        user_props["驯服贴"] -= 1
        if user_props["驯服贴"] <= 0:
            del user_props["驯服贴"]
        
        # 保存数据
        try:
            # 保存道具数据
            self._update_user_props(group_id, user_id, user_props)
            
            # 保存用户数据
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            group_data = data.setdefault(group_id, {})
            group_data[user_id] = user_data
            group_data[target_id] = target_data
            self._save_data(data)
            
            # 记录日志
            self._log_operation("info", 
                f"使用驯服贴: group={group_id}, user={user_id}, "
                f"target={target_id}"
            )
        except Exception as e:
            self._log_operation("error", f"驯服贴保存数据失败: {str(e)}")
        
        target_name = await self._get_at_user_name(event, target_id)
        yield event.plain_result(f"✅ 成功永久绑定 {target_name}！\n"
                                 f"- 该性奴不会被制裁、赎身或强制购买\n"
                                 f"- 剩余驯服贴: {user_props.get('驯服贴', 0)}")

    @command("道具强制购买")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def use_force_buy(self, event: AstrMessageEvent):
        """使用强制购买符购买已有主人的性奴"""
        # 解析@的目标用户
        target_id = self._parse_at_target(event)
        if not target_id:
            yield event.plain_result("❌ 请@要购买的对象")
            return
            
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        
        # 获取用户道具
        user_props = self._get_user_props(group_id, user_id)
        if "强制购买符" not in user_props or user_props["强制购买符"] < 1:
            yield event.plain_result("❌ 您没有强制购买符")
            return
        
        # 获取用户数据
        employer_data = self._get_user_data(group_id, user_id)
        target_data = self._get_user_data(group_id, target_id)
        
        # 检查目标是否已被永久绑定
        if target_data.get("is_permanent", False):
            target_name = await self._get_at_user_name(event, target_id)
            yield event.plain_result(f"❌ {target_name} 已被永久绑定，无法强制购买")
            return
        
        # 检查目标是否有主人
        if not target_data["contracted_by"]:
            target_name = await self._get_at_user_name(event, target_id)
            yield event.plain_result(f"❌ {target_name} 没有主人，请直接购买")
            return
        
        # 计算目标身价
        cost = self._calculate_wealth(target_data)
        
        # 检查金币是否足够
        if employer_data["coins"] < cost:
            yield event.plain_result(f"❌ 需要支付目标身价：{cost}金币")
            return
        
        # 获取原主人数据
        original_owner_id = target_data["contracted_by"]
        original_owner_data = self._get_user_data(group_id, original_owner_id)
        
        # 更新契约关系
        # 从原主人移除
        if target_id in original_owner_data["contractors"]:
            original_owner_data["contractors"].remove(target_id)
        
        # 添加到新主人
        employer_data["contractors"].append(target_id)
        target_data["contracted_by"] = user_id
        
        # 处理金币
        employer_data["coins"] -= cost  # 新主人支付身价
        original_owner_data["coins"] += cost  # 原主人获得补偿
        
        # 扣除道具
        user_props["强制购买符"] -= 1
        if user_props["强制购买符"] <= 0:
            del user_props["强制购买符"]
        
        # 保存数据
        try:
            # 保存道具数据
            self._update_user_props(group_id, user_id, user_props)
            
            # 保存用户数据
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            group_data = data.setdefault(group_id, {})
            group_data[user_id] = employer_data
            group_data[target_id] = target_data
            group_data[original_owner_id] = original_owner_data
            self._save_data(data)
            
            # 记录日志
            self._log_operation("info", 
                f"强制购买: group={group_id}, buyer={user_id}, "
                f"target={target_id}, original_owner={original_owner_id}, "
                f"cost={cost}"
            )
        except Exception as e:
            self._log_operation("error", f"强制购买保存数据失败: {str(e)}")
        
        target_name = await self._get_at_user_name(event, target_id)
        new_owner_name = event.get_sender_name()
        original_owner_name = await self._get_at_user_name(event, original_owner_id)
        
        yield event.plain_result(f"⚡ 强制购买成功! {new_owner_name} 从 {original_owner_name} 处抢走了 {target_name}\n"
                                 f"- 支付身价: {cost}金币\n"
                                 f"- 剩余强制购买符: {user_props.get('强制购买符', 0)}")

    @command("道具自由身保险")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def use_freedom_insurance(self, event: AstrMessageEvent):
        """使用自由身保险"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        
        # 获取用户道具
        user_props = self._get_user_props(group_id, user_id)
        if "自由身保险" not in user_props or user_props["自由身保险"] < 1:
            yield event.plain_result("❌ 您没有自由身保险")
            return
        
        # 获取用户数据
        user_data = self._get_user_data(group_id, user_id)
        time_data = self._get_user_time_data(group_id, user_id)
        
        # 新增：检查用户是否是性奴（有主人）
        if user_data["contracted_by"] is not None:
            yield event.plain_result("❌ 您已是性奴，不能使用自由身保险")
            return
        
        # 检查是否已有保险
        insurance_until = time_data.get("free_insurance_until")
        if insurance_until:
            insurance_time = SHANGHAI_TZ.localize(datetime.fromisoformat(insurance_until))
            if insurance_time > datetime.now(SHANGHAI_TZ):
                remaining = insurance_time - datetime.now(SHANGHAI_TZ)
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                yield event.plain_result(f"❌ 您已有自由身保险，剩余时间: {hours}小时{minutes}分钟")
                return
        
        # 设置保险到期时间
        duration = SHOP_ITEMS["自由身保险"]["duration_hours"]
        expire_time = datetime.now(SHANGHAI_TZ) + timedelta(hours=duration)
        time_data["free_insurance_until"] = expire_time.replace(tzinfo=None).isoformat()
        
        # 扣除道具
        user_props["自由身保险"] -= 1
        if user_props["自由身保险"] <= 0:
            del user_props["自由身保险"]
        
        # 保存数据
        try:
            # 保存道具数据
            self._update_user_props(group_id, user_id, user_props)
            
            # 保存时间数据
            self._save_user_time_data(group_id, user_id, time_data)
            
            # 记录日志
            self._log_operation("info", 
                f"使用自由身保险: group={group_id}, user={user_id}, "
                f"expire={expire_time}"
            )
        except Exception as e:
            self._log_operation("error", f"自由身保险保存数据失败: {str(e)}")
        
        expire_str = expire_time.strftime("%Y-%m-%d %H:%M")
        yield event.plain_result(f"🛡️ 自由身保险已激活! 有效期至: {expire_str}\n"
                                 f"- 在此期间您不会被购买为性奴\n"
                                 f"- 剩余自由身保险: {user_props.get('自由身保险', 0)}")
    
    @command("道具红星制裁")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def use_red_star_sanction(self, event: AstrMessageEvent):
        """使用红星制裁道具"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())

        # 获取用户道具
        user_props = self._get_user_props(group_id, user_id)
        if "红星制裁" not in user_props or user_props["红星制裁"] < 1:
            yield event.plain_result("❌ 您没有红星制裁道具")
            return

        # 获取用户数据和时间数据
        user_data = self._get_user_data(group_id, user_id)
        time_data = self._get_user_time_data(group_id, user_id)
        
        # 检查使用者是否符合条件（不满足制裁条件）
        total_assets = user_data["coins"] + user_data["bank"] + user_data.get("niuniu_coins", 0.0)
        contractor_count = len(user_data["contractors"])

        # 检查使用者是否满足制裁条件
        if total_assets > 2000 or contractor_count > 5:
            yield event.plain_result("❌ 您自身已满足制裁条件，无法使用红星制裁")
            return

        # 检查冷却时间（每天限用一次）
        now = datetime.now(SHANGHAI_TZ)
        last_use_key = "last_red_star_use"
        if time_data.get(last_use_key):
            last_use = SHANGHAI_TZ.localize(datetime.fromisoformat(time_data[last_use_key]))
            if last_use.date() == now.date():
                yield event.plain_result("❌ 今天已使用过红星制裁，请明天再来")
                return

        # 加载全群数据
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            self._log_operation("error", f"加载红星制裁数据失败: {str(e)}")
            data = {}

        group_data = data.get(group_id, {})
        if not group_data:
            yield event.plain_result("❌ 群组数据为空")
            return

        # 对每个满足条件的用户进行制裁
        sanction_results = []
        for uid, u_data in group_data.items():
            # 跳过使用者自己
            if uid == user_id:
                continue
    
            # 计算用户总资产和性奴数量
            u_total_assets = u_data["coins"] + u_data["bank"] + u_data.get("niuniu_coins", 0.0)
            u_contractor_count = len(u_data["contractors"])

            # 检查是否满足制裁条件
            if u_total_assets > 2000 or u_contractor_count > 5:
                # 75%概率触发制裁
                if random.random() < 0.75:
                    # 性奴制裁（非永久绑定的）
                    escape_results = []
                    escaped_slaves = []  # 存储逃走的性奴信息
                    if u_contractor_count > 0:
                        # 只处理非永久绑定的性奴
                        non_permanent = []
                        for cid in u_data["contractors"]:
                            slave_data = self._get_user_data(group_id, cid)
                            if not slave_data.get("is_permanent", False):
                                non_permanent.append(cid)
            
                        if non_permanent:
                            # 随机选择1-5个非永久性奴出逃
                            num_escape = random.randint(1, min(5, len(non_permanent)))
                            escaped_ids = random.sample(non_permanent, num_escape)
                
                            # 更新用户数据
                            for cid in escaped_ids:
                                if cid in u_data["contractors"]:
                                    u_data["contractors"].remove(cid)
                        
                            # 更新性奴数据 - 确保contracted_by被清除
                            for cid in escaped_ids:
                                slave_data = self._get_user_data(group_id, cid)
                                slave_data["contracted_by"] = None  # 关键修复：解除契约关系
                                # 保存性奴数据
                                group_data[cid] = slave_data
                
                            # 获取逃走的性奴名字
                            for cid in escaped_ids:
                                try:
                                    slave_name = await self._get_at_user_name(event, cid)
                                    escaped_slaves.append(slave_name)
                                except:
                                    escaped_slaves.append(f"用户{cid[-4:]}")
            
                    # 资产制裁
                    asset_results = []
                    if u_total_assets > 0:
                        # 随机损失10%-50%的总资产
                        loss_percent = random.uniform(0.1, 0.5)
                        loss_amount = u_total_assets * loss_percent
            
                        # 从现金中扣除，不够则从银行扣
                        if u_data["coins"] >= loss_amount:
                            u_data["coins"] -= loss_amount
                        else:
                            remaining = loss_amount - u_data["coins"]
                            u_data["coins"] = 0
                            u_data["bank"] = max(0, u_data["bank"] - remaining)
            
                    asset_results.append(f"资产损失: {loss_amount:.1f}金币({loss_percent*100:.0f}%)")
        
                    # 记录制裁结果 - 详细显示性奴丢失信息
                    try:
                        user_name = await self._get_at_user_name(event, uid)
                        sanction_entry = f"👉 群友 {user_name} 被制裁:"
                
                        # 如果有性奴逃跑，详细显示
                        if escaped_slaves:
                            sanction_entry += f"\n  - 丢失性奴 {len(escaped_slaves)} 名: {', '.join(escaped_slaves)}"
                
                        # 如果有资产损失
                        if asset_results:
                            sanction_entry += f"\n  - {asset_results[0]}"
                
                        sanction_results.append(sanction_entry)
                    except:
                        sanction_entry = f"👉 用户{uid[-4:]} 被制裁:"
                        if escaped_slaves:
                            sanction_entry += f"\n  - 丢失性奴 {len(escaped_slaves)} 名"
                        if asset_results:
                            sanction_entry += f"\n  - {asset_results[0]}"
                        sanction_results.append(sanction_entry)

        # 如果没有触发任何制裁
        if not sanction_results:
            sanction_results.append("本次制裁未影响任何用户")

        # 更新使用者数据
        time_data[last_use_key] = now.replace(tzinfo=None).isoformat()

        # 扣除道具
        user_props["红星制裁"] -= 1
        if user_props["红星制裁"] <= 0:
            del user_props["红星制裁"]

        # 保存数据
        try:
            # 保存道具数据
            self._update_user_props(group_id, user_id, user_props)

            # 保存用户数据
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
                
            # 保存时间数据
            self._save_user_time_data(group_id, user_id, time_data)
            
            # 记录日志
            self._log_operation("info", 
                f"使用红星制裁: group={group_id}, user={user_id}, "
                f"results={len(sanction_results)-1}"  # 减去未影响任何用户的条目
            )
        except Exception as e:
            self._log_operation("error", f"红星制裁保存数据失败: {str(e)}")

        # 构建响应消息
        response = "✨ 来自共和国的力量降临了。。。\n"
        response += f"📢 对全群进行了红星制裁！\n\n"
        response += "\n".join(sanction_results)

        yield event.plain_result(response)

    @command("道具市场侵袭")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def use_market_invasion(self, event: AstrMessageEvent):
        """使用市场侵袭道具"""
        # 解析@的目标用户
        target_id = self._parse_at_target(event)
        if not target_id:
            yield event.plain_result("❌ 请@要侵袭的对象")
            return

        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())

        # 获取用户道具
        user_props = self._get_user_props(group_id, user_id)
        if "市场侵袭" not in user_props or user_props["市场侵袭"] < 1:
            yield event.plain_result("❌ 您没有市场侵袭道具")
            return

        # 获取用户数据和时间数据
        user_data = self._get_user_data(group_id, user_id)
        time_data = self._get_user_time_data(group_id, user_id)

        # 检查冷却时间（每小时限用一次）
        now = datetime.now(SHANGHAI_TZ)
        last_use_key = "last_market_invasion_use"
        if time_data.get(last_use_key):
            last_use = SHANGHAI_TZ.localize(datetime.fromisoformat(time_data[last_use_key]))
            if (now - last_use) < timedelta(hours=1):
                remaining_minutes = 60 - int((now - last_use).total_seconds() / 60)
                yield event.plain_result(f"❌ 市场侵袭太频繁，请等待{remaining_minutes}分钟后再试")
                return

        # 获取目标用户数据
        target_data = self._get_user_data(group_id, target_id)

        # 检查双方是否符合条件
        user_total_assets = user_data["coins"] + user_data["bank"] + user_data.get("niuniu_coins", 0.0)
        user_contractor_count = len(user_data["contractors"])

        target_total_assets = target_data["coins"] + target_data["bank"] + target_data.get("niuniu_coins", 0.0)
        target_contractor_count = len(target_data["contractors"])

        if not ((user_total_assets > 2000 or user_contractor_count > 5) and 
                (target_total_assets > 2000 or target_contractor_count > 5)):
            yield event.plain_result("❌ 双方必须都满足条件（总资产>2000或性奴>5）")
            return

        # 随机决定胜负（60%发起方胜，40%目标方胜）
        user_wins = random.random() < 0.60

        # 初始化结果变量
        user_gain = 0
        user_slaves_gained = []
        target_loss = 0
        target_slaves_lost = []

        # 计算目标损失（10%-30%资产）
        target_loss_percent = random.uniform(0.1, 0.3)
        target_loss_amount = target_total_assets * target_loss_percent

        # 加载群组数据
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        group_data = data.setdefault(group_id, {})
        group_data[user_id] = user_data
        group_data[target_id] = target_data

        # 处理资产转移
        if user_wins:
            # 发起方获胜
            # 从目标扣除资产
            if target_data["coins"] >= target_loss_amount:
                target_data["coins"] -= target_loss_amount
            else:
                remaining = target_loss_amount - target_data["coins"]
                target_data["coins"] = 0
                target_data["bank"] = max(0, target_data["bank"] - remaining)

            # 给发起方增加资产
            user_data["coins"] += target_loss_amount
            user_gain = target_loss_amount
            target_loss = target_loss_amount

            # 处理性奴转移（最多3个）
            if target_data["contractors"]:
                # 只处理非永久绑定的性奴
                transferable = []
                for cid in target_data["contractors"]:
                    slave_data = self._get_user_data(group_id, cid)
                    if not slave_data.get("is_permanent", False):
                        transferable.append(cid)
    
                if transferable:
                    num_transfer = min(3, len(transferable))
                    transfer_ids = random.sample(transferable, num_transfer)
        
                    # 转移性奴
                    for cid in transfer_ids:
                        # 从目标移除
                        if cid in target_data["contractors"]:
                            target_data["contractors"].remove(cid)
            
                        # 添加到发起方
                        if cid not in user_data["contractors"]:
                            user_data["contractors"].append(cid)
            
                        # ==== 修复：正确更新性奴的主人信息 ====
                        # 获取性奴数据
                        slave_data = self._get_user_data(group_id, cid)
                        # 更新主人信息
                        slave_data["contracted_by"] = user_id
                        # 保存到待更新数据中
                        group_data[cid] = slave_data
            
                        try:
                            slave_name = await self._get_at_user_name(event, cid)
                            target_slaves_lost.append(slave_name)
                            user_slaves_gained.append(slave_name)
                        except:
                            target_slaves_lost.append(f"用户{cid[-4:]}")
                            user_slaves_gained.append(f"用户{cid[-4:]}")
        else:
            # 目标方获胜
            # 从发起方扣除资产（惩罚更多）
            user_loss_percent = random.uniform(0.15, 0.35)
            user_loss_amount = user_total_assets * user_loss_percent

            if user_data["coins"] >= user_loss_amount:
                user_data["coins"] -= user_loss_amount
            else:
                remaining = user_loss_amount - user_data["coins"]
                user_data["coins"] = 0
                user_data["bank"] = max(0, user_data["bank"] - remaining)

            # 给目标方增加资产
            target_data["coins"] += user_loss_amount
            user_gain = -user_loss_amount
            target_loss = -user_loss_amount  # 负值表示目标方获利

            # 处理性奴转移（发起方失去性奴）
            if user_data["contractors"]:
                # 只处理非永久绑定的性奴
                transferable = []
                for cid in user_data["contractors"]:
                    slave_data = self._get_user_data(group_id, cid)
                    if not slave_data.get("is_permanent", False):
                        transferable.append(cid)
    
                if transferable:
                    num_transfer = min(3, len(transferable))
                    transfer_ids = random.sample(transferable, num_transfer)
        
                    # 转移性奴
                    for cid in transfer_ids:
                        # 从发起方移除
                        if cid in user_data["contractors"]:
                            user_data["contractors"].remove(cid)
            
                        # 添加到目标方
                        if cid not in target_data["contractors"]:
                            target_data["contractors"].append(cid)
            
                        # ==== 修复：正确更新性奴的主人信息 ====
                        # 获取性奴数据
                        slave_data = self._get_user_data(group_id, cid)
                        # 更新主人信息
                        slave_data["contracted_by"] = target_id
                        # 保存到待更新数据中
                        group_data[cid] = slave_data
            
                        try:
                            slave_name = await self._get_at_user_name(event, cid)
                            user_slaves_gained.append(slave_name)  # 这里表示发起方失去的性奴
                            target_slaves_lost.append(slave_name)  # 目标方获得的性奴
                        except:
                            user_slaves_gained.append(f"用户{cid[-4:]}")
                            target_slaves_lost.append(f"用户{cid[-4:]}")

        # 更新使用者冷却时间
        time_data[last_use_key] = now.replace(tzinfo=None).isoformat()

        # 扣除道具
        user_props["市场侵袭"] -= 1
        if user_props["市场侵袭"] <= 0:
            del user_props["市场侵袭"]

        # 保存数据
        try:
            # 保存道具数据
            self._update_user_props(group_id, user_id, user_props)

            # 保存用户数据
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
                
            # 保存时间数据
            self._save_user_time_data(group_id, user_id, time_data)
            
            # 记录日志
            self._log_operation("info", 
                f"市场侵袭: group={group_id}, attacker={user_id}, "
                f"target={target_id}, result={'win' if user_wins else 'lose'}"
            )
        except Exception as e:
            self._log_operation("error", f"市场侵袭保存数据失败: {str(e)}")

        # 获取用户名
        user_name = event.get_sender_name()
        target_name = await self._get_at_user_name(event, target_id)

        # 构建响应消息
        response = "⚔️ 市场侵袭结果:\n\n"

        if user_wins:
            response += f"🏆 在资本的斗争中 {user_name} 战胜了 {target_name}！\n"
            response += f"- 掠夺资产: {user_gain:.1f}金币\n"
            if user_slaves_gained:
                response += f"- 获得性奴 {len(user_slaves_gained)}名: {', '.join(user_slaves_gained)}\n"
            else:
                response += "- 没有获得性奴\n"
        else:
            response += f"💥 在资本的斗争中 {target_name} 抵御了 {user_name} 的侵袭！\n"
            response += f"- 损失资产: {-user_gain:.1f}金币\n"
            if user_slaves_gained:
                response += f"- 失去性奴 {len(user_slaves_gained)}名: {', '.join(user_slaves_gained)}\n"
            else:
                response += "- 没有失去性奴\n"

        response += f"\n💼 {user_name} 当前资产: {user_data['coins'] + user_data['bank']:.1f}金币"
        response += f"\n💼 {target_name} 当前资产: {target_data['coins'] + target_data['bank']:.1f}金币"

        yield event.plain_result(response)
#endregion

#region ==================== 社交系统 ====================
    @command("约会")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def invite_date(self, event: AstrMessageEvent):
        """发起约会邀请"""
        target_id = self._parse_at_target(event)
        if not target_id:
            yield event.plain_result("❌ 请@要约会的对象")
            return
        
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        
        # 检查是否是自己
        if user_id == target_id:
            yield event.plain_result("不能和自己约会哦~")
            return
        
        # 检查是否是机器人
        if target_id == event.get_self_id():
            yield event.plain_result("抱歉，我现在很忙，没有时间约会~")
            return
        
        # 检查每日约会次数
        user_data = self._get_user_social_data(group_id, user_id)
        today = datetime.now(SHANGHAI_TZ).strftime("%Y-%m-%d")
        
        if user_data["last_date_date"] != today:
            user_data["daily_date_count"] = 0
            user_data["last_date_date"] = today
        
        if user_data["daily_date_count"] >= 3:
            yield event.plain_result("你今天已经约会3次了，请明天再来~")
            return
        
        # 创建约会邀请
        group_id_str = str(group_id)
        if group_id_str not in self.active_invitations:
            self.active_invitations[group_id_str] = {}
        
        self.active_invitations[group_id_str][target_id] = {
            "initiator_id": user_id,
            "created_at": datetime.now(SHANGHAI_TZ)
        }
        
        # 更新约会次数
        user_data["daily_date_count"] += 1
        
        # 保存数据
        social_data = self._load_social_data()
        social_data.setdefault(group_id_str, {})[user_id] = user_data
        self._save_social_data(social_data)
        
        target_name = await self._get_at_user_name(event, target_id)
        yield event.plain_result(f"✅ 已向 {target_name} 发送约会邀请，等待对方回应...")

    @command("同意约会")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def accept_date(self, event: AstrMessageEvent):
        """同意约会邀请"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        group_id_str = str(group_id)
        
        # 获取邀请
        if group_id_str not in self.active_invitations or user_id not in self.active_invitations[group_id_str]:
            yield event.plain_result("❌ 没有待处理的约会邀请")
            return
        
        invitation = self.active_invitations[group_id_str][user_id]
        
        # 检查邀请是否过期
        if datetime.now(SHANGHAI_TZ) - invitation['created_at'] > timedelta(seconds=60):
            del self.active_invitations[group_id_str][user_id]
            yield event.plain_result("❌ 约会邀请已过期")
            return
        
        # 执行约会
        initiator_id = invitation["initiator_id"]
        initiator_name = await self._get_at_user_name(event, initiator_id)
        user_name = event.get_sender_name()
        
        # 运行约会流程
        result = await self._run_date(group_id, initiator_id, user_id, initiator_name, user_name)
        
        # 删除邀请
        del self.active_invitations[group_id_str][user_id]
        
        # 构建响应消息
        response = f"💖 {initiator_name} 和 {user_name} 的约会结果：\n\n"
        for event_info in result["events"]:
            response += f"【{event_info['name']}】\n{event_info['description']}\n\n"
        
        response += f"✨ {initiator_name} 对 {user_name} 的好感度变化: +{result['user_a_to_b_change']}\n"
        response += f"✨ {user_name} 对 {initiator_name} 的好感度变化: +{result['user_b_to_a_change']}\n\n"
        
        if result["user_a_to_b_level_up"]:
            response += f"🎉 {initiator_name} 对 {user_name} 的关系提升为: {result['user_a_to_b_level_after']}\n"
        if result["user_b_to_a_level_up"]:
            response += f"🎉 {user_name} 对 {initiator_name} 的关系提升为: {result['user_b_to_a_level_after']}\n"
        
        yield event.plain_result(response)

    async def _run_date(self, group_id: str, user_a_id: str, user_b_id: str, user_a_name: str, user_b_name: str) -> dict:
        """执行约会流程"""
        # 记录开始时的好感度
        a_to_b_before = self.get_favorability(group_id, user_a_id, user_b_id)
        b_to_a_before = self.get_favorability(group_id, user_b_id, user_a_id)
        
        # 随机选择3个事件
        event_count = min(3, len(DATE_EVENTS))
        selected_events = random.sample(DATE_EVENTS, event_count)
        
        # 累计好感度变化
        a_to_b_change = 0
        b_to_a_change = 0
        
        # 处理每个事件
        events_result = []
        for event in selected_events:
            change_min, change_max = event["favorability_change"]
            change_a = random.randint(change_min, change_max)
            change_b = random.randint(change_min, change_max)
            
            a_to_b_change += change_a
            b_to_a_change += change_b
            
            events_result.append({
                "name": event["name"],
                "description": event["description"],
                "a_to_b_change": change_a,
                "b_to_a_change": change_b
            })
        
        # 更新好感度
        a_to_b_after = self._update_favorability(group_id, user_a_id, user_b_id, a_to_b_change)
        b_to_a_after = self._update_favorability(group_id, user_b_id, user_a_id, b_to_a_change)
        
        # 检查关系变化
        a_to_b_level_before = self._get_relation_level(a_to_b_before)
        a_to_b_level_after = self._get_relation_level(a_to_b_after)
        b_to_a_level_before = self._get_relation_level(b_to_a_before)
        b_to_a_level_after = self._get_relation_level(b_to_a_after)
        
        return {
            "events": events_result,
            "user_a_to_b_change": a_to_b_change,
            "user_b_to_a_change": b_to_a_change,
            "user_a_to_b_level_before": a_to_b_level_before,
            "user_a_to_b_level_after": a_to_b_level_after,
            "user_b_to_a_level_before": b_to_a_level_before,
            "user_b_to_a_level_after": b_to_a_level_after,
            "user_a_to_b_level_up": a_to_b_level_before != a_to_b_level_after,
            "user_b_to_a_level_up": b_to_a_level_before != b_to_a_level_after
        }

    @command("缔结关系")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def form_relationship(self, event: AstrMessageEvent):
        """缔结特殊关系"""
        parts = event.message_str.strip().split()
        if len(parts) < 3:
            yield event.plain_result("❌ 格式错误，请使用：/缔结关系 @对方 关系类型")
            yield event.plain_result("可用关系类型：恋人、兄弟、包养")
            return
        
        target_id = self._parse_at_target(event)
        if not target_id:
            yield event.plain_result("❌ 请@要缔结关系的对象")
            return
        
        relation_type = parts[2]
        if relation_type not in ["恋人", "兄弟", "包养"]:
            yield event.plain_result("❌ 无效的关系类型，可用：恋人、兄弟、包养")
            return
        
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        
        # 不能与自己缔结关系
        if user_id == target_id:
            yield event.plain_result("❌ 不能与自己缔结特殊关系哦~")
            return
        
        # 获取好感度
        user_to_target = self.get_favorability(group_id, user_id, target_id)
        target_to_user = self.get_favorability(group_id, target_id, user_id)
        
        # 检查好感度是否足够
        if relation_type == "包养":
            if target_to_user < 100:
                yield event.plain_result(f"❌ 对方对你的好感度不足，需要达到100点才能被包养。当前好感度: {target_to_user}")
                return
        else:
            if user_to_target < 100:
                yield event.plain_result(f"❌ 你对对方的好感度不足，需要达到100点。当前好感度: {user_to_target}")
                return
            if target_to_user < 100:
                yield event.plain_result(f"❌ 对方对你的好感度不足，需要达到100点。当前好感度: {target_to_user}")
                return
        
        # 检查所需道具
        required_item = SPECIAL_RELATION_ITEMS.get(relation_type)
        if not required_item:
            yield event.plain_result(f"❌ 无效的关系类型: {relation_type}")
            return
        
        # 检查用户是否拥有所需道具
        user_props = self._get_user_props(group_id, user_id)
        if required_item not in user_props or user_props[required_item] < 1:
            yield event.plain_result(f"❌ 缔结{relation_type}关系需要{required_item}，你还没有这个道具！")
            return
        
        # 获取用户数据
        user_data = self._get_user_social_data(group_id, user_id)
        target_data = self._get_user_social_data(group_id, target_id)
        
        # 检查关系是否已被占用
        internal_type = SPECIAL_RELATION_TYPES[relation_type]
        if user_data["special_relations"][internal_type] is not None:
            yield event.plain_result(f"❌ 你已经有一个'{relation_type}'关系了，请先解除现有关系。")
            return
          
        if target_data["special_relations"][internal_type] is not None:
            yield event.plain_result(f"❌ 对方已经有一个'{relation_type}'关系了，无法与你缔结。")
            return
        
        # 检查两人之间是否已经有其他特殊关系
        existing_relation = self.get_special_relation(group_id, user_id, target_id)
        if existing_relation:
            yield event.plain_result(f"❌ 你们之间已经有'{existing_relation}'关系了，不能再缔结其他特殊关系。")
            return
        
        # 缔结关系
        user_data["special_relations"][internal_type] = target_id
        target_data["special_relations"][internal_type] = user_id
        
        # 解锁好感度上限
        if self.get_favorability(group_id, user_id, target_id) == 100:
            self._update_favorability(group_id, user_id, target_id, 1)
        if self.get_favorability(group_id, target_id, user_id) == 100:
            self._update_favorability(group_id, target_id, user_id, 1)
        
        # 扣除道具
        user_props[required_item] -= 1
        if user_props[required_item] <= 0:
            del user_props[required_item]
        self._update_user_props(group_id, user_id, user_props)
        
        # 保存社交数据
        social_data = self._load_social_data()
        social_data.setdefault(str(group_id), {})[user_id] = user_data
        social_data[str(group_id)][target_id] = target_data
        self._save_social_data(social_data)
        
        # 记录日志
        self._log_operation("info", 
            f"缔结关系: group={group_id}, user={user_id}, "
            f"target={target_id}, relation={relation_type}"
        )
        
        target_name = await self._get_at_user_name(event, target_id)
        yield event.plain_result(f"✅ 恭喜！你与 {target_name} 成功缔结'{relation_type}'关系！\n- 消耗道具: {required_item}")

    @command("解除关系")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def break_relationship(self, event: AstrMessageEvent):
        """解除特殊关系"""
        target_id = self._parse_at_target(event)
        if not target_id:
            yield event.plain_result("❌ 请@要解除关系的对象")
            return
        
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        
        # 不能与自己解除关系
        if user_id == target_id:
            yield event.plain_result("❌ 不能与自己解除关系哦~")
            return
          
        # 获取用户数据
        user_data = self._get_user_social_data(group_id, user_id)
        target_data = self._get_user_social_data(group_id, target_id)
        
        # 查找关系
        relation_type = None
        for rel_type, rel_id in user_data["special_relations"].items():
            if rel_id == target_id:
                relation_type = rel_type
                break
          
        if not relation_type:
            yield event.plain_result("❌ 你们之间没有特殊关系，无法解除。")
            return
        
        # 解除关系
        user_data["special_relations"][relation_type] = None
        for rel_type, rel_id in target_data["special_relations"].items():
            if rel_id == user_id:
                target_data["special_relations"][rel_type] = None
                break
        
        # 重置好感度为50
        self._update_favorability(group_id, user_id, target_id, 50 - self.get_favorability(group_id, user_id, target_id))
        self._update_favorability(group_id, target_id, user_id, 50 - self.get_favorability(group_id, target_id, user_id))
        
        # 保存数据
        social_data = self._load_social_data()
        social_data.setdefault(str(group_id), {})[user_id] = user_data
        social_data[str(group_id)][target_id] = target_data
        self._save_social_data(social_data)
        
        # 记录日志
        self._log_operation("info", 
            f"解除关系: group={group_id}, user={user_id}, "
            f"target={target_id}, relation={relation_type}"
        )
        
        relation_name = RELATION_TYPE_NAMES.get(relation_type, relation_type)
        target_name = await self._get_at_user_name(event, target_id)
        yield event.plain_result(f"✅ 已成功解除与 {target_name} 的'{relation_name}'关系。双方好感度已重置为50。")

    @command("查看关系")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def view_relationship(self, event: AstrMessageEvent):
        """查看两人之间的关系"""
        target_id = self._parse_at_target(event)
        if not target_id:
            yield event.plain_result("❌ 请@要查看关系的对象")
            return
        
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        
        # 获取相互好感度
        user_to_target = self.get_favorability(group_id, user_id, target_id)
        target_to_user = self.get_favorability(group_id, target_id, user_id)
        
        # 获取关系等级
        user_to_target_level = self._get_relation_level(user_to_target)
        target_to_user_level = self._get_relation_level(target_to_user)
        
        # 获取特殊关系
        special_relation = self.get_special_relation(group_id, user_id, target_id)
        
        # 构建响应
        target_name = await self._get_at_user_name(event, target_id)
        response = f"💞 你与 {target_name} 的关系：\n"
        response += f"- 你对TA的好感度: {user_to_target} ({user_to_target_level})\n"
        response += f"- TA对你的好感度: {target_to_user} ({target_to_user_level})\n"
        
        if special_relation:
            response += f"- 特殊关系: {special_relation}\n"
        
        yield event.plain_result(response)

    @command("社交网络")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def social_network(self, event: AstrMessageEvent):
        """查看自己的社交网络"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        
        user_data = self._get_user_social_data(group_id, user_id)
        favorability_data = user_data["favorability"]
        
        # 按好感度排序
        sorted_relations = sorted(
            favorability_data.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]  # 取前5个
        
        # 获取特殊关系
        special_relations = {}
        for rel_type, rel_id in user_data["special_relations"].items():
            if rel_id:
                special_relations[rel_id] = RELATION_TYPE_NAMES.get(rel_type, rel_type)
        
        # 构建响应
        response = "🌟 你的社交网络（按好感度排序）:\n\n"
        for i, (target_id, favorability) in enumerate(sorted_relations, 1):
            if favorability <= 0:
                continue
                
            level = self._get_relation_level(favorability)
            special_relation = special_relations.get(target_id)
            
            try:
                target_name = await self._get_at_user_name(event, target_id)
            except:
                target_name = f"用户{target_id[-4:]}"
            
            relation_info = f"{i}. {target_name} - 好感度: {favorability} ({level})"
            if special_relation:
                relation_info += f" - {special_relation}"
            
            response += relation_info + "\n"
        
        yield event.plain_result(response)

    @command("赠送礼物")
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def give_gift(self, event: AstrMessageEvent):
        """赠送礼物增加好感度"""
        parts = event.message_str.strip().split()
        if len(parts) < 3:
            yield event.plain_result("❌ 格式错误，请使用：/赠送礼物 @对方 礼物名")
            return
        
        target_id = self._parse_at_target(event)
        if not target_id:
            yield event.plain_result("❌ 请@要赠送礼物的对象")
            return
        
        gift_name = parts[2]
        if gift_name not in ["玫瑰花束", "定制蛋糕"]:
            yield event.plain_result("❌ 无效的礼物，可用礼物：玫瑰花束、定制蛋糕")
            return
        
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        
        # 检查用户是否拥有该礼物
        user_props = self._get_user_props(group_id, user_id)
        if gift_name not in user_props or user_props[gift_name] < 1:
            yield event.plain_result(f"❌ 你没有{gift_name}，请先在商店购买")
            return
        
        # 确定好感度增加值
        if gift_name == "玫瑰花束":
            favorability_gain = random.randint(5, 10)
        elif gift_name == "定制蛋糕":
            favorability_gain = random.randint(8, 15)
        else:
            favorability_gain = 0
        
        # 更新好感度
        new_favorability = self._update_favorability(group_id, target_id, user_id, favorability_gain)
        
        # 扣除道具
        user_props[gift_name] -= 1
        if user_props[gift_name] <= 0:
            del user_props[gift_name]
        self._update_user_props(group_id, user_id, user_props)
        
        # 记录日志
        self._log_operation("info", 
            f"赠送礼物: group={group_id}, from={user_id}, "
            f"to={target_id}, gift={gift_name}, "
            f"favorability_gain={favorability_gain}"
        )
        
        target_name = await self._get_at_user_name(event, target_id)
        yield event.plain_result(f"🎁 你向 {target_name} 赠送了{gift_name}，TA对你的好感度增加了{favorability_gain}点！\n当前好感度: {new_favorability}")
#endregion
