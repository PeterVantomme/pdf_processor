from fpdf import FPDF
import fitz
import cv2
import os
import pytesseract
from ..Config import Paths as filepaths

class OCR_Reader():
    def __init__(self, doc_name):
        self.succeeded = False
        TOOLS = fitz.TOOLS
        filename = f"{filepaths.pdf_path.value}/{doc_name}"
        self.__process_document(filename)
        TOOLS.store_shrink(101)
        self.succeeded = True
    
    def __process_document(self, filename):
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
        try:
            del img
        except UnboundLocalError:
            self.is_succeeded = False
            raise ReferenceError

    def is_succeeded(self):
        return self.succeeded
        