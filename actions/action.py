import json
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import AllSlotsReset
from rasa_sdk.executor import CollectingDispatcher
import os
import re
from time_ex.TimeNormalizer import TimeNormalizer
import calendar
import yaml
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

try:
    with open("car_series.yml", "r", encoding="utf-8") as f:
        datas_lookup_CarSeries = yaml.load(f, Loader=yaml.FullLoader)
except:
    with open(os.path.join("actions", "car_series.yml"), "r", encoding="utf-8") as f:
        datas_lookup_CarSeries = yaml.load(f, Loader=yaml.FullLoader)


class ActionCallExternalApi(Action):

    def name(self) -> Text:
        return "action_call_external_api"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        intent = None
        confidence = 0
        if tracker.latest_message:
            intent = tracker.latest_message['intent']['name']
            confidence = tracker.latest_message['intent']['confidence']
        params = tracker.slots
        params['content'] = tracker.latest_message['text']
        resp = {"type": "task", "answer": "", 'content': params.get('content'),
                "params": params.get('params'), 'intent': params.get('intent'),
                'confidence': confidence}
        if intent:
            params['params'] = {}
            CarSeries = tracker.get_slot('CarSeries') if tracker.get_slot('CarSeries') else ""
            DataSource = tracker.get_slot('DataSource') if tracker.get_slot('DataSource') else ""
            params['params'] = {"CarSeries": CarSeries, "DataSource": DataSource}
            resp["answer"] = intent
            resp["params"] = params.get('params')
            resp["intent"] = intent
            msg = json.dumps(resp)
            dispatcher.utter_message(text=msg)

        return [AllSlotsReset()]


def subtract_months_and_days(months=0, days=0):
    """
    计算几个月和几天前的日期。

    :param months: 倒推的月份数
    :param days: 倒推的天数
    :return: 格式化的日期字符串（YYYY-MM-DD）
    """
    current_date = datetime.now().date()
    # 先倒推月份
    result_date = current_date - relativedelta(months=months)
    # 再倒推天数
    result_date = result_date - timedelta(days=days)

    return result_date.strftime('%Y-%m-%d')


def replace_date(match):
    year, month, day = match.groups()
    # 如果年份是两位数，补全为四位数
    if len(year) == 2:
        year = "20" + year  # 假设年份属于 2000 年代
    # 返回转换后的日期格式
    return f"{year}年{month}月{day}日"


def normalize_time(Time_temp):
    # 一阶段处理
    Time_temp = Time_temp.replace("今年", datetime.now().strftime('%Y年')).replace("半年", "6个月").replace("一年半",
                                                                                                     "一年6个月").replace(
        "这个月", datetime.now().strftime('%Y年#%m月')).replace(
        "本月", datetime.now().strftime('%Y年#%m月'))
    Time_temp = Time_temp.replace("#0", "")
    month_mapping = {
        "1月": 1, "2月": 2, "3月": 3, "4月": 4, "5月": 5, "6月": 6,
        "7月": 7, "8月": 8, "9月": 9, "10月": 10, "11月": 11, "12月": 12,
        "一月": 1, "二月": 2, "三月": 3, "四月": 4, "五月": 5, "六月": 6,
        "七月": 7, "八月": 8, "九月": 9, "十月": 10, "十一月": 11, "十二月": 12
    }
    pattern1 = r"\b(?:今年)?(?:\d{1,2}月|一月|二月|三月|四月|五月|六月|七月|八月|九月|十月|十一月|十二月)\b(?!\s*\d{1,2}日|\d{1,2}号|至|到)"

    tn = TimeNormalizer()
    match1 = re.search(pattern1, Time_temp)
    if match1:
        month_str = match1.group()
        month_str = month_str.replace("今年", "")
        month_num = month_mapping.get(month_str)
        current_year = datetime.today().year
        _, last_day = calendar.monthrange(current_year, month_num)
        start_time = datetime(current_year, month_num, 1)
        end_time = datetime(current_year, month_num, last_day)
        res = str({'type': 'timestamp', 'timestamp': [start_time.strftime('%Y-%m-%d'), end_time.strftime('%Y-%m-%d')]})
        return res

    pattern2 = r"(\d{2}|\d{4})[/-](\d{2})[/-](\d{2})"
    match2 = re.search(pattern2, Time_temp)
    if match2:
        Time_temp = re.sub(pattern2, replace_date, Time_temp)

    if "近" in Time_temp and "日" in Time_temp:
        Time_temp = Time_temp.replace("日", "天")
        res = tn.parse(Time_temp)
    elif "至今" in Time_temp:
        Time_temp = Time_temp.replace("至今", "至" + datetime.now().strftime('%Y年%m月%d日'))
        res = tn.parse(Time_temp)
    elif "到今天" in Time_temp:
        Time_temp = Time_temp.replace("到今天", "到" + datetime.now().strftime('%Y年%m月%d日'))
        res = tn.parse(Time_temp)
    elif "上个月" in Time_temp and ("日" not in Time_temp and "天" not in Time_temp and "号" not in Time_temp):
        res = tn.parse(Time_temp)
        res = json.loads(res)
        dt = datetime.strptime(res['timestamp'], "%Y-%m-%d %H:%M:%S")
        start_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        last_day = calendar.monthrange(int(dt.strftime("%Y")), int(dt.strftime("%m")))[1]
        end_time = dt.replace(day=last_day).strftime("%Y-%m-%d %H:%M:%S")
        res = str({'type': 'timespan', 'timespan': [start_time, end_time]})
    elif "上周" in Time_temp and ("日" not in Time_temp and "天" not in Time_temp and "号" not in Time_temp):
        pattern3 = r"^上周$"
        match3 = re.search(pattern3, Time_temp)
        if match3:
            res = tn.parse(Time_temp.replace("上周", "上周一到周五"))
        else:
            res = tn.parse(Time_temp)
    else:
        res = tn.parse(Time_temp)
    res = json.loads(res.replace("'", '"'))
    # print(res)
    # 二阶段处理
    if res["type"]:
        if res["type"] == "timespan":
            start_time = datetime.strptime(res['timespan'][0], "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(res['timespan'][1], "%Y-%m-%d %H:%M:%S")
            res = {"type": "timespan", "time": [start_time.strftime("%Y-%m-%d"), end_time.strftime("%Y-%m-%d")]}
        elif res["type"] == "timedelta":
            time_dict = {key: value for key, value in res['timedelta'].items() if key in {'year', 'month', 'day'}}
            month = time_dict.get('month')
            day = time_dict.get('day')
            start_time = subtract_months_and_days(months=month, days=day)
            res = {"type": "timespan",
                   "time": [start_time, datetime.now().strftime("%Y-%m-%d")]}
        elif res["type"] == "timestamp":
            time = datetime.strptime(res['timestamp'], "%Y-%m-%d %H:%M:%S")
            res = {"type": "timestamp", "time": [time.strftime("%Y-%m-%d"), time.strftime("%Y-%m-%d")]}
        else:
            res = {"type": "error"}
    else:
        res = {"type": "error"}
    return res


content = "过去48小时"
res = normalize_time(content)
print(res)


def extract_mean(s):
    # 定义正则表达式，匹配 "小于" 或 "大于" 以及后面的数字
    pattern = r'平均值\s*(大于|小于)\s*(\d+(\.\d{1,2})?)'
    match = re.search(pattern, s)
    if match:
        operator = match.group(1)  # 提取 "小于" 或 "大于"
        value = float(match.group(2))
        return operator, str(value)
    else:
        return "", ""


def extract_variance(s):
    # 定义正则表达式，匹配 "小于" 或 "大于" 以及后面的数字
    pattern = r'方差\s*(大于|小于)\s*(\d+(\.\d{1,2})?)'
    match = re.search(pattern, s)
    if match:
        operator = match.group(1)  # 提取 "小于" 或 "大于"
        value = float(match.group(2))
        return operator, str(value)
    else:
        return "", ""


def extract_number_soc(s):
    # 定义正则表达式，匹配可能带负号的整数
    pattern = r'-?\d+\.?\d*'
    match = re.search(pattern, s)

    if match:
        number = float(match.group(0))
        return str(number)
    else:
        return ""


class ActionCallExternalApiOfElectricity(Action):

    def name(self) -> Text:
        return "action_call_external_api_electricity"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        intent = None
        confidence = 0
        if tracker.latest_message:
            intent = tracker.latest_message['intent']['name']
            confidence = tracker.latest_message['intent']['confidence']
        params = tracker.slots
        params['content'] = tracker.latest_message['text']
        DetailOfElectricityList = ["累计放电", "真实电量"]
        resp = {"type": "0", "answer": "", 'content': params.get('content'),
                "params": params.get('params'), 'intent': params.get('intent'),
                'confidence': confidence}
        if intent:
            params['params'] = {}
            ElectricityData = {}
            CarSeries_list = []
            CarSeries = tracker.get_slot('CarSeries') if tracker.get_slot('CarSeries') else ""
            print("==================")
            print(f"车系：{CarSeries}")
            CarSeries_list.append(CarSeries)
            if len(CarSeries) > 0:
                CarSeries_list.extend([item for item in datas_lookup_CarSeries if item.upper().replace(" ", "").replace("-", "") in params['content'].replace(" ", "").replace("-", "")])
                CarSeries = max(CarSeries_list, key=len)

            Time_temp = tracker.get_slot('Time') if tracker.get_slot('Time') else ""
            print(f"时间：{Time_temp}")
            if len(Time_temp) > 0:
                try:
                    Time = normalize_time(Time_temp)
                except:
                    Time = {"type": "error"}
            else:
                Time = {}
            # Mean = tracker.get_slot('Mean') if tracker.get_slot('Mean') else ""
            # print(f"均值：{Mean}")
            operator_mean, value_mean = extract_mean(params['content'])
            # Variance = tracker.get_slot('Variance') if tracker.get_slot('Variance') else ""
            # print(f"方差：{Variance}")
            operator_variance, value_variance = extract_variance(params['content'])
            # StateOfCharge = tracker.get_slot('StateOfCharge') if tracker.get_slot('StateOfCharge') else ""
            pattern_soc = r"SOC.*?(-?\d+\.?\d*)"
            match = re.search(pattern_soc, params['content'])
            if match:
                StateOfCharge = match.group(1)
            else:
                StateOfCharge = ""
            print(f"SOC：{StateOfCharge}")
            number_soc = extract_number_soc(StateOfCharge)

            ElectricityData["Time"] = Time
            ElectricityData["DetailOfElectricity"] = [item for item in DetailOfElectricityList if item in params['content']]
            ElectricityData["Mean"] = {"operator": operator_mean, "value": value_mean}
            ElectricityData["Variance"] = {"operator": operator_variance, "value": value_variance}
            ElectricityData["SOC"] = {"value": number_soc}

            params['params'] = {"CarSeries": CarSeries, "ElectricityData": ElectricityData}
            resp["answer"] = intent
            resp["params"] = params.get('params')
            resp["intent"] = intent
            if "亏电" in params['content']:
                resp["type"] = "1"
            msg = json.dumps(resp)
            dispatcher.utter_message(text=msg)

        return [AllSlotsReset()]
