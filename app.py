from flask import Flask, render_template, request, Response
from SuapAutomator import SuapAutomator
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream_grades')
def stream_grades():
    username = request.args.get('username')
    password = request.args.get('password')
    class_code = request.args.get('class_code')
    course_type = request.args.get('course_type')

    def generate_data():
        automator = None
        full_results = []
        try:
            yield f"data: {json.dumps({'status': 'progress', 'message': 'Iniciando automação...'})}\n\n"
            automator = SuapAutomator(username, password)
            automator.login()
            
            automator.driver.get(f"https://suap.ifba.edu.br/edu/turma/{class_code}/?tab=dados_alunos")
            WebDriverWait(automator.driver, 20).until(EC.presence_of_element_located((By.XPATH, "//table[.//a[contains(@href, '/edu/aluno/')]]//tbody/tr")))
            
            linhas_alunos = automator.driver.find_elements(By.XPATH, "//table[.//a[contains(@href, '/edu/aluno/')]]//tbody/tr")
            alunos = []
            for linha in linhas_alunos:
                try:
                    celula_nome = linha.find_element(By.XPATH, ".//td[3]")
                    link_element = celula_nome.find_element(By.TAG_NAME, "a")
                    alunos.append({
                        'url': link_element.get_attribute('href'),
                        'nome': celula_nome.text.split('(')[0].strip(),
                        'matricula': link_element.text.strip()
                    })
                except: continue

            for aluno in alunos:
                yield f"data: {json.dumps({'status': 'student_processing', 'name': aluno['nome']})}\n\n"
                url_boletim = aluno['url'].rstrip('/') + '/?tab=boletim'
                automator.driver.get(url_boletim)
                
                try:
                    WebDriverWait(automator.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//table[@class='borda']//tbody/tr")))
                    frequencia_total, disciplinas_data = automator.extract_boletim_data(course_type)
                    
                    link_formula = f'=HYPERLINK("{url_boletim}", "Abrir Boletim")'

                    for d in disciplinas_data:
                        row = {
                            "Nome do Aluno": aluno['nome'],
                            "Matrícula": aluno['matricula'],
                            "Disciplina": d["Disciplina"],
                            "Situação": d["Situação"],
                        }
                        
                        if course_type == 'subsequente':
                            row.update({
                                "N1": d.get("N1"),
                                "NAF": d.get("NAF"),
                                "MFD/Conceito": d.get("MFD")
                            })
                        else:
                            row.update({
                                "Unidade 1": d.get("U1"),
                                "Unidade 2": d.get("U2"),
                                "Unidade 3": d.get("U3"),
                                "Média Final": d.get("MF")
                            })

                        row.update({
                            "Frequência Total (%)": frequencia_total,
                            "Link do Boletim": link_formula
                        })
                        full_results.append(row)
                except TimeoutException: continue
            
            yield f"data: {json.dumps({'status': 'finished', 'payload': full_results})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
        finally:
            if automator: automator.close_browser()

    return Response(generate_data(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)