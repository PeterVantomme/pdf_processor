from fpdf import FPDF
import fitz
import cv2
import os
import pytesseract
from ..Config import Paths as filepaths

class read_scanned_document():
    def __init__(self, doc_name):
        TOOLS = fitz.TOOLS
        filename = f"{filepaths.pdf_path.value}/{doc_name}"
        pdf_in = fitz.open(filename)
        pdf=FPDF()
        for i in range(len(pdf_in)):
            img = fitz.Pixmap(pdf_in, pdf_in.get_page_images(i)[0][0])
            img.save("temp_img_text.jpg")
            img = cv2.imread("temp_img_text.jpg")
            os.remove("temp_img_text.jpg")
            textstring = pytesseract.image_to_string(img).replace("\n"," ").replace("-","")
            pdf.add_page()
            pdf.set_font('Helvetica','',11)
            textstring = textstring.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0,10,textstring)
        pdf.output(filename,'F')
        del img
        TOOLS.store_shrink(101)
        self.succeeded = True
    
    def is_succeeded(self):
        return self.succeeded
        