import json
import requests
from bs4 import BeautifulSoup
import re

def lambda_handler(event, context):
    # Transforma el payload recibido en un diccionario
    number = event['number']
    doc_type = event['doc_type']
    object_response = {'data': list()}
    comparendos = {'comparendos': list(), 'resoluciones': list()}
    try:
        try:
            placa_veh = ""
        except:
            placa_veh = None
        doc_types = {
            "CC": 1,
            "NIT": 2,
            "CE": 3,
            "TI": 4,
            "PA": 5,
            "RC": 6,
            "SERVITECAS": 7,
            "CD": 8
        }
        tipo_documento = doc_types['CC']
        round_url = f"https://consultas.transitobogota.gov.co:8010/consultas_generales/buscar_comparendos.php?datos_enviados=S&tipo_documento={tipo_documento}&numero_identificacion={number}&placa_veh={placa_veh}&captcha_security_text=9ac46c1385c7925fc9ea77a15d3f9e8b&is_present_captcha_flag=2122721260&captcha_user_text=odwCM&pagina_actual=1&tipo_busqueda=BC&es_regresar=&existe_financiacion_finan=0&existe_financiacion_acpag=0"
        print(round_url)
        page = requests.get(round_url)
        soup = BeautifulSoup(page.text, 'html.parser')
        find = soup.find('//body[1]/form[1]/center[4]/table[1]/tbody[1]/tr[1]/td[1]/table[1]/tbody[1]')
        tds = soup.find_all("td", class_="tdtablapaginada1")
        print(len(tds))
        tds = tds + soup.find_all("td", class_="tdtablapaginada2")
        print(len(tds))
        counter = 0
        comparendo = dict()
        tipo_comparendo = False
        medio_imposicion = False
        for td in tds:
            switcher = {
                1: "estado",
                2: "id_comparendo",
                3: "placa",
                4: "fecha_imposicion",
                5: "valor_neto",
                6: "infraccion",
                7: "valor_pago",
                8: "",
                9: "placa",
                10: "",
                11: "fecha_notificacion",
                12: "fotodeteccion"
            }
            formatted_value = td.text.replace('\xa0', ' ').strip()
            print(counter, formatted_value)
            if counter in [1, 2, 3, 4, 5, 7]:
                comparendo[switcher[counter]] = formatted_value
            elif counter == 0 and formatted_value == 'COMPARENDO -ELECTRONICO':
                tipo_comparendo = True
            elif counter == 8 and formatted_value == 'CAMARAS SALVAVIDAS':
                medio_imposicion = True
            elif counter == 12:
                comparendo[switcher[counter]] = tipo_comparendo and medio_imposicion
                url_detail = "https://consultas.transitobogota.gov.co:8010/consultas_generales"
                the_ref = td.a['href'][1:]
                detail = requests.get(url_detail + the_ref)
                soup_detail = BeautifulSoup(detail.text, 'html.parser')
                spans = soup_detail.find_all("span", class_="datoformulario")
                matches = re.findall(r'\[([^\[\]]+)\s*\]', spans[8].text)
                comparendo[switcher[6]] = matches[0].strip()
                comparendo['secretaria'] = 'Bogotá D.C.'
                comparendo[switcher[11]] = spans[11].text.strip()
                ## agregar variables que no manda el scraper pero que toca mandar asi sea en null ##
                comparendo['direccion'] = None
                comparendo['fechaCoactivo'] = None
                comparendo['fechaNotificacion'] = None
                comparendo['nroCoactivo'] = None
                comparendo['scraper'] = 'Juzto-bogota'
                comparendos['comparendos'].append(comparendo)
                comparendo = dict()
                counter = -1
            counter = counter + 1
        print(comparendo)
        object_response['data'].append(comparendos)
        object_response['status'] = 'success'
    except Exception as ex:
        object_response['error'] = str(ex)
        object_response['status'] = 'error'
    return object_response
    