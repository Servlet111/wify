import random
import time
from time import localtime
import pytz
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os


def get_region_data(config_data, weather_type):
    # 获取所有地区数据
    region_data = {}
    for k, v in config_data.items():
        if k[0:6] == "region":
            # 传入地区获取天气信息
            region = config_data[k]
            id = k[6:]
            weather, temp, max_temp, min_temp, wind_dir, sunrise, sunset, category, pm2p5, proposal = get_weather(
                region, config_data, weather_type)
            if weather == "地区数据找不到":
                yq_data = "地区数据找不到"
            elif weather == "未配置和风天气key":
                yq_data = "未配置和风天气key"
            elif weather == "未配置和风天气key或key配置错误":
                yq_data = "未配置和风天气key或key配置错误"
            else:
                # 获取疫情数据
                yq_data = yq(region, config_data, weather_type)
            region_data[k] = region
            region_data["weather{}".format(id)] = weather
            region_data["max_temp{}".format(id)] = max_temp
            region_data["min_temp{}".format(id)] = min_temp
            region_data["temp{}".format(id)] = temp
            region_data["wind_dir{}".format(id)] = wind_dir
            region_data["sunrise{}".format(id)] = sunrise
            region_data["sunset{}".format(id)] = sunset
            region_data["category{}".format(id)] = category
            region_data["pm2p5{}".format(id)] = pm2p5
            region_data["proposal{}".format(id)] = proposal
            region_data["yq{}".format(id)] = yq_data
    return region_data


def get_horoscope(config_data):
    # 获取所有星座数据
    horoscope_data = {}
    for k, v in config_data.items():
        if k[0:9] == "horoscope":
            try:
                key = config_data["tian_api"]
                url = "http://api.tianapi.com/star/index?key={}&astro={}".format(key, v)
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                    'Content-type': 'application/x-www-form-urlencoded'

                }
                response = get(url, headers=headers).json()
                if response["code"] == 200:
                    horoscope = response["newslist"][-1]["content"]
                    horoscope = horoscope.split("。")[0]
                else:
                    horoscope = response["msg"]
            except KeyError:
                horoscope = "未配置天行数据key"
            horoscope_data[k] = horoscope
    return horoscope_data


def yq(region, config_data, weather_type):
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Mobile Safari/537.36',
    }
    if weather_type == 2:
        try:
            key = config_data["tian_api"]
        except KeyError:
            data = "未配置天行数据key"
            return data
        region_url = "http://api.tianapi.com/citylookup/index?key={}&area={}".format(key, region)
        response = get(region_url, headers=headers).json()
        if response["code"] == 200:
            city = response["newslist"][0]["citycn"]
            if city in ["台北", "高雄", "台中", "台湾"]:
                city = "台湾"
        else:
            return response["msg"]
    else:
        key = config_data["weather_key"]
        url = "https://geoapi.qweather.com/v2/city/lookup?key={}&location={}".format(key, region)
        r = get(url).json()
        if r["code"] == "200":
            city = r["location"][0]["adm2"]
            if region in ["台北", "高雄", "台中", "台湾"]:
                city = "台湾"
        else:
            return ""
    response = get('https://covid.myquark.cn/quark/covid/data?city={}'.format(city), headers=headers).json()
    if city in ["北京", "上海", "天津", "重庆", "香港", "澳门", "台湾"]:
        city_data = response["provinceData"]
    else:
        city_data = response["cityData"]
    try:
        sure_new_loc = "昨日新增：{}".format(city_data["sure_new_loc"])
        sure_new_hid = "昨日无症状：{}".format(city_data["sure_new_hid"])
        present = "现有确诊：{}".format(city_data["present"])
        danger = "中/高风险区：{}/{}".format(city_data["danger"]["1"], city_data["danger"]["2"])
        statistics_time = response["time"]
        yq_data = "{}疫情数据\n{}\n{}\n{}\n{}\n{}".format(city, sure_new_loc, sure_new_hid, present, danger,
                                                      statistics_time)
    except TypeError:
        yq_data = ""
    return yq_data


def get_commemoration_day(today, commemoration_day):
    # 获取纪念日的日期格式
    commemoration_year = int(commemoration_day.split("-")[0])
    commemoration_month = int(commemoration_day.split("-")[1])
    commemoration_day = int(commemoration_day.split("-")[2])
    commemoration_date = date(commemoration_year, commemoration_month, commemoration_day)
    # 获取纪念日的日期差
    commemoration_days = str(today.__sub__(commemoration_date)).split(" ")[0]
    return commemoration_days


def get_commemoration_data(today, config_data):
    # 获取所有纪念日数据
    commemoration_days = {}
    for k, v in config_data.items():
        if k[0:13] == "commemoration":
            commemoration_days[k] = get_commemoration_day(today, v)
    return commemoration_days


def get_countdown_data(today, config_data):
    # 获取所有倒计时数据
    countdown_data = {}
    for k, v in config_data.items():
        if k.startswith("countdown") and "-" in v:
            date_parts = v.split("-")
            if len(date_parts) == 3:
                countdown_year = int(date_parts[0])
                countdown_month = int(date_parts[1])
                countdown_day = int(date_parts[2])
                countdown_date = date(countdown_year, countdown_month, countdown_day)
                if today == countdown_date:
                    countdown_data[k] = 0
                else:
                    countdown_data[k] = str(countdown_date - today).split(" ")[0]
    return countdown_data



def color(name, config):
    # 获取字体颜色，如没设置返回随机颜色
    try:
        if config[name] == "":
            color = get_color()
        else:
            color = config[name]
        return color
    except KeyError:
        color = get_color()
        return color


def get_color():
    # 获取随机颜色
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)


def get_access_token(config):
    try:
        # appId
        app_id = config["app_id"]
    except KeyError:
        print("推送消息失败，app_id未配置")
        os.system("pause")
        sys.exit(1)
    try:
        # appSecret
        app_secret = config["app_secret"]
    except KeyError:
        print("推送消息失败，app_secret未配置")
        os.system("pause")
        sys.exit(1)
    post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
                .format(app_id, app_secret))
    try:
        access_token = get(post_url).json()['access_token']
    except KeyError:
        print("获取access_token失败，请检查app_id和app_secret是否正确")
        os.system("pause")
        sys.exit(1)
    # print(access_token)
    return access_token


def get_weather(region, config, weather_type):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    if weather_type == 2:
        try:
            key = config["tian_api"]
        except KeyError:
            data = "未配置天行数据key"
            return data, data, data, data, data, data, data, data, data, data
        region_url = "http://api.tianapi.com/citylookup/index?key={}&area={}".format(key, region)
        response = get(region_url, headers=headers).json()
        if response["code"] == 200:
            ad_code = response["newslist"][0]["adcode"]
            # return ad_code, ad_code, ad_code, ad_code, ad_code, ad_code, ad_code, ad_code, ad_code, ad_code
            weather_url = "http://api.tianapi.com/tianqi/index?key={}&city={}&type=1".format(key, ad_code)
            response = get(weather_url, headers=headers).json()
            # 天气
            weather = response["newslist"][0]["weather"]
            # 当前温度
            temp = response["newslist"][0]["real"]
            # 风向
            wind_dir = response["newslist"][0]["wind"]
            # 最高气温
            max_temp = response["newslist"][0]["highest"]
            # 最低气温
            min_temp = response["newslist"][0]["lowest"]
            # 日出时间
            sunrise = response["newslist"][0]["sunrise"]
            # 日落时间
            sunset = response["newslist"][0]["sunset"]
            # 空气质量
            category = response["newslist"][0]["quality"]
            # pm2.5
            pm2p5 = "天行数据暂未返回pm2.5数据"
            # 今日建议
            proposal = response["newslist"][0]["tips"]
            return weather, temp, max_temp, min_temp, wind_dir, sunrise, sunset, category, pm2p5, proposal
        else:
            data = response["msg"]
            return data, data, data, data, data, data, data, data, data, data
    else:
        try:
            key = config["weather_key"]
        except KeyError:
            data = "未配置和风天气key"
            return data, data, data, data, data, data, data, data, data, data
        region_url = "https://geoapi.qweather.com/v2/city/lookup?location={}&key={}".format(region, key)
        response = get(region_url, headers=headers).json()
        if response["code"] == "404":
            # print("地区数据找不到")
            data = "地区数据找不到"
            return data, data, data, data, data, data, data, data, data, data
        elif response["code"] == "401":
            # print("未配置和风天气key或key配置错误")
            data = "未配置和风天气key或key配置错误"
            return data, data, data, data, data, data, data, data, data, data
        else:
            # 获取地区的location--id
            location_id = response["location"][0]["id"]
        weather_url = "https://devapi.qweather.com/v7/weather/now?location={}&key={}".format(location_id, key)
        response = get(weather_url, headers=headers).json()
        # 天气
        weather = response["now"]["text"]
        # 当前温度
        temp = response["now"]["temp"] + u"\N{DEGREE SIGN}" + "C"
        # 风向
        wind_dir = response["now"]["windDir"]
        # 获取逐日天气预报
        url = "https://devapi.qweather.com/v7/weather/3d?location={}&key={}".format(location_id, key)
        response = get(url, headers=headers).json()
        # 最高气温
        max_temp = response["daily"][0]["tempMax"] + u"\N{DEGREE SIGN}" + "C"
        # 最低气温
        min_temp = response["daily"][0]["tempMin"] + u"\N{DEGREE SIGN}" + "C"
        # 日出时间
        sunrise = response["daily"][0]["sunrise"]
        # 日落时间
        sunset = response["daily"][0]["sunset"]
        url = "https://devapi.qweather.com/v7/air/now?location={}&key={}".format(location_id, key)
        response = get(url, headers=headers).json()
        if response["code"] == "200":
            # 空气质量
            category = response["now"]["category"]
            # pm2.5
            pm2p5 = response["now"]["pm2p5"]
        else:
            # 国外城市获取不到数据
            category = ""
            pm2p5 = ""
        id = random.randint(1, 16)
        url = "https://devapi.qweather.com/v7/indices/1d?location={}&key={}&type={}".format(location_id, key, id)
        response = get(url, headers=headers).json()
        proposal = ""
        if response["code"] == "200":
            proposal += response["daily"][0]["text"]
        return weather, temp, max_temp, min_temp, wind_dir, sunrise, sunset, category, pm2p5, proposal


def get_tianhang(config):
    # 获取早安心语，晚安心语，健康小提示，土味情话，生活小窍门， 彩虹屁，毒鸡汤，舔狗日记，小段子，朋友圈文案， 文化谚语
    data = ["zaoan", "wanan", "healthtip", "saylove", "qiaomen", "caihongpi", "dujitang", "tiangou", "mnpara",
            "pyqwenan", "proverb"]
    data_list = {}
    for i in data:
        try:
            key = config["tian_api"]
            url = "http://api.tianapi.com/{}/index?key={}".format(i, key)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                'Content-type': 'application/x-www-form-urlencoded'

            }
            response = get(url, headers=headers).json()
            if response["code"] == 200:
                if i != "proverb":
                    content = response["newslist"][0]["content"]
                else:
                    content = "{}，{}".format(response["newslist"][0]["front"], response["newslist"][0]["behind"])
            else:
                content = response["msg"]
        except KeyError:
            content = "未配置天行数据key"
        if i == "caihongpi":
            i = "chp"
        elif i == "healthtip":
            i = "health_tip"
        elif i == "pyqwenan":
            i = "wenan"
        elif i == "qiaomen":
            i = "xqm"
        data_list[i] = content
    return data_list


def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    # 判断是否为农历生日
    if birthday_year[0] == "r":
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        # 获取农历生日的生日
        try:
            year_date = ZhDate(year, r_mouth, r_day).to_datetime().date()
        except TypeError:
            print("请检查生日的日子是否在今年存在")
            os.system("pause")
            sys.exit(1)

    else:
        # 获取国历生日的今年对应月和日
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        # 今年生日
        year_date = date(year, birthday_month, birthday_day)
    # 计算生日年份，如果还没过，按当年减，如果过了需要+1
    if today > year_date:
        if birthday_year[0] == "r":
            # 获取农历明年生日的月和日
            r_last_birthday = ZhDate((year + 1), r_mouth, r_day).to_datetime().date()
            birth_date = date((year + 1), r_last_birthday.month, r_last_birthday.day)
        else:
            birth_date = date((year + 1), birthday_month, birthday_day)
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    elif today == year_date:
        birth_day = 0
    else:
        birth_date = year_date
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    return birth_day


def get_ciba():
    url = "http://open.iciba.com/dsapi/"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    r = get(url, headers=headers)
    note_en = r.json()["content"]
    note_ch = r.json()["note"]
    return note_ch, note_en


def send_message(to_user, access_token, note_ch, note_en, config, horoscope_data, region_data, tianhang_data):
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    # 设置时区为亚洲/上海
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    # 获取当前时间，并将其转换到上海时区
    local_time = datetime.now(shanghai_tz)
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = datetime.date(datetime(year=year, month=month, day=day))
    week = week_list[today.isoweekday() % 7]
    # date1 = datetime.now()
    # 获取所有纪念日数据
    commemoration_data = get_commemoration_data(today, config)
    # 获取所有倒计时数据
    countdown_data = get_countdown_data(today, config)
    # 获取所有生日数据
    birthdays = {}
    for k, v in config.items():
        if k[0:5] == "birth":
            birthdays[k] = v
    try:
        template_id = config["template_id"]
    except KeyError:
        print("推送消息失败，模板id未配置")
        os.system("pause")
        sys.exit(1)
    data = {
        "touser": to_user,
        "template_id": template_id,
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {
                "value": "{} {}".format(today, week),
                "color": color("color_date", config)
            },
            "note_en": {
                "value": note_en,
                "color": color("color_note_en", config)
            },
            "note_ch": {
                "value": note_ch,
                "color": color("color_note_zh", config)
            },
        }
    }
    for key, value in tianhang_data.items():
        # 将天行数据插入data
        data["data"][key] = {"value": value, "color": color("color_{}".format(key), config)}
    for key, value in region_data.items():
        # 将地区数据插入data
        data["data"][key] = {"value": value, "color": color("color_{}".format(key), config)}
    for key, value in horoscope_data.items():
        # 将星座数据插入data
        data["data"][key] = {"value": value, "color": color("color_{}".format(key), config)}
    for key, value in commemoration_data.items():
        # 将纪念日数据插入data
        data["data"][key] = {"value": value, "color": color("color_{}".format(key), config)}
    for key, value in countdown_data.items():
        # 将倒计时数据插入data
        data["data"][key] = {"value": value, "color": color("color_{}".format(key), config)}
    for key, value in birthdays.items():
        # 获取距离下次生日的时间
        birth_day = get_birthday(value["birthday"], year, today)
        if birth_day == 0:
            birthday_data = "今天{}生日哦，祝{}生日快乐！".format(value["name"], value["name"])
        else:
            birthday_data = "距离{}的生日还有{}天".format(value["name"], birth_day)
        # 将生日数据插入data
        data["data"][key] = {"value": birthday_data, "color": color("color_{}".format(key), config)}
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    response = post(url, headers=headers, json=data).json()
    if response["errcode"] == 40037:
        print("推送消息失败，请检查模板id是否正确")
        os.system("pause")
        sys.exit(1)
    elif response["errcode"] == 40036:
        print("推送消息失败，请检查模板id是否为空")
        os.system("pause")
        sys.exit(1)
    elif response["errcode"] == 40003:
        print("推送消息失败，请检查微信号是否正确")
        os.system("pause")
        sys.exit(1)
    elif response["errcode"] == 43004:
        print("推送消息失败，用户取消关注公众号")
        os.system("pause")
        sys.exit(1)
    elif response["errcode"] == 0:
        print("推送消息成功，5秒后自动关闭")
    else:
        print(response)


def handler(event, context):
    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except FileNotFoundError:
        print("推送消息失败，请检查config.txt文件是否与程序位于同一路径")
        os.system("pause")
        sys.exit(1)
    except SyntaxError:
        print("推送消息失败，请检查配置文件格式是否正确")
        os.system("pause")
        sys.exit(1)

    # 获取accessToken
    accessToken = get_access_token(config)
    try:
        # 接收的用户
        users = config["user"]
    except KeyError:
        print("推送消息失败，接收用户未配置")
        os.system("pause")
        sys.exit(1)
    # 获取地区数据
    try:
        weather_type = config["weather_type"]
    except KeyError:
        weather_type = 1
    region_data = get_region_data(config, weather_type)
    try:
        note_ch = config["note_ch"]
        note_en = config["note_en"]
    except KeyError:
        note_ch, note_en = "", ""
    if note_ch == "" and note_en == "":
        # 获取词霸每日金句
        note_ch, note_en = get_ciba()
    # 获取星座数据
    horoscope_data = get_horoscope(config)
    # 获取天行数据
    tianhang_data = get_tianhang(config)
    # 公众号推送消息
    for user in users:
        send_message(user, accessToken, note_ch, note_en, config, horoscope_data, region_data, tianhang_data)
    time.sleep(5)


if __name__ == "__main__":
    handler(event="", context="")
