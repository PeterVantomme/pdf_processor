# pdf_processor v1
## Usage:
- Use docker-compose to start the application within a Docker environment
- Register a new user
- Login with the new user to get authentication token
- Now u can use the API freely

## URI's:
- /register : accepts multipart form data with password, password2, username and email.
- /token : accepts multipart form data with username and password.
- /refresh : accepts multipart form data with refresh.
- /user : shows data of current user.
- /user/change-password : accepts multipart form data with old_password and new_password.
- /extract/rc : accepts multipart form data with file & returns JSON with information about the document.
- /extract/pb : accepts multipart form data with file & returns JSON with information about the document.
- /extract/ak : accepts multipart form data with file & returns JSON with information about the document.
- /qr : accepts multipart form data with file & returns decrypted message in qr-code and filename, make sure the first page contains the QR-code.
- /qr/{filename} : returns file with relevant pages.
 
**All URI's besides register require an authorization header with Bearer {token}**
  
## Changelog:
18/05/2022: 
- Current version supports rc, pb and ak information extraction as well as QR-code reading.
- Secret key generated upon starting server.
- Nginx & Gunicorn WSGI as supporting reverse proxy & webserver

## Todo:
18/05/2022:
- Add exception messages.
