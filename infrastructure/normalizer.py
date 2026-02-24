import unicodedata
import re
import pandas as pd

class TextNormalizer:
    @staticmethod
    def normalize(text: str) -> str:
        if text is None or pd.isna(text) or text == "": 
            return ""
        
        text = str(text).upper().strip()
        
        # Eliminar acentos
        text = "".join(c for c in unicodedata.normalize('NFD', text) 
                      if unicodedata.category(c) != 'Mn')
        
        # Limpieza de caracteres especiales
        text = re.sub(r'[^A-Z0-9 ]', '', text)
        
        # Eliminar espacios dobles
        text = " ".join(text.split())
        
        return text