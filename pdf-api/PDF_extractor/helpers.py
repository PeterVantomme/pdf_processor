from .Tabular_Reading_modules.extractors import RCExtractor, PBExtractor, AkteExtractor
from .QR_modules.Transform_Data import transform_file
from .QR_modules.QR_Interpreter_ZBAR import read_file
import json

class ExtractorController:
    def assign_to_extractor(self, doc_name, filetype):
        filetype = filetype.lower().strip()
        if filetype in ["rekening courant", "rc", "compte courant"]:
            extractor = RCExtractor(doc_name)
        elif filetype in ["pb","personenbelasting","impôt sur le revenu","impôt"]:
            extractor = PBExtractor(doc_name)
        elif filetype in ["akte","acte"]:
            extractor = AkteExtractor(doc_name)
        else:
            return "Filetype not supported"
        return extractor.get_json()

class QRController:
    def get_qr_from_document(self,doc_name):
        return self.__structure_data(self.__interpret(self.__transform(doc_name)), doc_name)

    def __transform(self,doc_name):
        return transform_file(doc_name) #Returns clean image

    def __interpret(self,image):
        return read_file(image) #Returns QR code
    
    def __structure_data(self,data, doc_name):
        data = json.dumps({"filename":doc_name,
                           "data": f"{data}"})
        return data