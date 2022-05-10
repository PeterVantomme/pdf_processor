import camelot
from ..Config import Paths as filepaths
import pandas as pd
import re
import json

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
        self.json_result = self.transform_extraction()#automatically calls the extractor methods
        self.cleanup_document_location()

    def detail_extractor(self):
        '''
        This method allows you to extract the bottom table of the R/C document. (04/05/2022)
        '''
        table = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}",flavor='stream', split_text=True, table_areas=['30,450,620,30'])[0]
        df = table.df
        rows = [row for row in df.values]
        return rows
        

    def get_details(self,rows):
        import re
        detail_pattern = re.compile('\d{2}\/\d{2}\/\d{4}\\n')
        detail = [line for line in rows if re.search(detail_pattern,line[0])]
        detail_date_code = [line[0].split("\n") for line in detail]
        detail_date_amounts = [line[1:] for line in detail]

        detail = {}
        for row in range(len(detail_date_code)):
            detail[f"Boekingsdatum {detail_date_code[row][0]}"] = {"Onderwerp":detail_date_code[row][1],
                                                                "Uitwerkingsdatum":detail_date_amounts[row][0],
                                                                "Bedrag in uw voordeel":0.00 if detail_date_amounts[row][1] == "" else detail_date_amounts[row][1],
                                                                "Bedrag verschuldigd @ FODF":0.00 if detail_date_amounts[row][2] == "" else detail_date_amounts[row][2]}

        return(detail)

    def get_conditions(self,rows):
        conditions = {}
        detail = [line for line in rows if "Toestand eind" in line[0]]
        for row in range(len(detail)):
            conditions[detail[row][0]] = {"Bedrag in uw voordeel": detail[row][2],
                                        "Bedrag verschuldigd @ FODF": detail[row][3]}

        return conditions

    def get_past_saldi(self,rows):
        saldi = {}
        detail = [line for line in rows if "Vorig saldo op datum van" in line[0]]
        for row in range(len(detail)):
            saldi[detail[row][0]] = {"Bedrag in uw voordeel": detail[row][2],
                                    "Bedrag verschuldigd @ FODF": detail[row][3]}
        return saldi
        

    def summary_extractor(self):
        data = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}", flavor='stream', split_text=True, table_areas=['30,650,350,500'])
        df = data[0].df
        vat_number = re.findall("([0-9].+?.+)",df.iloc[0,0])[0]
        df = df.iloc[[3,4],:]
        
        summary = {"VAT":vat_number,
                   "Ontbrekende aangifte(n)": 0 if "*****" in df.iloc[1,0] else df.iloc[1,0],
                   "Te betalen/te ontvangen saldo": float(df.iloc[1,1].replace(".","").replace(",","."))} #TODO zorgen dat de tekst te betalen/te ontvangen autom. overgenomen wordt.

        return summary

    def transform_extraction(self):
        rows = self.detail_extractor()
        complete = {"summary":self.summary_extractor(),
                    [line for line in rows if "Verrichtingen en saldi sinds" in line[0]][0][0]:{"saldiverleden":self.get_past_saldi(rows),
                                                                                                "toestanden sinds laatste saldi datum":self.get_conditions(rows),
                                                                                                "details":self.get_details(rows)}}
        return json.dumps(complete)
    
    def get_json(self):
        return self.json_result
        
class PBExtractor(Extractor):
    def __init__(self, doc_name):
        super().__init__("PB", doc_name)
        self.json_result = self.transform_extraction()#automatically calls the extractor methods
    
    def transform_extraction(self):
        complete_info = json.dumps({"klantinfo":self.get_customer_info(),"aanslagbiljet":self.get_data()})
        return complete_info
    
    def get_customer_info(self):
        customer_info_table = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}", flavor='stream', split_text=True,table_areas=['250,775,620,650'])
        info = customer_info_table[0]
        customer_info = [value[0] for value in info.df[2:].values]   
        return customer_info
    
    def get_data(self):
        data_table = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}", flavor='stream', table_areas=['50,500,620,400'])
        table = data_table[0].df
       
        table = pd.DataFrame(pd.Series(table.values.tolist()).str.join(""))
        table = pd.DataFrame(table[0]+table[1]) if table.shape[1]>1 else table

        #helper methods
        amount_to_pay_or_receive_by_index = float([row.split("€")[1].strip() for row in table.loc[:,0] if "€" in row][0].replace(".","").replace(",","."))

        aanslagbiljet_info = {}
        aanslagbiljet_info["Te betalen bedrag"] = amount_to_pay_or_receive_by_index
        try:
            aanslagbiljet_info["Rekeningnummer"] = re.search("[A-Z].[0-9].*[0-9]",table.loc[table.iloc[:,0].str.contains("rekeningnummer")].values[0][0].split("rekeningnummer: ")[1])[0]
            aanslagbiljet_info["Mededeling"] = re.split(":.",table.loc[table.iloc[:,0].str.contains("mededeling")].values[0][0])[1].strip()
            aanslagbiljet_info["Vervaldatum"] = re.search("[0-9].\/.*",table.loc[table.iloc[:,0].str.contains("ten laatste")].values[0][0])[0]
        except IndexError: #Aanslagbiljetten tem 2010
            try:
                aanslagbiljet_info["Rekeningnummer"] = re.search("[0-9].*-[0-9]*",table.loc[table.iloc[:,0].str.contains("rekeningnummer")].values[0][0].split("rekeningnummer")[1])[0]
                aanslagbiljet_info["Mededeling"]=0
                aanslagbiljet_info["Vervaldatum"] = re.search("[0-9].\/.*",table.loc[table.iloc[:,0].str.contains("ten laatste")].values[0][0])[0]
            except (TypeError,IndexError): #Bedrag ontvangen
                aanslagbiljet_info["Mededeling"]="Ontvangst"
                aanslagbiljet_info["Te ontvangen bedrag"] = amount_to_pay_or_receive_by_index
                del aanslagbiljet_info["Te betalen bedrag"]

        return aanslagbiljet_info
        
    def get_json(self):
        return self.json_result