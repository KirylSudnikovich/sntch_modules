from odoo import models, fields, api
import time
import http.client
import jwt
import ast


class ResCompany(models.Model):
    _inherit = 'res.company'

    api_key = fields.Char()
    api_secret = fields.Char()
    status = fields.Char(readonly=True)

    def check_zoom_creds(self):
        token = self.generate_jwt(self.api_key, self.api_secret)
        conn = http.client.HTTPSConnection("api.zoom.us")

        headers = {
            'authorization': f"Bearer {token}",
            'content-type': "application/json"
            }

        conn.request("GET", "/v2/users?status=active&page_size=30&page_number=1", headers=headers)
        res = conn.getresponse()
        if res.code == 200:
            self.status = "OK"
        else:
            data = res.read().decode("UTF-8")
            data = ast.literal_eval(data)
            self.status = data.get('message', 'Error')

    def generate_jwt(self, key, secret):
        header = {"alg": "HS256", "typ": "JWT"}

        payload = {"iss": key, "exp": int(time.time() + 3600)}

        token = jwt.encode(payload, secret, algorithm="HS256", headers=header)
        return token.decode("utf-8")