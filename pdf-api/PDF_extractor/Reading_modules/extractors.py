import json
import os
import re
import camelot
import cv2
import fitz
import numpy as np
import pandas as pd
import pytesseract

from ..Config import Paths as filepaths

# Superclass (partially abstract)
# Used for all extractors and contains basic methods required for all extractors.
# This also creates structure in how extractors are built.
class Extractor():
    def __init__(self, doc_type, doc_name):
        self.doc_type = doc_type
        self.doc_name = doc_name

    def __transform_extraction(self):
        pass

    def __get_data(self):
        pass

    def __get_detail(self):
        pass

    def get_json(self):
        return self.json_result

    def cleanup_document_location(self):
        os.remove(f"{filepaths.pdf_path.value}/{self.doc_name}")

# Extractor superclass for reading all PDF-documents for tax (PB & VB)
# Contains shared methods
class BelastingExtractor(Extractor):
    def __init__(self, doc_type, doc_name):
        super().__init__(doc_type, doc_name)

    def get_customer_info(self):
        customer_info_table = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}", flavor='stream', split_text=True,table_areas=['250,775,620,650'])
        info = customer_info_table[0]
        customer_info = [value[0] for value in info.df[2:].values]   
        return customer_info

    def get_data(self, type):
        if type == "VENNOOTSCHAP":
            vervaldatum_regex = re.compile("[0-9].\..*")
        else:
            vervaldatum_regex = re.compile("[0-9].\\.*")
        data_table = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}", flavor='stream', table_areas=['50,500,620,400'])
        table = data_table[0].df
        aanslagbiljet_info = {}
        table = pd.DataFrame(pd.Series(table.values.tolist()).str.join(""))
        #helper methods
        amount_to_pay_or_receive_by_index = float([row.split("€")[1].strip() for row in table.loc[:,0] if "€" in row][0].replace(".","").replace(",","."))
        aanslagbiljet_info["Te betalen bedrag"] = amount_to_pay_or_receive_by_index
        try:
            aanslagbiljet_info["Rekeningnummer"] = re.search("[A-Z].[0-9].*[0-9]",table.loc[table.iloc[:,0].str.contains("rekeningnummer")].values[0][0].split("rekeningnummer: ")[1])[0]
        except IndexError:
            aanslagbiljet_info["Rekeningnummer"] = re.search(re.compile("[A-Z].[0-9].*[0-9]"),table.loc[table.iloc[:,0].str.contains("compte bancaire")].values[0][0])[0]
        try:
            aanslagbiljet_info["Mededeling"] = re.split(":.",table.loc[table.iloc[:,0].str.contains("mededeling|communication structurée", regex=True, case=False)].values[0][0])[1].strip()  
            aanslagbiljet_info["Vervaldatum"] = re.search(vervaldatum_regex,table.loc[table.iloc[:,0].str.contains("ten laatste|au plus tard le", regex=True, case=False)].values[0][0])[0]
        except IndexError: #Terug te krijgen bedrag ipv te betalen
            aanslagbiljet_info["Bedrag in uw voordeel"] = aanslagbiljet_info["Te betalen bedrag"]
            del aanslagbiljet_info["Te betalen bedrag"]

        return aanslagbiljet_info

# Extractor for reading RC-type documents (Rekening Courant/BTW-uittreksel)
class RCExtractor(Extractor):
    def __init__(self, doc_name):
        super().__init__("RC", doc_name)
        self.json_result = self.__transform_extraction()#automatically calls the extractor methods
        self.cleanup_document_location()
    
    # dict -> JSON
    def __transform_extraction(self):
        result = self.__get_data()
        result = self.__get_summary(result)
        return json.dumps(result)
    
    # Helper method for extracting the payment values from the details-table.
    def __get_payment_values(self, row):
        row_value = [re.search("^[0-9]{1,4}[.,]{1,}[0-9]{1,}.?[0-9]*",value)[0] for value in row if re.search("^[0-9]{1,4}[.,]{1,}[0-9]{1,}.?[0-9]*", value) is not None][0]
        row_value_clean = float(row_value.replace(".","").replace(",","."))
        payment_entries = {}
        payment_entries["Bedrag in uw voordeel"]=0.00 if len(row)==np.where(row==row_value)[0] or len(row)==np.where(row==row_value)[0]+1 else row_value_clean
        payment_entries["Bedrag @FOD Financiën"]=row_value_clean if len(row)==np.where(row==row_value)[0] or len(row)==np.where(row==row_value)[0]+1 else 0.00
        return payment_entries

    # Combines all data and returns it as a dictionary.
    def __get_data(self):
        tables = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}", flavor='stream', split_text=True, table_areas=['0,550,620,30'])
        if tables[0].df.shape[1]==1:
            tables = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}", flavor='stream', split_text=True, table_areas=['0,500,620,30']) 
    
        table = tables[0].df
        full_date_regex = "^([0-9].\/){2}[0-9]{4}"
        last_balance = pd.DataFrame(table.loc[table.loc[:,0].str.contains("Vorig saldo op", regex=True, case=False)])
        situations_df = pd.DataFrame(table.loc[table.loc[:,0].str.contains("Toestand eind|Toestand tot", regex=True, case=False)])
        details_df = pd.DataFrame(table.loc[table.loc[:,0].str.contains(full_date_regex, regex=True)])
        
        detail_frame = self.__get_detail(details_df)
        situation_frame = self.__get_situations(situations_df)
        formatted_data = self.__get_formatted_data(detail_frame, situation_frame, last_balance)

        return formatted_data
    
    # Returns data from blue table at the top of the page.
    def __get_summary(self, result):
        df = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}",flavor='stream', split_text=True, table_areas=['30,650,350,500'])[0].df
        try:
            vat = re.findall("([0-9].+?.+)",df.iloc[0,0])[0]
            df = df.iloc[[3,4],:]
            pay_receive_string = re.search("Te betalen saldo|Terug te krijgen|Over te dragen saldo", df.iloc[0,1])[0]
            result["Samenvatting"] = {"BTW-nummer":vat,
                        "ontbrekende aangiftes": 0 if "*****" in df.iloc[1,0] else df.iloc[1,0],
                        pay_receive_string: float(df.iloc[1,1].replace(".","").replace(",","."))}
        except IndexError:
            result["Samenvatting"] = {}
            document = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}",flavor='stream',table_areas=['30,700,650,100'])
            data = document[0].df
            vat_nr = re.search(re.compile("([0-9].+?.+)"),data.loc[data.loc[:,0].str.contains("Registratienummer")][0].values[0])[0]
            result["Samenvatting"]["BTW-nummer"] = vat_nr
            amount = data.loc[data[0].str.contains("TOTAAL")].values[0]
            if re.search("[0-9]?.[0-9]{0,3},[0-9]{0,2}",amount[0]) is not None:
                result["Samenvatting"]["terug te geven"] = re.search("[0-9]?.[0-9]{0,3},[0-9]{0,2}",amount[0])[0].replace(".","").replace(",",".")
            elif re.search("[0-9]?.[0-9]{0,3},[0-9]{0,2}",amount[1]) is not None:
                result["Samenvatting"]["over te dragen"] = re.search("[0-9]?.[0-9]{0,3},[0-9]{0,2}",amount[1])[0].replace(".","").replace(",",".")
            elif re.search("[0-9]?.[0-9]{0,3},[0-9]{0,2}",amount[2]) is not None:
                result["Samenvatting"]["te betalen"] = re.search("[0-9]?.[0-9]{0,3},[0-9]{0,2}",amount[2])[0].replace(".","").replace(",",".")
        return result

    # Returns table containing detailed information (bookings) about how the sum in the summary has been calculated.
    def __get_detail(self,details_df):
        details_d = {}
        full_date_regex = "^([0-9].\/){2}[0-9]{4}"
        for detail in details_df.values:
            booking_date = re.search(full_date_regex,detail[0])[0]
            dict_entry = {}
            subject = detail[1] if len(detail)>4 else detail[0].split("\n")[1]
            dict_entry.update(self.__get_payment_values(detail))
            dict_entry["Uitwerkingsdatum"] = detail[2] if re.search(full_date_regex,detail[1]) is None else re.search(full_date_regex,detail[1])[0]
            details_d[f"Boekingsdatum {booking_date} voor {subject}"] = dict_entry
        return details_d

    # Returns table containing detailed information (situations at end of each month) about how the sum in the summary has been calculated.
    def __get_situations(self, situations_df):
        situations_d = {}
        for situation in situations_df.values:
            dict_entry = self.__get_payment_values(situation)
            situation_date = [re.search("[0-9]{2}\/[0-9]{4}",value)[0] for value in situation if re.search("[0-9]{2}\/[0-9]{4}", value) is not None][0]
            situations_d[f"{situation[0]} {situation_date}"]=dict_entry
        return situations_d

    # Structuring dict before transforming to JSON.
    def __get_formatted_data(self, details, situations, last_balance):
        result = {}
        result["Vorige balans"] = self.__get_payment_values(last_balance.iloc[0,:])
        result["Toestanden"] = situations
        result["Detail"] = details
        return result

    def get_json(self):
        return self.json_result
# Extractor for reading PB-type documents (Personenbelasting)        
class PBExtractor(BelastingExtractor):
    def __init__(self, doc_name):
        self.doc_name = doc_name
        self.super_extractor = BelastingExtractor("PB",doc_name)
        self.json_result = self.__transform_extraction()#automatically calls the extractor methods
        self.cleanup_document_location()
    
    # Returns JSON from combined dicts
    def __transform_extraction(self):
        complete_info = json.dumps({"klantinfo": self.super_extractor.get_customer_info(), "aanslagbiljet":self.super_extractor.get_data(type="PERSOON"), "details":self.__get_detail()})
        return complete_info

    # Returns more detailed information by extracting the tax-codes with their values from the document.
    def __get_detail(self):
        tables = camelot.read_pdf(f"{filepaths.pdf_path.value}/{self.doc_name}", flavor='stream', table_areas=['50,700,625,500'], pages="3")
        df = tables[0].df
        start_idx_row = df[df[0].str.contains("[Cc]ode",regex=True, case=True) == True].index[0]
        data = df.iloc[start_idx_row:,:].reset_index(drop=True)
        data_code_idx = np.where(data.iloc[0,:].str.contains("[Cc]ode", regex=True, case=True)==True)[0]
        data_code = data.iloc[:,data_code_idx]
        data_amount_idx = np.where(data.iloc[0,:].str.contains("[Gg]egevens|Donnée", regex=True, case=True)==True)[0]
        data_amount = data.iloc[:,data_amount_idx]
        data_cstacked = pd.DataFrame(data_code.stack()).melt(ignore_index=True)
        data_astacked = pd.DataFrame(data_amount.stack()).melt(ignore_index=True)
        final_data = pd.concat([data_cstacked, data_astacked], axis=1).drop("variable",axis=1).drop_duplicates()
        final_data.columns = final_data.iloc[0]
        try:
            final_data = final_data[~final_data['Gegevens'].str.contains("[a-zA-Z]").fillna(False)]
        except KeyError:#FR
            final_data = final_data[~final_data['Donnée'].str.contains("[a-zA-Z]").fillna(False)]

        final_data = final_data[~final_data['Code'].str.contains("[a-zA-Z]").fillna(False)]
        final_data = final_data[final_data['Code'].map(len) > 0].reset_index(drop=True).T
        data_info = final_data.to_dict()
        return data_info
        
    def get_json(self):
        return self.json_result
# Extractor for reading VB-type documents (Vennootschapsbelasting)        
class VBExtractor(BelastingExtractor):
    def __init__(self, doc_name):
        self.doc_name = doc_name
        self.super_extractor = BelastingExtractor("VB",doc_name)
        self.json_result = self.__transform_extraction()#automatically calls the extractor methods
        self.cleanup_document_location()

    # Returns JSON from combined dicts
    def __transform_extraction(self):
        complete_info = json.dumps({"klantinfo":self.super_extractor.get_customer_info(), "Betaling/Ontvangs/Overdracht":self.super_extractor.get_data(type="VENNOOTSCHAP")})
        return complete_info

    def get_json(self):
        return self.json_result
# Extractor for reading AK-type documents (Aktes (alle types))      
class AkteExtractor(Extractor):
    def __init__(self, doc_name):
        super().__init__("Akte", doc_name)
        self.json_result = self.__transform_extraction()#automatically calls the extractor methods
        self.cleanup_document_location()

    def __transform_extraction(self):
        reference_code, annots = self.__get_data()
        return json.dumps({"Referentiecode":reference_code, "Annotaties":annots})

    def __get_data(self):
        pdf = fitz.open(f"{filepaths.pdf_path.value}/{self.doc_name}")
        reference_code = self.get_reference_code(pdf)
        _,annots = self.get_data_from_annots(pdf,regex=None)

        annots_temp = self.process_annots(pdf, annots)
        if len(annots_temp)>0:
            annots = annots_temp
        return reference_code,annots

    def get_data_from_annots(self, pdf, regex):
        annot_list = []
        annots = pdf[0].annots(types=fitz.PDF_ANNOT_SQUARE)
        for annot in annots:
            annot_content = annot.get_text(option="text")
            annot_list.append(annot_content) if len(annot_content)>0 else 0

        annot_list = [element.split("\n") for element in annot_list]
        annot_list = [subitem for item in annot_list for subitem in item if len(subitem)>0]

        #2 - Controleer of annotaties de aktereferentiecode bevatten
        reference_code = [element for element in annot_list if re.search(regex,element)] if regex is not None else None
        return reference_code, annot_list

    def get_reference_code_from_selectable_text(self, pdf, regex):
        text_page_1 = pdf[0].get_text()
        reference_code = re.search(regex,text_page_1)[0] if re.search(regex,text_page_1) is not None else None
        if reference_code is None or len(reference_code)<1:
            return None
        return reference_code

    def get_string_from_scanned_document(self, pdf):
        textstring = ""
        max_range = pdf.page_count if pdf.page_count<3 else 3
        for i in range(max_range):
            img_first_page = fitz.Pixmap(pdf, pdf.get_page_images(i)[0][0])
            img_first_page.save("temp_img_text.jpg")
            del img_first_page
            img = cv2.imread("temp_img_text.jpg")
            textstring += pytesseract.image_to_string(img) 
        return textstring

    def search_string_for_reference_code(self, textstring, regex):
        ref_code = re.search(regex, textstring)
        return ref_code

    def get_reference_code(self, pdf):
        reference_code_regex = re.compile("[0-9].-[A-Z]-([0-9].\/)*[0-9]{4}-[0-9]{5}")
        reference_code, _ = self.get_data_from_annots(pdf, reference_code_regex)
        textstring_pdf = None
        if len(reference_code)==0:
            reference_code = self.get_reference_code_from_selectable_text(pdf, reference_code_regex)
        if reference_code is None:
            textstring_pdf = self.get_string_from_scanned_document(pdf)
            reference_code = self.search_string_for_reference_code(textstring_pdf, reference_code_regex)
        return reference_code, textstring_pdf

    def get_image_list(self, pdf):
        for page_index in range(len(pdf)):
            image_list = pdf[page_index].get_images()
        return len(image_list)

    def process_annots(self, pdf, annots):
        image_count = self.get_image_list(pdf)
        text = pdf[0].get_text() #Selecteer eerste blz om te doorzoeken op niet-gevonden annotaties.
        if image_count>0:
            return text.split("\n")
        else:
            return [re.search(re.compile("[0-9]{1,}"+annot),text)[0] for annot in annots if re.search(re.compile("[0-9]{1,} "+annot),text) is not None]

    def get_json(self):
        return self.json_result
