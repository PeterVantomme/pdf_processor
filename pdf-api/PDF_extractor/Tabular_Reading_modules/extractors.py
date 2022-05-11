import camelot
from ..Config import Paths as filepaths
import pandas as pd
import re
import numpy as np
import json

class Extractor():
    def __init__(self, doc_type, doc_name):
        self.doc_type = doc_type
        self.doc_name = doc_name

    def __transform_extraction(self):
        pass

    def __get_data(self):
        pass

    def get_json(self):
        pass

    def cleanup_document_location(self):
        import os
        os.remove(f"{filepaths.pdf_path.value}/{self.doc_name}")

class RCExtractor(Extractor):
    def __init__(self, doc_name):
        super().__init__("RC", doc_name)
        self.json_result = self.__transform_extraction()#automatically calls the extractor methods
        self.cleanup_document_location()

    def __transform_extraction(self):
        result = self.__get_data()
        result = self.__get_summary(result)
        return json.dumps(result)
    
    def __get_summary(self, result):
        df = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}",flavor='stream', split_text=True, table_areas=['30,650,350,500'])[0].df
        try:
            vat = re.findall("([0-9].+?.+)",df.iloc[0,0])[0]
            df = df.iloc[[3,4],:]
            pay_receive_string = re.search("Te betalen saldo|Terug te krijgen|Over te dragen saldo", df.iloc[0,1])[0]
            result["samenvatting"] = {"BTW-nummer":vat,
                        "ontbrekende aangiftes": 0 if "*****" in df.iloc[1,0] else df.iloc[1,0],
                        pay_receive_string: float(df.iloc[1,1].replace(".","").replace(",","."))}
        except IndexError:
            result["samenvatting"] = {}
            document = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}",flavor='stream',table_areas=['30,700,650,100'])
            data = document[0].df
            vat_nr = re.search(re.compile("([0-9].+?.+)"),data.loc[data.loc[:,0].str.contains("Registratienummer")][0].values[0])[0]
            result["samenvatting"]["BTW-nummer"] = vat_nr
            amount = data.loc[data[0].str.contains("TOTAAL")].values[0]
            if re.search("[0-9]?.[0-9]{0,3},[0-9]{0,2}",amount[0]) is not None:
                result["samenvatting"]["terug te geven"] = re.search("[0-9]?.[0-9]{0,3},[0-9]{0,2}",amount[0])[0].replace(".","").replace(",",".")
            elif re.search("[0-9]?.[0-9]{0,3},[0-9]{0,2}",amount[1]) is not None:
                result["samenvatting"]["over te dragen"] = re.search("[0-9]?.[0-9]{0,3},[0-9]{0,2}",amount[1])[0].replace(".","").replace(",",".")
            elif re.search("[0-9]?.[0-9]{0,3},[0-9]{0,2}",amount[2]) is not None:
                result["samenvatting"]["te betalen"] = re.search("[0-9]?.[0-9]{0,3},[0-9]{0,2}",amount[2])[0].replace(".","").replace(",",".")
        return result

    def __get_data(self):
        tables = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}", flavor='stream', split_text=True, table_areas=['0,550,620,30'])
        if tables[0].df.shape[1]==1:
            tables = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}", flavor='stream', split_text=True, table_areas=['0,500,620,30']) 
    
        table = tables[0]
        try:
            if table.shape[1] > 3:
                df_combined_temp = pd.DataFrame(pd.Series(table.df.iloc[:,:4].values.tolist()).str.join(","))
                df = table.df.copy().iloc[:,2:]
                df.loc[:,0] = df_combined_temp
                df = df.loc[:,[0,4,6]]
            else:
                df = table.df.copy()
        except KeyError:
            if table.shape[1] > 3:
                df_combined_temp = pd.DataFrame(pd.Series(table.df.iloc[:,:2].values.tolist()).str.join(","))
                df = table.df.copy().iloc[:,2:]
                df.loc[:,0] = df_combined_temp
                df = df.loc[:,[0,2,3]]
        
        detail_frame = self.__get_detail(df)
        situation_frame = self.__get_situations(df)
        formatted_data = self.__get_formatted_data(detail_frame, situation_frame)

        return formatted_data

    def __get_detail(self,df):
        details_information = [row for row in df.iloc[:,0] if re.match(re.compile("[A-Z]*[0-9].*[0-9]|[0-9]*\/"),row)]
        details = df.loc[df.loc[:,0].isin(details_information),:]
        details

        if details.shape[1] > 3:
            details[0] = details.loc[:,0].apply(lambda x: x.replace(",","\n"))
            details[0] = details[0]+"\n"+details[2]
            details = details.drop([2,4],axis=1)
            details.columns = [0,1,2]

        elif details.shape[1] < 3:
            details[2] = details.loc[details.loc[:,0].str.contains("A|U"),1]
            details = details.assign(benef=lambda x: x.apply(lambda y:y[1] if y[2] is np.nan else "0,00", axis=1)).drop(1,axis=1)
            details = details.assign(owed= details[2].fillna("0,00")).drop(2,axis=1)
            details = details.loc[:,[0,"benef","owed"]]
        
        return details

    def __get_situations(self, df):
        situation_information = [row for row in df.iloc[:,0] if re.search(re.compile("TOESTAND|Toestand|Vorig saldo"),row)]
        situations = df.loc[df.loc[:,0].isin(situation_information),:]

        if situations.shape[1] < 3:
            situations = situations.assign(owed=lambda x: x[1].str.split("\n").apply(lambda y: y[1]))
            situations = situations.assign(benef=lambda x: x[1].str.split("\n").apply(lambda y: y[0]))
            situations.drop(1, axis=1, inplace=True)
            situations = situations.loc[:,[0,"benef","owed"]]

        elif situations.shape[1] > 3:
            situations[0] = situations.loc[:,0].apply(lambda x: x.replace(",","\n"))
            situations[0] = situations[0]+""+situations[2]
            situations = situations.drop([2,4],axis=1)
            situations.columns = [0,1,2]

        return situations

    def __get_formatted_data(self, details, situations):
        detail_d={}
        indexer = 0
        for row in details.values:
            indexer += 1
            detail_d[indexer] = {"Boekingsdatum":re.search(re.compile("[0-9]*\/[0-9]*\/[0-9]{4}"),row[0])[0],
                                "Onderwerp":re.search(re.compile("[A-Z]-[0-9]*.[0-9]{4}|[A-Z]"),row[0])[0],
                                "Uitwerkingsdatum":re.search(re.compile("[0-9]*\/[0-9]*\/[0-9]{4}"),row[0])[0].replace("\n",""),
                                "In uw voordeel":row[1].replace(".","").replace(",","."),
                                "Verschuldigd @FODF": row[2].replace(".","").replace(",","."),}
            date_of_last_balance = re.search(re.compile("[0-9]*\/[0-9]*\/[0-9]{4}"),situations.iloc[0,0].replace(",",""))[0]

        result = {}
        for row in situations.values:
            if pd.Series(row).str.contains("toestand", regex=True, case=False)[0]:
                    result[row[0].replace("\n"," ").replace(",","")]= {"In uw voordeel": row[1],
                                    "Verschuldigd @FODF": row[2]}   

        result[f"Vorig saldo op datum {date_of_last_balance}"] ={"In uw voordeel": situations.iloc[0,1],
                                                                "Verschuldigd @FODF": situations.iloc[0,2]}
                                        
        result["Details"] = detail_d
        return result

    def get_json(self):
        return self.json_result
        
class PBExtractor(Extractor):
    def __init__(self, doc_name):
        super().__init__("PB", doc_name)
        self.json_result = self.__transform_extraction()#automatically calls the extractor methods
        self.cleanup_document_location()
    
    def __transform_extraction(self):
        complete_info = json.dumps({"klantinfo":self.__get_customer_info(),"aanslagbiljet":self.__get_data()})
        return complete_info
    
    def __get_customer_info(self):
        customer_info_table = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}", flavor='stream', split_text=True,table_areas=['250,775,620,650'])
        info = customer_info_table[0]
        customer_info = [value[0] for value in info.df[2:].values]   
        return customer_info
    
    def __get_data(self):
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