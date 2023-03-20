import requests
import json
def post_wechat(filename):
    headers = {
        "Content-Type": "application/json; charset=UTF-8"
    }
    url = "https://wxpusher.zjiecode.com/api/send/message"
    pyload = {
        "appToken": "AT_BA8E2Mfd8vRwuiWlbnAMQnx20EaFwgdp",
        "content": "http://test.luckytnt.top:8881/map/" + filename + ".jpg",
        "summary": "消息摘要",
        # 消息摘要，显示在微信聊天页面或者模版消息卡片上，限制长度100，可以不传，不传默认截取content前面的内容。
        "contentType": 2,
        # 内容类型 1表示文字  2表示html(只发送body标签内部的数据即可，不包括body标签) 3表示markdown
        "topicIds": [
            # 发送目标的topicId，是一个数组！！！，也就是群发，使用uids单发的时候， 可以不传。
        ],
        "uids": [
            # 发送目标的UID，是一个数组。注意uids和topicIds可以同时填写，也可以只填写一个。
            "UID_E0zrUrJZVMMQvglmg6VRys376cqo"
        ],
        "url": "http://test.luckytnt.top:8881/map/" + filename + ".jpg",
        # //原文链接，可选参数
        "verifyPay": False
        # 是否验证订阅时间，true表示只推送给付费订阅用户，false表示推送的时候，不验证付费，不验证用户订阅到期时间，用户订阅过期了，也能收到。
    }

    response = requests.post(url, data=json.dumps(pyload), headers=headers).text