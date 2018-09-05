from requests import post
files = {'file': open('python.pdf', 'rb')}

r = post("http://localhost:8000/file/", files = files)
print(r.status_code)
print(r.text)