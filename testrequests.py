import requests
#print(requests.options('http://localhost:8000/upload/'))
print(requests.post('http://localhost:8000/upload/', data={'file': open('test_document_shifted.pdf', 'rb')}, headers={'Content-Type': "multipart/form-data; boundary=----WebKitFormBoundaryRJgudGEoNU7Xj6UV"}))
