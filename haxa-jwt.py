import jwt

secret = "d1d49162bb374c31b5be11aa72a8a190cd69dd6636c359015548d0ca41ac15ce"
payload = {"role": "admin", "iat": 1234567890, "exp": 9999999999}
token = jwt.encode(payload, secret, algorithm="HS256")
print(token)