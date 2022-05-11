from .Tabular_Reading_modules.extractors import RCExtractor, PBExtractor
import camelot
from .QR_modules.Transform_Data import transform_file
from .QR_modules.QR_Interpreter_ZBAR import read_file
from .Config import Paths as filepaths
import pandas as pd
import json

class ExtractorController:
    def assign_to_extractor(self,doc_name):
        tables = camelot.read_pdf(f"{filepaths.pdf_path.value}/{doc_name}", flavor='stream', split_text=True, table_areas=['30,700,620,500'])
        table = tables[0].df
        table = pd.DataFrame(pd.Series(table.values.tolist()).str.join(""))
        if len(table.loc[table[0].str.contains("personenbelasting|aanslagbiljet",regex=True, case=False)]) >0:
            return PBExtractor(doc_name).get_json()
        elif len(table.loc[table[0].str.contains("Btw-rekeninguittreksel",regex=True, case=False)]) >0:
            return RCExtractor(doc_name).get_json()
        #TODO:catchen wanneer niets gevonden

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