import requests
url = 'http://127.0.0.1:5000/api/login'
resp = requests.post(url, json={'email':'pablito@gmail.com','password':'test'})
print('status', resp.status_code)
print('headers', resp.headers)
print('body', resp.text)
