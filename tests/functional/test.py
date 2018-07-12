# coding: utf-8

import os
import unittest

import datetime
import logging
from logging import debug, info, error
from subprocess import Popen, PIPE, STDOUT
import urllib2
import hashlib
import json
import sys
import time

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(PROJECT_ROOT)
import api
import store

URL = "http://localhost:8080/method"
CLIENTS_INTERESTS = {"1001": ['int1', 'int2'],
                     "1002": ['int3', 'int4']}


def setup_store():
    s = store.Store()
    for uid, value in CLIENTS_INTERESTS.items():
        s.cache_set("i:%s" % uid, value, 60 * 60)


def wait_until(func_true, timeout=5, period=1):
    time_start = time.time()
    while time.time() < time_start + timeout:
        if func_true():
            return
        debug("waiting for %d sec...", period)
        time.sleep(period)
    raise Exception("Timeout after %d sec" % period * timeout)


def process_listens(pid, port=8080):
    ports_info = (
        Popen("netstat -anpt", shell=True, stdout=PIPE, stderr=STDOUT)
            .stdout.readlines()
    )
    for ln in ports_info:
        cols = ln.split()
        if cols[-1] == "%d/python" % pid:
            return "127.0.0.1:%d" % port in cols
    else:
        return False


def set_valid_auth(request):
    if request.get("login") == api.ADMIN_LOGIN:
        request["token"] = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).hexdigest()
    else:
        msg = request.get("account", "") + request.get("login", "") + api.SALT
        request["token"] = hashlib.sha512(msg).hexdigest()


class FunctionalTest(unittest.TestCase):
    _popen = None

    @classmethod
    def setUpClass(cls):
        setup_store()
        cls._popen = Popen(["/usr/bin/python", "api.py"])
        pid = cls._popen.pid
        debug("Started server process pid = %d, wait for port open", pid)
        wait_until(lambda: process_listens(pid))

    @classmethod
    def tearDownClass(cls):
        debug("killing test server...")
        cls._popen.terminate()
        cls._popen.wait()

    def test_clients_interests(self):
        request = {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "clients_interests",
            "arguments": {"client_ids": [1001, 1002]}
        }
        set_valid_auth(request)
        f_http = urllib2.urlopen(URL, data=json.dumps(request))
        self.assertEqual(f_http.code, 200)
        result = json.load(f_http)
        self.assertEqual(
            result["response"],
            CLIENTS_INTERESTS
        )

    def test_online_score(self):
        request = {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "online_score",
            "arguments": {"first_name": u"Йцук",
                          "last_name": u"Фыва"}
        }
        set_valid_auth(request)
        f_http = urllib2.urlopen(URL, data=json.dumps(request))
        self.assertEqual(f_http.code, 200)
        result = json.load(f_http)
        self.assertEqual(
            result["response"],
            {'score': 0.5}
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')
    unittest.main()
