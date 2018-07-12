# coding: utf-8

import os
import sys
import hashlib
import datetime
import functools
import mock
import json
import unittest
import traceback

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(PROJECT_ROOT)
import api


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def inner(self, *args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                try:
                    f(self, *new_args)
                except Exception as exc:
                    extra_msg = "test args: %s" % (new_args,)
                    exc.args += (extra_msg,)
                    raise

        return inner

    return decorator


class TestStore(object):
    def cache_set(self, key, val, ttl):
        pass

    def cache_get(self, key):
        return None

    def get(self, key):
        return ['interest1', 'interest2']


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.settings = TestStore()

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.settings)

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            request["token"] = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).hexdigest()
        else:
            msg = request.get("account", "") + request.get("login", "") + api.SALT
            request["token"] = hashlib.sha512(msg).hexdigest()

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}},
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    ])
    def test_bad_auth(self, request):
        _, code = self.get_response(request)
        self.assertEqual(api.FORBIDDEN, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
        {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
        {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
    ])
    def test_invalid_method_request(self, request):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertTrue(len(response))

    @cases([
        {},
        {"phone": "79175002040"},
        {"phone": "89175002040", "email": "stupnikov@otus.ru"},
        {"phone": "79175002040", "email": "stupnikovotus.ru"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": -1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": "1"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.1890"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "XXX"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000", "first_name": 1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "s", "last_name": 2},
        {"phone": "79175002040", "birthday": "01.01.2000", "first_name": "s"},
        {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
    ])
    def test_invalid_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @cases([
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ])
    def test_ok_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        score = response.get("score")
        self.assertTrue(isinstance(score, (int, float)) and score >= 0, arguments)
        self.assertEqual(sorted(self.context["has"]), sorted(arguments.keys()))

    def test_ok_score_admin_request(self):
        arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
        request = {"account": "horns&hoofs", "login": "admin", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)
        score = response.get("score")
        self.assertEqual(score, 42)

    @cases([
        {},
        {"date": "20.07.2017"},
        {"client_ids": [], "date": "20.07.2017"},
        {"client_ids": {1: 2}, "date": "20.07.2017"},
        {"client_ids": ["1", "2"], "date": "20.07.2017"},
        {"client_ids": [1, 2], "date": "XXX"},
    ])
    def test_invalid_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @cases([
        #{"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_ok_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        self.assertEqual(len(arguments["client_ids"]), len(response))
        self.assertTrue(all(v and isinstance(v, list) and all(isinstance(i, basestring) for i in v)
                            for v in response.values()))
        self.assertEqual(self.context.get("nclients"), len(arguments["client_ids"]))


class TestFields(unittest.TestCase):

    def _test_simple_positive(self, field_cls, value, result=None):
        assert not (value is None and result is not None)
        if not result:
            result = value
        d = field_cls()
        self.assertEqual(d.parse_validate(value), result)

    def _test_simple_negative(self, field_cls, value):
        d = field_cls()
        with self.assertRaises(api.ValidationError):
            d.parse_validate(value)

    @cases([
        ("09.07.2018", datetime.datetime(year=2018, month=7, day=9)),
        ("28.02.1950", datetime.datetime(year=1950, month=2, day=28)),
        ("1.3.2000", datetime.datetime(year=2000, month=3, day=1)),
    ])
    def test_date_positive(self, value, result):
        self._test_simple_positive(api.DateField, value, result)

    @cases([
        "12.o2.2018",
        "01.13.2000",
        "12.12.05",
        None
    ])
    def test_date_negative(self, value):
        self._test_simple_negative(api.DateField, value)

    @cases([
        ("09.07.2018", datetime.datetime(year=2018, month=7, day=9)),
        ("09.07.1985", datetime.datetime(year=1985, month=7, day=9)),
    ])
    def test_birthday_positive(self, value, result):
        self._test_simple_positive(api.BirthDayField, value, result)

    @cases([
        "12.02.1900",
        "01.12.2040",
        "01.13.2010", # to ensure DateField validation has effect here
        None
    ])
    def test_birthday_negative(self, value):
        self._test_simple_negative(api.BirthDayField, value)

    @cases(["simple", "http://ww.af.ru", u"йцукен123", "{}[]<>?!&^%#$|", ""])
    def test_char_positive(self, value):
        self._test_simple_positive(api.CharField, value)

    @cases([None, {}, bytearray("asdf")])
    def test_char_negative(self, value):
        self._test_simple_negative(api.CharField, value)

    @cases([{}, {1: "1234", 2: {}, "123": None}])
    def test_arguments_positive(self, value):
        self._test_simple_positive(api.ArgumentsField, value)

    @cases([None, [], "{}"])
    def test_arguments_negative(self, value):
        self._test_simple_negative(api.ArgumentsField, value)

    @cases(["simple_1@mail.com", u"1234@143.рф"])
    def test_email_positive(self, value):
        self._test_simple_positive(api.EmailField, value)

    @cases([None, "http://wew.asdf.ru"])
    def test_email_negative(self, value):
        self._test_simple_negative(api.EmailField, value)

    @cases(["71234567890", 70001112233, u"70001113333"])
    def test_phone_positive(self, value):
        self._test_simple_positive(api.PhoneField, value, str(value))

    @cases([None, 7098, "7999111554409", "90001112233", "9876543210u"])
    def test_phone_negative(self, value):
        self._test_simple_negative(api.PhoneField, value)

    @cases([0, 1, 2])
    def test_gender_positive(self, value):
        self._test_simple_positive(api.GenderField, value)

    @cases([None, -1, 1.1, "2"])
    def test_gender_negative(self, value):
        self._test_simple_negative(api.GenderField, value)

if __name__ == "__main__":
    unittest.main()
