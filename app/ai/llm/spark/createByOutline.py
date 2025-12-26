# -*- coding:utf-8 -*-
import hashlib
import hmac
import base64
import json
import time

import requests





class createByOutline():

    def __init__(self, APPId, APISecret, Text, outline):
        self.APPid = APPId
        self.APISecret = APISecret
        self.text = Text
        self.outline = outline
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

    # 创建PPT生成任务
    def create_task(self):

        timestamp = int(time.time())
        signature = self.get_signature(timestamp)


        headers = {
            "appId": self.APPid,
            "timestamp": str(timestamp),
            "signature": signature,
            "Content-Type": "application/json; charset=utf-8"
        }
        self.header = headers

        body = {
            "query": self.text,
            "outline": self.outline
        }
        url = 'https://zwapi.xfyun.cn/api/aippt/createByOutline'
        response = requests.request("POST", url=url, json=body, headers=headers).text
        resp = json.loads(response)
        print(resp)
        if 0 == resp['code']:
            print('创建PPT任务成功')
            return resp['data']['sid']
        else:
            print('创建PPT任务失败')
            return None

        # 轮询任务进度，返回完整响应信息

    def get_process(self, sid):
        print("sid:" + sid)
        print(self.header)
        if (None != sid):
            response = requests.request("GET", url=f"https://zwapi.xfyun.cn/api/aippt/progress?sid={sid}",
                                        headers=self.header).text
            print(response)
            return response
        else:
            return None

        # 获取PPT，以下载连接形式返回

    def get_result(self):

        # 创建PPT生成任务
        task_id = self.create_task()
        # PPTurl = ''
        # 轮询任务进度
        while (True):
            time.sleep(1)
            response = self.get_process(task_id)
            resp = json.loads(response)
            process = resp['data']['process']
            if (process == 100):
                PPTurl = resp['data']['pptUrl']
                break
        return PPTurl



if __name__ == '__main__':
    # 控制台获取
    APPId = "xxxxxxxx"
    APISecret = "xxxxxxxxxxxxxxxxxxxxxxxx"

    # PPT生成（直接根据用户输入要求，获得最终PPT）
    Text = "集团客户部2023年工作总结"
    # 自定义大纲示例
    outline = '''
    {"id":Null,"title":"集团客户部通过建立稳固客户关系，成功拓展业务并提升项目执行效率。跨部门协作流畅，确保服务与支持的高标准。深入的市场洞察助力定制化解决方案，强化了集团的市场竞争","subTitle":"全面总结与展望客户关系发展","chapters":[{"id":Null,"chapterTitle":"2023年工作回顾","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":[{"id":Null,"chapterTitle":"关键项目推进情况","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":null},{"id":Null,"chapterTitle":"客户满意度分析","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":null},{"id":Null,"chapterTitle":"部门内部建设进展","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":null}]},{"id":Null,"chapterTitle":"客户关系管理成果","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":[{"id":Null,"chapterTitle":"客户满意度提升","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":null},{"id":Null,"chapterTitle":"关键客户维护策略","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":null},{"id":Null,"chapterTitle":"长期合作项目回顾","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":null}]},{"id":Null,"chapterTitle":"重点项目推进情况","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":[{"id":Null,"chapterTitle":"项目一的完成情况","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":null},{"id":Null,"chapterTitle":"项目二的实施过程","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":null},{"id":Null,"chapterTitle":"内部交流与知识共享","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":null}]},{"id":Null,"chapterTitle":"面临的挑战与对策","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":[{"id":Null,"chapterTitle":"市场竞争加剧分析","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":null},{"id":Null,"chapterTitle":"客户需求变化应对","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":null},{"id":Null,"chapterTitle":"内部管理优化策略","fileUrl":"","fileType":0,"chartFlag":false,"searchFlag":false,"chapterContents":null}]}],"fileUrl":"","fileType":0,"end":"","fileId":null}
    '''

    demo = createByOutline(APPId, APISecret, Text ,outline)
    result = demo.get_result()



    #print("生成的PPT请从此地址获取：\n" + result)





