from .extractors import RCExtractor
from .Transform_Data import transform_file
from .QR_Interpreter_ZBAR import read_file
import json

class ExtractorController:
    def assign_to_extractor(self,doc_name):
        return RCExtractor(doc_name).get_json() #result from extractor

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