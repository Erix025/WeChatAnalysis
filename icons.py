import xml.etree.ElementTree as ET
import os
import requests
from PyQt5.QtGui import QPixmap
import threading
import re

lock = threading.Lock()


def get_emoji(xml_string, thumb=True, output_path="./") -> str:
    """供下载用"""
    try:
        emoji_info = parser_xml(xml_string)
        md5 = emoji_info["md5"]
        image_format = [".png", ".gif", ".jpeg"]
        for f in image_format:
            prefix = "th_" if thumb else ""
            file_path = os.path.join(output_path, prefix + md5 + f)
            if os.path.exists(file_path):
                return file_path
        url = emoji_info["thumburl"] if thumb else emoji_info["cdnurl"]
        if not url or url == "":
            url = get_emoji_url(md5, thumb)
        if type(url) == str and url != "":
            print("下载表情包ing:", url)
            emoji_path = download(url, output_path, md5, thumb)
            return emoji_path
        elif type(url) == bytes:
            image_format = get_image_format(url[:8])
            if image_format:
                if thumb:
                    output_path = os.path.join(
                        output_path, "th_" + md5 + "." + image_format
                    )
                else:
                    output_path = os.path.join(output_path, md5 + "." + image_format)
            else:
                output_path = os.path.join(output_path, md5)
            with open(output_path, "wb") as f:
                f.write(url)
            print("表情包数据库加载", output_path)
            return output_path
        else:
            print("！！！未知表情包数据，信息：", xml_string, emoji_info, url)
            output_path = os.path.join(output_path, "404.png")
            if not os.path.exists(output_path):
                QPixmap(":/icons/icons/404.png").save(output_path)
            return output_path
    except:
        output_path = os.path.join(output_path, "404.png")
        if not os.path.exists(output_path):
            QPixmap(":/icons/icons/404.png").save(output_path)
        return output_path


def parser_xml(xml_string):
    assert type(xml_string) == str
    # Parse the XML string
    try:
        root = ET.fromstring(xml_string)
    except:
        res = re.search("<msg>.*</msg>", xml_string)
        if res:
            xml_string = res.group()
        root = ET.fromstring(xml_string.replace("&", "&amp;"))
    emoji = root.find("./emoji")
    # Accessing attributes of the 'emoji' element
    fromusername = emoji.get("fromusername")
    tousername = emoji.get("tousername")
    md5 = emoji.get("md5")
    cdnurl = emoji.get("cdnurl")
    encrypturl = emoji.get("encrypturl")
    thumburl = emoji.get("thumburl")
    externurl = emoji.get("externurl")
    androidmd5 = emoji.get("androidmd5")
    width = emoji.get("width")
    height = emoji.get("height")
    return {
        "width": width,
        "height": height,
        "cdnurl": cdnurl,
        "thumburl": thumburl if thumburl else cdnurl,
        "md5": (md5 if md5 else androidmd5).lower(),
    }


def get_emoji_url(self, md5: str, thumb: bool) -> str | bytes:
    """供下载用，返回可能是url可能是bytes"""
    if thumb:
        sql = """
            select
                case
                    when thumburl is NULL or thumburl = '' then cdnurl
                    else thumburl
                end as selected_url
            from CustomEmotion
            where md5 = ?
        """
    else:
        sql = """
            select CDNUrl
            from CustomEmotion
            where md5 = ?
        """
    try:
        lock.acquire(True)
        self.cursor.execute(sql, [md5])
        return self.cursor.fetchone()[0]
    except:
        md5 = md5.upper()
        sql = f"""
            select {"Thumb" if thumb else "Data"}
            from EmotionItem
            where md5 = ?
        """
        self.cursor.execute(sql, [md5])
        res = self.cursor.fetchone()
        return res[0] if res else ""
    finally:
        lock.release()


def download(url, output_dir, name, thumb=False):
    resp = requests.get(url)
    byte = resp.content
    image_format = get_image_format(byte[:8])
    if image_format:
        if thumb:
            output_path = os.path.join(output_dir, "th_" + name + "." + image_format)
        else:
            output_path = os.path.join(output_dir, name + "." + image_format)
    else:
        output_path = os.path.join(output_dir, name)
    with open(output_path, "wb") as f:
        f.write(resp.content)
    return output_path


def get_image_format(header):
    # 定义图片格式的 magic numbers
    image_formats = {
        b"\xFF\xD8\xFF": "jpeg",
        b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A": "png",
        b"\x47\x49\x46": "gif",
        b"\x42\x4D": "bmp",
        # 添加其他图片格式的 magic numbers
    }
    # 判断文件的图片格式
    for magic_number, image_format in image_formats.items():
        if header.startswith(magic_number):
            return image_format
    # 如果无法识别格式，返回 None
    return None
