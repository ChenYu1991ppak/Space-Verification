import requests
from utils.encryption import generate_sign

# from config import UPLOAD_STATUS_URL, UPLOAD_URL, SAVE_PICTURE_INFO_URL, UPLOAD_CHECK_URL

from scipy.misc import toimage
import oss2

import binascii
import time
from PIL import Image
import numpy as np
import hashlib
import shutil

import os
import json

import asyncio

info_dir = "/mnt/info"

_MD5_SUFFIX = "geetest-diao-bao-le"


# ---------- CONFIG ---------- #
# OSS CN
ACCESS_KEY_ID = "LTAIEFgYaESBRo0M"
ACCESS_KEY_SECRET = "voZESq5cFNqLtoGJ3i4KU5fMqawYbY"
BUCKET_NAME = "sensebot"
ENDPOINT = "oss-cn-qingdao.aliyuncs.com"
# OSS NA
ACCESS_KEY_ID2 = "LTAIEFgYaESBRo0M"
ACCESS_KEY_SECRET2 = "voZESq5cFNqLtoGJ3i4KU5fMqawYbY"
BUCKET_NAME2 = "sensebot-na"
ENDPOINT2 = "oss-us-east-1.aliyuncs.com"

auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, ENDPOINT, BUCKET_NAME)
auth2 = oss2.Auth(ACCESS_KEY_ID2, ACCESS_KEY_SECRET2)
bucket2 = oss2.Bucket(auth2, ENDPOINT2, BUCKET_NAME2)

ONLINE = True

if ONLINE is True:
    # UPLOAD_STATUS_URL = ["http://114.215.28.11:8000/get_server_status", "http://122.226.180.213:8000/get_server_status", "http://123.138.241.101:8000/get_server_status"]
    # UPLOAD_CHECK_URL = ["http://114.215.28.11:8000/confirm_file", "http://122.226.180.213:8000/confirm_file", "http://123.138.241.101:8000/confirm_file"]
    # UPLOAD_URL = ["http://114.215.28.11:8000/upload", "http://122.226.180.213:8000/upload", "http://123.138.241.101:8000/upload"]
    # SAVE_PICTURE_INFO_URL = "http://118.190.239.206:8000/saver/clickpictureinfo"
    UPLOAD_STATUS_URL = ["http://114.215.28.11:8000/get_server_status"]
    UPLOAD_CHECK_URL = ["http://114.215.28.11:8000/confirm_file"]
    UPLOAD_URL = ["http://114.215.28.11:8000/upload"]
    SAVE_PICTURE_INFO_URL = "http://118.190.239.206:8000/saver/clickpictureinfo"
else:
    UPLOAD_STATUS_URL = ["http://10.0.0.10:8000/get_server_status"]
    UPLOAD_CHECK_URL = ["http://10.0.0.10:8000/confirm_file"]
    UPLOAD_URL = ["http://10.0.0.10:8000/upload"]
    SAVE_PICTURE_INFO_URL = "http://192.168.1.229:8010/saver/clickpictureinfo"

Mark = "2018.11.23"


class PictureInfo(object):

    def __init__(self, pic_type, lang="zh", level=1, mark=""):
        """ A structure, which can be delivered in queue, saving picture information """
        # related to picture
        self.name            = _make_name()        # picture name
        self.bg              = None                # original picture
        self.time            = time.time()         # time stamp of picture generation
        self.pic_type        = pic_type            # captcha type
        self.mark            = mark
        # related to captcha
        self.lang            = lang      # language of picture prompt
        self.level           = level     # the level of difficulty
        self.prompt_text     = None      # prompt of captcha
        self.ans_location    = None      # answer location. format: [[[x, y], [w, h]]]
        self.picture         = None      # final captcha picture after processed
        self.prompt          = None      # prompt picture which would be concatenate at bottom of captcha picture
        # about picture reinforcement
        self.source          = None      # normalized numpy matrix of picture
        self.style           = None      # style for style transfer
        self.valid           = True
        self.collection      = pic_type + "_" + "l" + str(level) + "_" + str(lang) + "_" + mark
        # self.collection      = pic_type

    def record(self):
        """ Return a dict with the picture infomation uploaded to database """

        result = {
            "name": self.name,
            "pic_type": self.pic_type,
            "path": os.path.join(self.collection, self.style),
            "path_v1": os.path.join(self.collection, self.style),
            "style": self.style,
            "lang": self.lang,
            "level": "l" + str(self.level),
            # "level": "l" + str(self.level + 1),
            "answer_text": self.prompt_text,
            "answer_location": self.ans_location,
            "collection": self.collection,
            "time": self.time,
            "wordlib": self.mark,
            "used": True
        }
        return result


def _make_name():
    s = str(time.time()) + _MD5_SUFFIX
    s = s.encode('utf-8')
    md5_obj = hashlib.md5()
    md5_obj.update(s)
    return md5_obj.hexdigest()+".jpg"

def _add_word_picture(output_picture, word_picture):
    w, h, t = output_picture.shape
    w_w, w_h, w_t = word_picture.shape
    picture = np.zeros(shape=(w + w_w, h, t), dtype=output_picture.dtype)
    picture[0:w, 0:h] = output_picture
    picture[w:w + w_w, 0:w_h] = word_picture
    return picture


# def wrap2pic_info(img_file, qa_file, lang="zh"):
# 	pic_info = PictureInfo(pic_type="space", lang="zh",mark=Mark)

# 	img = Image.open(img_file)
# 	pic_info.picture = np.asarray(img)
# 	pic_info.source = np.asarray(img)
# 	pic_info.prompt = np.zeros(shape=(40, 344, 3), dtype="uint8")
# 	pic_info.style = "space"
# 	pic_info.time = time.time()


def upload_sences(image_dir, qa_dir, lang="en"):
    q_s = 0
    # session = yield from create_session(loop)
    print(image_dir)
    for root, sub, files in os.walk(image_dir):

        print("total image %s" % len(files))
        for k, f in enumerate(files):
            #print(f)
            img_file = os.path.join(root, f)
            mark = f.split(".")[0]

            if lang == "zh":
                qa_file = os.path.join(qa_dir + "_zh", str(mark) + "_question.json")
            elif lang == "en":
                qa_file = os.path.join(qa_dir + "_en", str(mark) + "_question.json")
            else:
                raise Exception() 

            # info
            name = _make_name()
            pic_type = "space"
            style = "space"
            level = "l1"
            #lang = "zh"
            collection = pic_type + "_"  + str(level) + "_" + str(lang) + "_" + Mark

            # upload image
            img = Image.open(img_file).convert("RGB")
            picture = np.asarray(img)
            word_picture = np.zeros(shape=(40, 344, 3), dtype="uint8")
            picture = _add_word_picture(picture, word_picture)
            p = toimage(picture, mode="RGB")
            binary_pic = p.tobytes("jpeg", "RGB", 100)

            try:
                print(name)
                # upload to oss
                pic_path = os.path.join(collection, style, name)
                #bucket.put_object("nerualpic/%s" % pic_path, binary_pic)
                #bucket2.put_object("nerualpic/%s" % pic_path, binary_pic)
                # upload to server
                path = "%s" % os.path.join(collection, style)
                file_dict = {
            		"file": ("-".join((path, name)), binary_pic, "image/jpeg")
            	}
                #for upload_url in UPLOAD_URL:
                    #response = requests.post(upload_url, files=file_dict)
                    #response.close()

                #params = {"filename": "%s/%s" % (path, name)}
                #for upload_check_url in UPLOAD_CHECK_URL:
                    #response = requests.get(upload_check_url, params=params)
                    #text = response.text
                    #res = json.loads(text)["status"]
                    #if not res:
                        #raise Exception("upload fail:(%s, %s)" % (upload_check_url, str(params)))
                  
                with open(qa_file, 'r', encoding='utf-8') as j:
                    data = json.load(j)
                for ques in data["questions"]:
                    # print(ques)
                    save_pictures_info = []
                    q_s += 1
                    pic_info = PictureInfo("space", lang=lang, level=1, mark=Mark)
                    # print(pic_info.lang)
                    pic_info.name = name
                    pic_info.style = style
                    pic_info.prompt_text = ques["question"]

                    loc = (ques["loc"][0], ques["loc"][1])
                    wh = (ques["width"], ques["height"])
                    answer_loc = [[loc, wh]]
                    pic_info.ans_location = answer_loc
                    save_pictures_info.append(pic_info.record())
                    if q_s % 10 == 0:
                        print("%s: %s" % (lang, q_s))
                
                    questions_info = json.dumps(save_pictures_info)
                    # print(questions_info)
                    timestamp = str(time.time())
                    message = 'SB' + str(timestamp)
                    msg = message.encode('utf-8')
                    sign = binascii.b2a_hex(generate_sign(msg))
                    formdata = dict()
                    formdata["db"] = "gt_resources_v1"
                    formdata["timestamp"] = timestamp
                    formdata["sign"] = sign.decode()
                    formdata["picture_infos"] = questions_info
                    formdata["max"] = "200000"
                    #print("111")
                    #print(formdata)
                    #response = requests.post(SAVE_PICTURE_INFO_URL, data=formdata)
                    #print(list(response))
                    #text = response.text
                    #print(text)
                    #if text == "fail":
                        #print("save picture_info fail")
                    #response.close()
                    info_file = mark + "_info"
                    info_path = os.path.join("output/info", info_file)
                    with open(info_path, "a+", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

            except oss2.exceptions.OssError:
                # server_logger.warn("upload picture error")
                print("upload picture error")


if __name__ == "__main__":
    image_dir = "output/images"
    qa_dir = "output/questions"

    print(SAVE_PICTURE_INFO_URL)
    upload_sences(image_dir, qa_dir, lang="zh")
    # upload_sences(image_dir, qa_dir, lang="en")

