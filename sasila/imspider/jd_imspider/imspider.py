#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import requests
from sasila.downloader.web_driver_pool import get_web_driver_pool
from Queue import Queue
from selenium import webdriver
from sasila.utils import logger
import time
from bs4 import BeautifulSoup as bs
import json
import requests

reload(sys)
sys.setdefaultencoding('utf-8')


def abstract(text, start, end):
    if text is None or text == '':
        return ''
    res = ''
    if start is not None and start != '':
        if start not in text:
            return res
        else:
            text = text[text.index(start) + len(start):]
    if end is not None and end != '':
        if end not in text:
            return res
        else:
            res = text[0:text.index(end)]
    else:
        res = text
    return res


class JdMessage(object):
    def __init__(self):
        self.has_login = False
        self.login_success = False
        self.success_cookies = None
        self.need_sms_captch = False
        self.message = ""
        self.qr_captcha = None
        self.qr_cookies = None


class JdImSpider(object):
    def __init__(self):
        self.web_driver_pool = None  # type:  Queue

    def init_pool(self):
        logger.info('init web driver pool...')
        self.web_driver_pool = get_web_driver_pool(1)
        logger.info('init web driver pool success...')

    def login(self, account, password, cookie):
        message = JdMessage()

        web = self.web_driver_pool.get()  # type: webdriver.PhantomJS
        web.delete_all_cookies()
        if self._validate_login(cookie):
            web.get("https://passport.jd.com/new/login.aspx?ReturnUrl=http%3A%2F%2Fhome.jd.com%2F")
            element = web.find_element_by_css_selector("div.login-tab.login-tab-r").find_element_by_css_selector("a")
            element.click()
            element = web.find_element_by_id("loginname")
            element.clear()
            element.send_keys(account)
            element = web.find_element_by_id("nloginpwd")
            element.clear()
            element.send_keys(password)
            element = web.find_element_by_css_selector("a#loginsubmit")
            element.click()
            time.sleep(5)

            if '我的京东' in bs(web.execute_script("return document.documentElement.outerHTML")).title.string:
                cookie = web.get_cookies()
                result = json.dumps(cookie).decode('unicode-escape')
                message.login_success = True
                message.message = '登录成功'
            else:
                # 需要手机验证码
                if True:
                    message.need_sms_captch = True
                    message.message = '需要手机验证码'
                if True:
                    message.message = '登录失败：' + '原因'
        else:
            message.has_login = True
            message.message = '已经登录'

        self.web_driver_pool.put(web)
        return message

    def _validate_login(self, cookie):
        if not cookie:
            return True
        cookies = json.loads(cookie)
        cookie_dict = dict()
        for c in cookies:
            cookie_dict[c['name']] = c['value']
        headers = dict()
        headers[
            "User-Agent"] = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36"
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        headers["Accept-Encoding"] = "gzip, deflate, sdch"
        headers["Accept-Language"] = "zh-CN,zh;q=0.8"
        session = requests.Session()
        response = session.get("https://home.jd.com/", cookies=cookie_dict, headers=headers)

        # for c in cookies:
        #     web.add_cookie({k: c[k] for k in ('name', 'value', 'domain', 'path', 'expiry') if k in c})
        # web.get("https://home.jd.com/")
        # web.execute_script("return document.documentElement.outerHTML")

        if '我的京东' in bs(response.text).title.string:
            return False
        else:
            return True

    def qr_login(self):
        message = JdMessage()
        headers = dict()
        headers[
            "User-Agent"] = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36"
        headers["Accept"] = "*/*"
        headers["Accept-Encoding"] = "gzip, deflate"
        headers["Accept-Language"] = "zh-CN,en,*"
        headers["Referer"] = "https://passport.jd.com/new/login.aspx?ReturnUrl=http%3A%2F%2Fhome.jd.com%2F"
        session = requests.Session()
        response = session.get("https://qr.m.jd.com/show?appid=133&size=147&t=1486614526653")
        message.qr_captcha = response.content
        message.qr_cookies = session.cookies.get_dict()
        return message

    def submit_qrlogin(self, cookie_dict):
        message = JdMessage()
        headers = dict()
        headers[
            "User-Agent"] = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36"
        headers["Accept"] = "*/*"
        headers["Accept-Encoding"] = "gzip, deflate"
        headers["Accept-Language"] = "zh-CN,en,*"
        headers["Referer"] = "https://passport.jd.com/new/login.aspx?ReturnUrl=http%3A%2F%2Fhome.jd.com%2F"
        session = requests.Session()

        response = session.get("https://qr.m.jd.com/check?callback=jQuery6172296&appid=133&_=1486609849337",
                               cookies=json.loads(cookie_dict),
                               headers=headers)

        ticket = abstract(response.content, '\"ticket\" : \"', '\"')
        print ticket

        headers['X-Requested-With'] = 'XMLHttpRequest'
        response = session.get("https://passport.jd.com/uc/qrCodeTicketValidation?t=" + ticket, headers=headers)

        return response.headers
