from flask import Flask, jsonify, request, send_from_directory
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)

SWAGGER_URL = '/swagger'
API_URL = '/static/openapi.yaml'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "API de Cines y Películas"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

def get_cines_data():
    # url = "https://www.sensacine.com/cines/ciudades-72368/"
    url = "https://www.sensacine.com/cines/ciudades-54166/"

    # Gets the HTML content of the page
    response = requests.get(url)   
    
    # Checks if the request was successful
    if response.status_code != 200:
        return None
    
    # Parses the HTML content
    soup = BeautifulSoup(response.content, 'lxml')

    # Finds all the div elements with the class 'meta meta-theater'
    cines = soup.find_all('div', class_='meta meta-theater')
    
    # Checks if any cines were found
    if not cines:
        return None
    
    cines_data = []
    
    # Iterates over the cines
    for cine in cines:
        # Finds the h2 element with the class 'title'
        nombre_cine = cine.find('h2', class_='title')
        # Finds the address element with the class 'address address-without-acces'
        direccion_cine = cine.find('address', class_='address address-without-acces')
        # Finds the a element with the href attribute
        enlace_cine = cine.find('a', href=True)
        # num salas
        num_salas = cine.find(class_='screen-number')

        # Checks if all the required elements were found
        if nombre_cine and direccion_cine and enlace_cine:
            # Creates a dictionary with the data
            cine_data = {
                "nombre": nombre_cine.text.strip(),
                "direccion": direccion_cine.text.strip(),
                "url": "https://www.sensacine.com" + enlace_cine['href'],
                "num_salas": num_salas.text.strip()
            }            
            
            cines_data.append(cine_data)
    
    return cines_data

def get_peliculas_by_cine(cine_url):
    
    # Fetches the URL of the cinema
    cine_response = requests.get(cine_url)

    peliculas_data = []
    number_of_days = 1

    if cine_response.status_code == 200:
        cine_soup = BeautifulSoup(cine_response.content, 'lxml')
    
        for i in range(number_of_days):
            date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
            date_url = cine_url + f"#shwt_date={date}"
            
            date_response = requests.get(date_url)
            
            if date_response.status_code == 200:
                date_soup = BeautifulSoup(date_response.content, 'lxml')
                peliculas = date_soup.find_all('div', class_='card entity-card entity-card-list movie-card-theater cf hred')
                
                if peliculas:
                    for pelicula in peliculas:
                        titulo_pelicula = pelicula.find('a', class_='meta-title-link')
                        horarios = pelicula.find_all('span', class_='showtimes-hour-item-value')
                        
                        if titulo_pelicula and horarios:
                            pelicula_data = {
                                "titulo": titulo_pelicula.text.strip(),
                                "horarios": [horario.text.strip() for horario in horarios],
                                "fecha": date
                            }
                        peliculas_data.append(pelicula_data)
        return peliculas_data


@app.route('/cines', methods=['GET'])
def get_cines():    
    cines_data = get_cines_data()
    if cines_data is None:
        return jsonify({"error": "No se pudieron obtener los datos de los cines"}), 500
    return jsonify(cines_data)


@app.route('/peliculas', methods=['GET'])
def get_peliculas():
    peliculas = []
    response = requests.get('https://www.sensacine.com/peliculas/')
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'lxml')
        peliculas_list = soup.find_all('div', class_='entity-card')
        for pelicula in peliculas_list:
            titulo = pelicula.find('a', class_='meta-title-link').text.strip()
            duracion = pelicula.find('div', class_='meta-body-item meta-body-info').text.strip()
            director = pelicula.find('div', class_='meta-body-item meta-body-direction').text.strip()
            reparto = pelicula.find('div', class_='meta-body-item meta-body-actor').text.strip()
            sinopsis = pelicula.find('div', class_='content-txt').text.strip()
            valoracion = pelicula.find('span', class_='stareval-note').text.strip()
            pelicula_data = {
                "titulo": titulo,
                "duracion": duracion,
                "director": director,
                "reparto": reparto,
                "sinopsis": sinopsis,
                "valoracion": valoracion
            }
            peliculas.append(pelicula_data)
    return jsonify(peliculas)

@app.route('/horarios', methods=['GET'])
def get_horarios():
    cine_nombre = request.args.get('cine')
    pelicula_titulo = request.args.get('pelicula')
    
    if not cine_nombre or not pelicula_titulo:
        return jsonify({"error": "Parámetros 'cine' y 'pelicula' son requeridos"}), 400
    
    cines_data = get_cines_data()
    if cines_data is None:
        return jsonify({"error": "Error en la solicitud HTTP o no se encontraron cines"}), 500
    
    for cine in cines_data:
        if cine["nombre"].lower() == cine_nombre.lower():

            cine_url = cine["url"]
            peliculas = get_peliculas_by_cine(cine_url)

            for pelicula in peliculas:
                if pelicula["titulo"].lower() == pelicula_titulo.lower():
                    return jsonify({
                        "cine": cine["nombre"],
                        "direccion": cine["direccion"],
                        "titulo": pelicula["titulo"],
                        "horarios": pelicula["horarios"],
                        "fecha": pelicula["fecha"]
                    })
    
    return jsonify({"error": "No se encontraron horarios para la película en el cine especificado"}), 404


@app.route('/cartelera', methods=['GET'])
def get_cartelera_by_cine():
    cine_nombre = request.args.get('cine')

    print(cine_nombre)
    
    if not cine_nombre:
        return jsonify({"error": "Parámetro 'cine' es requerido"}), 400
    
    cines_data = get_cines_data()
    if cines_data is None:
        return jsonify({"error": "Error en la solicitud HTTP o no se encontraron cines"}), 500
    
    for cine in cines_data:
        if cine["nombre"].lower() == cine_nombre.lower():
            print("Cine encontrado:")
            print(cine["nombre"] + " " + cine["url"])
            cine_url = cine["url"]
            peliculas = get_peliculas_by_cine(cine_url)
            return jsonify(peliculas)
    
    return jsonify({"error": "No se encontraron horarios para el cine especificado"}), 404

@app.route('/cines_pelicula', methods=['GET'])
def get_cines_pelicula():
    pelicula_titulo = request.args.get('pelicula')
    
    if not pelicula_titulo:
        return jsonify({"error": "Parámetro 'pelicula' es requerido"}), 400
    
    cines_data = get_cines_data()
    if cines_data is None:
        return jsonify({"error": "Error en la solicitud HTTP o no se encontraron cines"}), 500
    
    cines_pelicula = []
    for cine in cines_data:
        for pelicula in cine["peliculas"]:
            if pelicula["titulo"].lower() == pelicula_titulo.lower():
                cines_pelicula.append({
                    "cine": cine["nombre"],
                    "direccion": cine["direccion"],
                    "horarios": pelicula["horarios"],
                    "fecha": pelicula["fecha"]
                })
    
    if not cines_pelicula:
        return jsonify({"error": "No se encontraron cines que emitan la película especificada"}), 404
    
    return jsonify(cines_pelicula)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True)