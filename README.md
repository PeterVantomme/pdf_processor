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
- /extract/vb : accepts multipart form data with file & returns JSON with information about the document.
- /extract/ak : accepts multipart form data with file & returns JSON with information about the document.
- /qr : accepts multipart form data with file & returns decrypted message in qr-code and filename, make sure the first page contains the QR-code.
- /qr/{filename} : returns file with relevant pages.
- /cleanup : removes QR-files that weren't requested.
 
**All URI's besides register require an authorization header with Bearer {token}**
  
## Changelog:
23/05/2022
- Fixed memoryleak in QR-segment
- Added manual and notebooks.

19/05/2022:
- Fixed BUG where RC-extractor didnt't recognise more than two rows of the "Toestand" type.
- Added Cleanup URI functionality so user can remove unnecessary files.
- Reworked RC to work more efficiënt.
- Added exceptions.
- Added extractor for type "Vennootschapsbelasting".

18/05/2022: 
- Current version supports rc, pb and ak information extraction as well as QR-code reading.
- Secret key generated upon starting server.
- Nginx & Gunicorn WSGI as supporting reverse proxy & webserver.

## Used libraries:
- PyMuPDF for processing PDF documents
- PyTesseract for OCR on Extractors
- PyZBAR for reading QR-codes
- Camelot for detecting tables and extracting text
- OpenCV for transforming QR-image
- Django & Django REST Framework for API interface
- Numpy and Pandas for Array/DataFrame manipulation
