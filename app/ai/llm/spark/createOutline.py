# -*- coding:utf-8 -*-
import hashlib
import hmac
import base64
import json
import time

import requests


class createOutline():

    def __init__(self, APPId, APISecret, Text):
        self.APPid = APPId
        self.APISecret = APISecret
        self.text = Text
        self.header = {}

    # 获取签名
    def get_signature(self, ts):
        try:
            # 对app_id和时间戳进行MD5加密
            auth = self.md5(self.APPid + str(ts))
            # 使用HMAC-SHA1算法对加密后的字符串进行加密
            return self.hmac_sha1_encrypt(auth, self.APISecret)
        except Exception as e:
            print(e)
            return None

    def hmac_sha1_encrypt(self, encrypt_text, encrypt_key):
        # 使用HMAC-SHA1算法对文本进行加密，并将结果转换为Base64编码
        return base64.b64encode(
            hmac.new(encrypt_key.encode('utf-8'), encrypt_text.encode('utf-8'), hashlib.sha1).digest()).decode('utf-8')

    def md5(self, text):
        # 对文本进行MD5加密，并返回加密后的十六进制字符串
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    # 创建大纲生成任务
    def create_task(self):
        url = 'https://zwapi.xfyun.cn/api/aippt/createOutline'
        timestamp = int(time.time())
        signature = self.get_signature(timestamp)
        body = self.getbody(self.text)

        headers = {
            "appId": self.APPid,
            "timestamp": str(timestamp),
            "signature": signature,
            "Content-Type": "application/json; charset=utf-8"
        }
        self.header = headers
        response = requests.request("POST", url=url, data=json.dumps(body), headers=headers).text
        resp = json.loads(response)
        print(resp)


    # 构建请求body体
    def getbody(self, text):
        body = {
            "query": text,
            "is_figure":True
        }
        return body

if __name__ == '__main__':
    # 控制台获取
    APPId = "xxxxxxxxxxxxx"
    APISecret = "xxxxxxxxxxxxxxxxxxxxxxxx"

    # 创建大纲生成任务  （仅生成大纲，需要调用5、通过sid和修改后大纲生成PPT 或 6、通过大纲生成PPT的接口 来创建ppt生成任务）
    Text = "集团客户部2023年工作总结"
    demo = createOutline(APPId, APISecret, Text)
    demo.create_task()






