import camelot, itertools
from .Config import Paths as filepaths
import numpy as np
import pandas as pd

class Extractor():
    def __init__(self, doc_type, doc_name):
        self.doc_type = doc_type
        self.doc_name = doc_name

    def extract_table(self):
        pass

    def extract_text(self):
        pass

    def transform_extraction(self):
        pass

    def cleanup_document_location(self):
        import os
        os.remove(f"{filepaths.pdf_path.value}/{self.doc_name}")

class RCExtractor(Extractor):
    def __init__(self, doc_name):
        super().__init__("RC", doc_name)
        df_detail = self.detail_extractor()
        df_summary, vat_number = self.summary_extractor()
        self.json_result = self.transform_extraction(df_detail, df_summary, vat_number)
        self.cleanup_document_location()

    def get_info_first_column(self, df, search_string, index=0):
        return [element for element in df.iloc[:,0].values if search_string in element][index]

    def get_info_other_column_based_on_first(self, df, search_string,col=0, row=0):
        str_first_col = self.get_info_first_column(df, search_string)
        contents = [element for element in df.values if str_first_col in element][0][col] #.iloc[:,:]
        if isinstance(contents,list):
            contents = '0.00' if "*****" in contents[0] else contents[row]
        if "*****" in contents:
            return '0.00'
        return contents

    def detail_extractor(self):
        '''
        This method allows you to extract the bottom table of the R/C document. (04/05/2022)
        '''
        table = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}", line_scale=100,flavor='lattice', split_text=True)[1]

        temp_list = list()
        maxLen = max(map(len, table.data))
        for row in table.data:
            row = [element for element in row if len(element) > 0]
            row = [element.split("\n") if '*' in element else element for element in row]
            row = list(itertools.chain(*row)) if isinstance(row[0], list) else row
            if len(row) < maxLen:
                row.extend(np.zeros([maxLen-len(row),0]))
            temp_list.append(row)

        df = pd.DataFrame(temp_list)
        return df

    def summary_extractor(self):
        import re
        data = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}", flavor='stream', split_text=True, table_areas=['30,650,350,500'])
        df = data[0].df
        vat_number = re.findall("([0-9].+?.+)",df.iloc[0,0])[0]
        df = df.iloc[[3,4],:]
        
        return df, vat_number

    def extract_text(self):
        pass #No text extraction required, primary data is in tables

    def transform_extraction(self, df_detail, df_summary, vat_number):
        #Makes a dictionary from data in the df's that were extracted
        import re
        import json
        check_value = lambda value: 0 if "*****" in value else float(value.replace(".","").replace(",",".")) 
        last_balance_dict = {"date":re.findall("([0-9].+?\/.+\/.+)",self.get_info_first_column(df_detail,"Vorig saldo op datum van"))[0],
                             "amount_to_receive":float(self.get_info_other_column_based_on_first(df_detail,"Vorig saldo op datum van",1).replace(".","").replace(",",".")),
                             "amount_to_pay":float(self.get_info_other_column_based_on_first(df_detail,"Vorig saldo op datum van",2).replace(".","").replace(",","."))}
        history_dict = {"date_since":re.findall("([0-9].+?\/.+\/.+)",self.get_info_first_column(df_detail,"Verrichtingen en saldi sinds"))[0]}

        for row in range(df_detail[0].str.contains('Toestand eind').value_counts()[True]):
            date = re.findall('([0-9].+?\/.+)',self.get_info_first_column(df_detail,'Toestand eind ',index=row))[0]
            history_dict[f"state_end {date}"] = {"amount_to_receive":float(self.get_info_other_column_based_on_first(df_detail,"Toestand eind",1,row).replace(".","").replace(",",".")), 
                                                 "amount_to_pay":float(self.get_info_other_column_based_on_first(df_detail,"Toestand eind",2,row).replace(".","").replace(",","."))}


        current = {"booking_date":df_detail.iloc[df_detail.shape[0]-1,0],
                   "subject":df_detail.iloc[df_detail.shape[0]-1,1],
                   "implementation_date":df_detail.iloc[df_detail.shape[0]-1,2],
                   "amount_to_receive":check_value(df_detail.iloc[df_detail.shape[0]-1,3]),
                   "amount_to_pay":0.00 if isinstance(df_detail.iloc[df_detail.shape[0]-1,4], np.ndarray) else check_value(df_detail.iloc[df_detail.shape[0]-1,4])}

        detail_dict = {"last_balance":last_balance_dict,
                       "history":history_dict,
                       "current":current}
        
        summary_dict = {"VAT":vat_number,
                        "missing_declarations": check_value(df_summary.iloc[1,0]),
                        "to_transfer/to_pay": check_value(df_summary.iloc[1,1])}
        
        complete = {"summary":summary_dict,
                    "detail":detail_dict}
        return json.dumps(complete)

    def get_json(self):
        return self.json_result
        