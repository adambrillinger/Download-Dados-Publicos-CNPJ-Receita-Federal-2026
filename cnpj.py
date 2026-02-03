from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time
import os
import shutil

URL = "https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9"

DOWNLOADS_DIR = r"C:\xxxxxxx"
DESTINO_DIR = r"C:\xxxxxxxxx"


def esperar_e_mover_download(timeout=5400):
    inicio = time.time()

    arquivos_iniciais = set(os.listdir(DOWNLOADS_DIR))

    while True:
        arquivos_atuais = set(os.listdir(DOWNLOADS_DIR))

        # arquivo novo apareceu
        novos = arquivos_atuais - arquivos_iniciais

        # remove arquivos temporários
        novos = {f for f in novos if not f.endswith(".crdownload")}

        if novos:
            arquivo = max(
                novos,
                key=lambda f: os.path.getmtime(os.path.join(DOWNLOADS_DIR, f))
            )

            origem = os.path.join(DOWNLOADS_DIR, arquivo)
            destino = os.path.join(DESTINO_DIR, arquivo)

            shutil.move(origem, destino)
            print(f"✔ Arquivo movido para: {destino}")
            return destino

        if time.time() - inicio > timeout:
            raise TimeoutError("Download não apareceu na pasta Downloads")

        time.sleep(1)

options = Options()
# options.add_argument("--headless")  # deixe visível para validar
driver = webdriver.Chrome(options=options)
driver.maximize_window()
wait = WebDriverWait(driver, 30)

def obter_competencia_local_mais_recente(pasta):
    competencias = set()

    for nome in os.listdir(pasta):
        match = re.search(r"\d{4}-\d{2}", nome)
        if match:
            competencias.add(match.group())

    if not competencias:
        return None

    return sorted(competencias)[-1]


try:
    driver.get(URL)
    time.sleep(5)  # garante que o Vue renderizou

    # 🔍 Localiza o botão pelo TEXTO visível "Modificado"
    botao_modificado = driver.find_element(
    By.XPATH,
    "//span[normalize-space()='Modified']/ancestor::button")
    "//span[contains(normalize-space(),'Modified') or contains(normalize-space(),'Modificado')]/ancestor::button"

    # 🔘 Clica no botão
    botao_modificado.click()

    print("✔ Botão 'Modificado' clicado com sucesso")

    time.sleep(2)  # só para você ver o efeito na tela

 # 2️⃣ Aguarda o menu abrir e clicar em "Últimos 7 dias"
    btn_7_dias = driver.find_element(
    By.XPATH,
    "//span[contains(normalize-space(),'7 day') or contains(normalize-space(),'7 dias')]/ancestor::button"

    btn_7_dias.click()

    print("✔ Filtro 'Últimos 7 dias' aplicado com sucesso")

    time.sleep(2)  # só para visualizar o efeito

# 3️⃣ Aguarda a lista atualizar
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[starts-with(@class,'files-list__row-name-')]")
    ))

    # 4️⃣ Coleta dos valores (sem duplicar)
    elementos = driver.find_elements(
        By.XPATH,
        "//*[starts-with(@class,'files-list__row-name-')]"
    )

    competencias = set()

    for el in elementos:
        texto = el.text.strip()
        if re.fullmatch(r"\d{4}-\d{2}", texto):
            competencias.add(texto)

    if not competencias:
        print("Nenhuma competência encontrada.")
    else:
        ordenadas = sorted(competencias)
        mais_recente = ordenadas[-1]

        print("Competências encontradas:")
        for c in ordenadas:
            print(" -", c)

        print("\n👉 Competência mais recente:", mais_recente)    

    competencia_local = obter_competencia_local_mais_recente(DESTINO_DIR)

    if competencia_local:
        print(f"📂 Competência mais recente local: {competencia_local}")

    if mais_recente <= competencia_local:
        print("ℹ Nenhuma competência nova encontrada. Download não será executado.")
        driver.quit()
        exit(0)
    else:
        print("📂 Nenhuma competência encontrada localmente. Download será executado.")


    # 5️⃣ Localiza o span da competência mais recente
    linha_competencia = wait.until(
    EC.presence_of_element_located(
        (
            By.XPATH,
            f"//span[starts-with(@class,'files-list__row-name-') and normalize-space()='{mais_recente}']"
        )
    )
    )

    # 6️⃣ Sobe até a linha (tr)
    row = linha_competencia.find_element(By.XPATH, "./ancestor::tr")

    # 7️⃣ Dentro da linha, encontra o botão de ações (3 pontinhos)
    botao_acoes = row.find_element(
    By.XPATH,
    ".//button[@aria-label='Actions']"
    )

    # 8️⃣ Clica no botão de ações
    driver.execute_script("arguments[0].click();", botao_acoes)
    print(f"✔ Menu de ações aberto para {mais_recente}")

    # 9️⃣ Aguarda o botão "Baixar / Download" no menu
    btn_download = wait.until(
    EC.element_to_be_clickable(
        (
            By.XPATH,
            "//span[contains(normalize-space(),'Download') or contains(normalize-space(),'Baixar')]/ancestor::button"
        )
    )
    )

    btn_download.click()
    print("⬇ Download iniciado com sucesso")

    print("⏳ Aguardando término do download...")
    esperar_e_mover_download()
    print("✔ Download concluído com sucesso")


finally:
    print("Fechando navegador com segurança...")
    time.sleep(2)
    driver.quit()
