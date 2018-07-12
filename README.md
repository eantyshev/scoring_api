# scoring_api

An ultimate HTTP server serving "scoring API", with operational Redis cache
(
"online_score": uses Redis as a cache, able to perform w/o one,
"clients_interests": gets information from Redis, fails if no record for a given client_id
)

## Basic usage:
```
$ python api.py &
```
(starts listening on localhost:8080)
clients_interests method:
```
$ curl -X POST  -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", "arguments": {"client_ids": [1001,1002]}}' http://127.0.0.1:8080/method
```
online_score
stdout:
```
{"code": 200, "response": {"1001": ["horses", "jogging", "kkjhkk"]}}
```

online_score method:
```
$ curl -X POST  -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", "arguments": {"first_name": "Евгений", "last_name": "qqev", "email": "wre@hgf"}}' http://127.0.0.1:8080/method
```
stdout:
```
{"code": 200, "response": {"score": 2.0}}
```

## Tests
to run unit tests:
```
$ python tests/unit/test.py
```

to run functional tests (redis server on 6379 is required):
```
$ python tests/functional/test.py
```
