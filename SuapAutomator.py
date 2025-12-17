import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class SuapAutomator:
    def __init__(self, username, password):
        if not username or not password:
            raise ValueError("Usuário e senha são obrigatórios.")
        self.username = username
        self.password = password
        self.driver = self.initialize_driver()

    @staticmethod
    def _converter_para_numero(valor_texto):
        if not isinstance(valor_texto, str): return None
        try:
            valor_limpo = valor_texto.replace(',', '.').replace('%', '').strip()
            if not valor_limpo or valor_limpo == '-': return None
            return float(valor_limpo)
        except: return None

    def _obter_valor_misto(self, valor_texto):
        """Tenta número, se não for, retorna o texto (para conceitos)."""
        num = self._converter_para_numero(valor_texto)
        if num is not None: return num
        texto = valor_texto.strip()
        return texto if texto and texto != '-' else None

    def initialize_driver(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
        return webdriver.Chrome(options=chrome_options)

    def login(self):
        self.driver.get("https://suap.ifba.edu.br/")
        self.driver.find_element(By.NAME, "username").send_keys(self.username)
        self.driver.find_element(By.NAME, "password").send_keys(self.password)
        self.driver.find_element(By.NAME, "password").submit()
        time.sleep(2)

    def extract_boletim_data(self, course_type):
        frequencia_total = "N/A"
        try:
            seletor_freq = "//table[@class='borda']/tfoot//td[contains(text(), '%')]"
            frequencia_total = self._obter_valor_misto(self.driver.find_element(By.XPATH, seletor_freq).text)
        except: pass

        disciplinas = []
        linhas = self.driver.find_elements(By.XPATH, "//table[@class='borda']//tbody/tr")
        for linha in linhas:
            col = linha.find_elements(By.TAG_NAME, 'td')
            if len(col) >= 13:
                item = {
                    "Disciplina": col[1].text,
                    "Situação": col[6].text.strip(),
                }
                
                if course_type == 'subsequente':
                    # No Subsequente: 7=N1, 11=NAF, 12=MFD (13 é Ações)
                    item["N1"] = self._converter_para_numero(col[7].text)
                    item["NAF"] = self._converter_para_numero(col[11].text)
                    item["MFD"] = self._obter_valor_misto(col[12].text)
                else: 
                    # No Integrado: 7=U1, 9=U2, 11=U3, 13=MF (14 é Ações)
                    item["U1"] = self._converter_para_numero(col[7].text)
                    item["U2"] = self._converter_para_numero(col[9].text)
                    item["U3"] = self._converter_para_numero(col[11].text)
                    val_mf = col[13].text if len(col) > 13 else col[12].text
                    item["MF"] = self._obter_valor_misto(val_mf)
                
                disciplinas.append(item)
        
        return frequencia_total, disciplinas

    def close_browser(self):
        self.driver.quit()