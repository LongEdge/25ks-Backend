# -*- coding:utf-8 -*-
import hashlib
import hmac
import base64
import json
import time
import random

import requests

from requests_toolbelt.multipart.encoder import MultipartEncoder


class createOutlineByDoc():

    def __init__(self, APPId, APISecret):
        self.APPid = APPId
        self.APISecret = APISecret
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

    # 创建任务生成任务
    def create_task(self):

        timestamp = int(time.time())
        signature = self.get_signature(timestamp)

        headers = {
            "appId": self.APPid,
            "timestamp": str(timestamp),
            "signature": signature,
            "Content-Type": "multipart/form-data; charset=utf-8"
        }

        #提交网络文件
        body = {
            "file_url": "https://openres.xfyun.cn/xfyundoc/2024-05-09/7f69a59d-ca21-4569-a295-14c02e3b0cf5/1715247028782/%E4%BD%9C%E6%96%87.txt",
            "file_name": "作文.txt",
        }
        data = MultipartEncoder(
            fields=body,
            boundary='------------------' + str(random.randint(1e28, 1e29 - 1))
        )

        # 提交本地文件
        # params = {
        #     "file_url": "",
        #     "file_name": "作文.txt",  # 文件名, 带文件名后缀
        #     "file": (
        #         '作文.txt.docx', open('作文.txt', 'rb'),
        #         'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        # }
        # data = MultipartEncoder(fields=params)


        headers['Content-Type'] = data.content_type
        url = 'https://zwapi.xfyun.cn/api/aippt/createOutlineByDoc'
        self.header = headers
        response =requests.post(url=url, data=data, headers=headers).text
        resp = json.loads(response)
        print(resp)


if __name__ == '__main__':
    # 控制台获取
    APPId = "xxxxxxxxxxxx"
    APISecret = "xxxxxxxxxxxxxxxxxxxxxxxxxxxx"

    # 自定义大纲生成任务（仅生成大纲，需要调用5、通过sid和修改后大纲生成PPT 或 6、通过大纲生成PPT的接口 来创建ppt生成任务）
    demo = createOutlineByDoc(APPId, APISecret)
    result = demo.create_task()

