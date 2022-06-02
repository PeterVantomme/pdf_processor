from .Reading_modules.extractors import RCExtractor, PBExtractor, AkteExtractor, VBExtractor
from .Reading_modules.ocr import OCR_Reader
from .QR_modules.Transform_Data import transform_file, transform_image
from .QR_modules.QR_Interpreter_ZBAR import read_file
import json, os
from .Config import Paths

# Checks filetype and returns the correct extractor. Filetype is provided by the URL iteself.
class ExtractorController:
    def assign_to_extractor(self, doc_name, filetype):
        filetype = filetype.lower().strip()
        if filetype in ["rekening courant", "rc", "compte courant"]:
            extractor = RCExtractor(doc_name)
        elif filetype in ["pb","personenbelasting","impôt sur le revenu","impôt"]:
            extractor = PBExtractor(doc_name)
        elif filetype in ["vb","vennootschapsbelasting"]:
            extractor = VBExtractor(doc_name)
        elif filetype in ["akte","acte", "ak"]:
            extractor = AkteExtractor(doc_name)
        else:
            return "Filetype not supported \n Supported filetypes URI's: /rc, /pb, /ak, /vb"
        return extractor.get_json()

class OCRController:
    def convert(doc_name):
        return OCR_Reader(doc_name).is_succeeded()

# Controls execution of QR-reader. First interpret, if it fails, try to transform and interpret again.
class QRController:
    def get_qr_from_document(self,doc_name):
        try:
            image = transform_file(doc_name)
            output = self.__interpret(image)
        except IndexError:
            output = self.__interpret(transform_image(image))
        self.__remove_oldest_file() if len(os.listdir(Paths.pdf_path.value)) > 25 else None
        return self.__structure_data(output, doc_name)

    # Removes oldest file in documents folder when 25 files are saved. This is to save disk space.
    def __remove_oldest_file(self):
        list_of_files = os.listdir(Paths.pdf_path.value)
        full_path = [Paths.pdf_path.value+"/{0}".format(x) for x in list_of_files]
        oldest_file = min(full_path, key=os.path.getctime)
        os.remove(oldest_file)

    def __interpret(self,image):
        return read_file(image) #Returns QR code
    
    def __structure_data(self,data, doc_name):
        data = json.dumps({"filename":doc_name,
                           "data": f"{data}"})
        return data