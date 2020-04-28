from odoo import models, fields, api
import time
import http.client
import jwt
import ast
import json


class ResCompany(models.TransientModel):
    _name = 'zoom.adapter'

    def _get_user_id(self):
        self.user_id = self.env.company.user_id

    api_key = fields.Char()
    api_secret = fields.Char()
    status = fields.Char(readonly=True)
    user_id = fields.Char(compute=_get_user_id)

    def send_request(self, method, url, token, body):
        conn = http.client.HTTPSConnection("api.zoom.us")
        headers = {
            'authorization': f"Bearer {token}",
            'content-type': "application/json"
        }
        data = json.dumps(body)
        conn.request(method, f"/v2/{url}", headers=headers, body=data)
        res = conn.getresponse()
        return res

    def create_meeting(self, meeting):
        token = self.generate_jwt(self.env.company.api_key, self.env.company.api_secret)
        body = {
            'topic': meeting.name
        }
        res = self.send_request("POST", f"users/{self.env.company.user_id}/meetings", token, body)
        data = res.read().decode("UTF-8")
        print(data)

    def generate_jwt(self, key, secret):
        header = {"alg": "HS256", "typ": "JWT"}

        payload = {"iss": key, "exp": int(time.time() + 60)}

        token = jwt.encode(payload, secret, algorithm="HS256", headers=header)
        return token.decode("utf-8")