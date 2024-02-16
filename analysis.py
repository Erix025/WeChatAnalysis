import csv
from datetime import datetime, timedelta
import os
import xml
import icons
import re
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import tqdm
from collections import Counter
from snownlp import SnowNLP


class Msg:
    time: datetime
    sender: str
    content: str
    type: int
    icon: str
    receiver: str

    def __init__(self, item):
        self.time = datetime.strptime(item[8], "%Y-%m-%d %H:%M:%S")
        self.sender = item[10]
        if item[4] == "1":
            self.sender = "Eric025"
        self.content = item[7]
        self.type = int(item[2])
        if self.type != 47:
            self.icon = None
        else:
            emoji = icons.parser_xml(self.content)
            md5 = emoji.get("md5")
            self.icon = md5

    def __str__(self):
        return f"{self.time} {self.sender}: {self.content}"


def key_word_counter(messages, keywords, exceptwords):
    counter = {}
    if isinstance(keywords, str):
        keywords = [keywords]
    for msg in messages:
        if all(exceptword not in msg.content for exceptword in exceptwords) and any(
            [keyword in msg.content for keyword in keywords]
        ):
            if msg.sender == "":
                continue
            if msg.sender not in counter.keys():
                counter[msg.sender] = 0
            counter[msg.sender] += 1
    counter = dict(sorted(counter.items(), key=lambda x: x[1], reverse=True))
    return counter


def sentiment_analysis(messages):
    contents = [
        msg.content
        for msg in messages
        if msg.type == 1 and len(msg.content) < 50 and "捂脸" not in msg.content
    ]
    if len(contents) < 5:
        return
    sentiments = {}
    for msg in tqdm.tqdm(contents):
        sentiments[msg] = SnowNLP(msg).sentiments
    neg_count = len([s for s in sentiments.values() if s < 0.3])
    pos_count = len([s for s in sentiments.values() if s > 0.7])
    print(f"positive: {pos_count}")
    print(f"negative: {neg_count}")
    print(f"average:{sum(sentiments.values())/len(sentiments)}")
    most_5_positive = sorted(sentiments.items(), key=lambda x: x[1], reverse=True)[:5]
    most_5_negative = sorted(sentiments.items(), key=lambda x: x[1])[:5]
    print(most_5_positive)
    print(most_5_negative)


def sentense_freq(messages):
    contents = [msg.content for msg in messages if msg.type == 1]
    counter = Counter(contents)
    print(counter.most_common(10))


def top_icons(messages):
    icon_counts = {}
    for msg in messages:
        if msg.type == 47:
            icon = msg.icon
            if icon:
                if icon not in icon_counts:
                    icon_counts[icon] = 0
                icon_counts[icon] += 1
    # print most used icon
    # 获取排名前20的表情
    icon_counts = dict(sorted(icon_counts.items(), key=lambda x: x[1], reverse=True))
    icon_counts = dict(list(icon_counts.items())[:20])
    most_used_xml_strings = {}
    for msg in messages:
        if msg.icon in icon_counts.keys():
            if msg.icon not in most_used_xml_strings.keys():
                most_used_xml_strings[msg.icon] = msg.content
        if len(most_used_xml_strings) == 20:
            break
    image_paths = []
    for icon in icon_counts.keys():
        image_paths.append(icons.get_emoji(most_used_xml_strings[icon]))
    print(icon_counts)

    # 创建一个新的图形
    fig = plt.figure(figsize=(20, 20))
    print(image_paths)
    # 按顺序显示每一张图片
    for i, icon in enumerate(icon_counts.keys()):
        # 读取图片
        image_path = image_paths[i]
        try:
            img = mpimg.imread(image_path)
        except:
            continue
        # 创建一个子图
        ax = fig.add_subplot(5, 4, i + 1)

        # 显示图片
        ax.imshow(img)

        # 设置子图的标题
        ax.set_title(f"{icon_counts[icon]}次")

        ax.axis("off")
    plt.subplots_adjust(wspace=0.5, hspace=0.5)

    # 显示图形
    plt.show()


def activate_days(messages):
    counter = {}
    for msg in messages:
        date = msg.time.strftime("%Y-%m-%d")
        if date not in counter:
            counter[date] = 0
        counter[date] += 1
    return counter


def activate_days_rank(messages):

    senders = get_sender_list(messages)
    counter = {}
    start_time = datetime(2023, 2, 15)
    end_time = datetime(2024, 2, 15)
    date_list = [
        (start_time + timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range((end_time - start_time).days)
    ]
    for sender in senders:
        sender_messages = [msg for msg in messages if msg.sender == sender]
        days = activate_days(sender_messages)
        counter[sender] = [key for key in date_list if key not in days.keys()]
    counter = dict(sorted(counter.items(), key=lambda x: len(x[1])))
    print(counter)


def summary(messages):
    # 总消息次数
    total_count = len(messages)

    # 表情统计
    icon_counts = {}
    # 发言时间统计
    month_count = {}
    hour_count = {}
    weekday_count = {}

    for msg in messages:
        month = msg.time.strftime("%m")
        if month not in month_count:
            month_count[month] = 0
        month_count[month] += 1

        hour = msg.time.strftime("%H")
        if hour not in hour_count:
            hour_count[hour] = 0
        hour_count[hour] += 1

        weekday = msg.time.strftime("%w")
        if weekday not in weekday_count:
            weekday_count[weekday] = 0
        weekday_count[weekday] += 1

    # 打印统计结果
    print(f"total count: {total_count}")
    print(f"text count: {len(text_list)}")
    print(f"image count: {len(image_list)}")
    print(f"voice count: {len(voice_list)}")
    print(f"video count: {len(vedio_list)}")
    print(f"icon count: {len(icon_list)}")
    print(f"location count: {len(location_list)}")
    print(f"hongbao count: {len(hongbao_list)}")
    print(f"revoke count: {len(revoke_list)}")
    print(f"plp count: {len(plp_list)}")

    plt.rcParams["font.sans-serif"] = ["SimHei"]  # 指定默认字体为黑体
    plt.rcParams["axes.unicode_minus"] = False  # 解决保存图像时负号'-'显示为方块的问题
    labels = [
        "文字消息",
        "图片消息",
        "表情消息",
        "语音消息",
        "视频消息",
        "位置消息",
        "红包消息",
        "撤回消息",
        "拍了拍消息",
    ]
    sizes = [
        len(text_list),
        len(image_list),
        len(icon_list),
        len(voice_list),
        len(vedio_list),
        len(location_list),
        len(hongbao_list),
        len(revoke_list),
        len(plp_list),
    ]
    colors = [
        "#87CEEB",
        "#20B2AA",
        "#FFDEAD",
        "#FFD700",
        "#FFA07A",
        "#00CED1",
        "#FF69B4",
        "#808080",
        "#FFC0CB",
    ]
    plt.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%")
    plt.axis("equal")
    plt.show()

    print(month_count)
    # 绘制月度图
    labels = [
        "1月",
        "2月",
        "3月",
        "4月",
        "5月",
        "6月",
        "7月",
        "8月",
        "9月",
        "10月",
        "11月",
        "12月",
    ]
    sizes = [month_count.get(f"{i:02}", 0) for i in range(1, 13)]
    plt.bar(labels, sizes)
    plt.show()

    print(hour_count)
    # 绘制小时图
    labels = [f"{i:02}" for i in range(24)]
    sizes = [hour_count.get(f"{i:02}", 0) for i in range(24)]
    plt.bar(labels, sizes)
    plt.show()

    print(weekday_count)
    # 绘制星期图
    labels = ["日", "一", "二", "三", "四", "五", "六"]
    sizes = [weekday_count.get(f"{i}", 0) for i in range(7)]
    plt.bar(labels, sizes)
    plt.show()

    top_icons(messages)


def loong_king(messages):
    counter = {}
    for msg in messages:
        if msg.sender not in counter:
            counter[msg.sender] = 0
        counter[msg.sender] += 1
    counter = dict(sorted(counter.items(), key=lambda x: x[1], reverse=True))
    print(counter)
    return counter


def word_freq(messages):
    # 统计词频
    import jieba
    from collections import Counter

    contents = [msg.content for msg in messages if msg.type == 1]
    text = "".join(contents)
    words = jieba.cut_for_search(text)
    counter = Counter([word for word in words if len(word) > 1])
    print(counter.most_common(100))


def get_sender_list(messages):
    senders = []
    for msg in messages:
        if msg.sender not in senders:
            senders.append(msg.sender)
    return senders


def personal_analysis(messages, sender):
    messages = [msg for msg in messages if msg.sender == sender]
    # word_freq(messages)
    # top_icons(messages)
    # sentiment_analysis(messages)
    sentense_freq(messages)


def personal_summary(messages):
    senders = get_sender_list(messages)
    for sender in senders:
        print(sender)
        personal_analysis(messages, sender)


messages = []

with open("来莫_utf8.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in tqdm.tqdm(reader):
        if row[4] != "1" and row[4] != "0":
            continue
        messages.append(Msg(row))

start_time = datetime(2023, 2, 15)
end_time = datetime(2024, 2, 15)

messages = [msg for msg in messages if start_time <= msg.time <= end_time]
# 消息类型统计
icon_list = []
image_list = []
text_list = []
voice_list = []
vedio_list = []
location_list = []
hongbao_list = []
revoke_list = []
plp_list = []

for msg in messages:
    if msg.type == 1:
        text_list.append(msg)
    if msg.type == 3:
        image_list.append(msg)
    if msg.type == 34:
        voice_list.append(msg)
    if msg.type == 43:
        vedio_list.append(msg)
    if msg.type == 47:
        icon_list.append(msg)
    if msg.type == 48:
        location_list.append(msg)
    if msg.type == 10000:
        if "撤回" in msg.content:
            revoke_list.append(msg)
            pattern = r'"(.+?)"撤回了一条消息'
            match = re.match(pattern, msg.content)
            if match:
                msg.sender = match.group(1)
            else:
                msg.sender = "Eric025"
        if "拍了拍" in msg.content:
            plp_list.append(msg)
            pattern = r'拍了拍"(.+?)"'
            match = re.match(pattern, msg.content)
            if match:
                msg.receiver = match.group(1)
            else:
                msg.receiver = "Eric025"
        if "收到红包" in msg.content:
            hongbao_list.append(msg)

# activate_days_rank(messages)

# personal_summary(messages)

# summary(messages)
# print(loong_king(messages))
# word_freq(messages)

keyword_list = ["农", "龙"]
exceptword_list = ["农学", "农业", "龙川", "龙船"]
guonan_list = ["脑婆", "老婆", "爱", "草", "卓艾", "怜爱", "恋爱", "链哎"]

user_msg_counter = loong_king(messages)

word_counter = key_word_counter(messages, guonan_list, [])

rate = {}
for sender in word_counter.keys():
    rate[sender] = word_counter[sender] / user_msg_counter[sender]
rate = dict(sorted(rate.items(), key=lambda x: x[1], reverse=True))
print(rate)
