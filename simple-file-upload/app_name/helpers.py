from .extractors import RCExtractor

class ExtractorController:
    def assign_to_extractor(self,doc_name):
        return RCExtractor(doc_name).get_json() #result from extractor
