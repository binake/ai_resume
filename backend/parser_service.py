import sys
import base64
import requests
import urllib3
import json
import uuid
import hmac
import hashlib
from datetime import datetime

class ResumeParserService:
    def __init__(self, url, secret_id, secret_key):
        self.url = 'https://ap-beijing.cloudmarket-apigw.com/service-9wsy8usn/ResumeParser'
        self.secret_id = "RrIawnDnCs4ha4hs"
        self.secret_key = "JQSIHcT3xjgVAD1p33kvcn3I6KG4TcrB"

    def create_headers(self):
        date_time = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        sign_str = f"x-date: {date_time}"
        sign = base64.b64encode(hmac.new(self.secret_key.encode('utf-8'), sign_str.encode('utf-8'), hashlib.sha1).digest())
        auth = json.dumps({
            "id": self.secret_id,
            "x-date": date_time,
            "signature": sign.decode('utf-8')
        })
        headers = {
            'request-id': str(uuid.uuid1()),
            'Authorization': auth,
            "Content-Type": "application/json; charset=utf-8"
        }
        return headers

    def parse(self, file_path, need_avatar=1):
        with open(file_path, 'rb') as f:
            cont = f.read()
        base_cont = base64.b64encode(cont)
        if sys.version.startswith('3'):
            base_cont = base_cont.decode('utf-8')
        data = {
            'file_name': file_path.split('/')[-1],
            'file_cont': base_cont,
            'need_avatar': need_avatar
        }
        headers = self.create_headers()
        res = requests.post(self.url, data=json.dumps(data), headers=headers)
        if res.status_code != 200:
            return {'error': f'HTTP {res.status_code}', 'detail': res.text}
        try:
            return json.loads(res.text)
        except Exception as e:
            return {'error': 'parse json failed', 'detail': str(e), 'raw': res.text} 