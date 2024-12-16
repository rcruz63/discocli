""" Aplicación de Interfaz de Línea de Comandos (CLI) utilizando la biblioteca Click de Python """
from typing import Optional
import click
import requests
import json
from datetime import datetime
import csv
from io import StringIO
from typing import List, Dict, Any
import logging
from bs4 import BeautifulSoup
import re

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes para el rango de fechas válido
FECHA_INICIO = datetime(2008, 2, 1)
FECHA_FIN = datetime(2021, 6, 30)

BASE_URL = "https://www.rtve.es/play/audios/moduloRadio/1936/emisiones"

def validar_fecha(mes: int, anio: int) -> bool:
    """
    Valida si la fecha está dentro del rango de emisión del programa.
    
    Args:
        mes: Número del mes (1-12)
        anio: Año a consultar
        
    Returns:
        bool: True si la fecha es válida, False en caso contrario
    """
    fecha = datetime(anio, mes, 1)
    return FECHA_INICIO <= fecha <= FECHA_FIN

def obtener_rango_fechas_valido() -> str:
    """
    Retorna una cadena con el rango de fechas válido para consulta.
    
    Returns:
        str: Descripción del rango de fechas válido
    """
    return (f"El programa se emitió desde {FECHA_INICIO.strftime('%B %Y')} "
            f"hasta {FECHA_FIN.strftime('%B %Y')}")

def analizar_estructura_api() -> None:
    """
    Función de análisis para entender la estructura de la API de RTVE.
    Realiza peticiones de prueba y registra la estructura de la respuesta.
    """
    try:
        # Añadir headers para simular un navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Referer': 'https://www.rtve.es/',
        }
        
        # Intentar obtener los datos
        response = requests.get(BASE_URL, headers=headers)
        response.raise_for_status()
        
        logger.info(f"Código de estado: {response.status_code}")
        logger.info(f"Headers de respuesta: {dict(response.headers)}")
        
        # Intentar parsear como JSON primero
        try:
            json_data = response.json()
            logger.info("Respuesta JSON:")
            logger.info(json.dumps(json_data, indent=2, ensure_ascii=False)[:1000])
        except json.JSONDecodeError:
            # Si no es JSON, mostrar como texto
            logger.info("Respuesta no es JSON. Mostrando como texto:")
            logger.info(f"Contenido: {response.text[:1000]}...")
            
    except requests.RequestException as e:
        logger.error(f"Error al hacer la petición: {str(e)}")
        if hasattr(e.response, 'text'):
            logger.error(f"Contenido del error: {e.response.text[:500]}")

def obtener_episodios(mes: int, anio: int) -> List[Dict[str, Any]]:
    """
    Obtiene los episodios para un mes y año específicos.
    
    Args:
        mes: Número del mes (1-12)
        anio: Año a consultar
        
    Returns:
        Lista de episodios con su información
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    }
    
    episodios = []
    page = 1
    while True:
        url = f"{BASE_URL}?month={mes}&year={anio}&search=&page={page}"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar todos los elementos de episodio
            items = soup.select('li.elem_')
            if not items:
                break
                
            for item in items:
                try:
                    # Extraer datos del atributo data-setup
                    data_setup = json.loads(item.get('data-setup', '{}'))
                    
                    # Extraer título
                    titulo_elem = item.select_one('.maintitle')
                    titulo = titulo_elem.text.strip() if titulo_elem else data_setup.get('title', 'Sin título')
                    
                    # Extraer ID y construir URL
                    id_asset = data_setup.get('idAsset', '')
                    url_episodio = f"https://www.rtve.es/play/audios/discopolis/{id_asset}/" if id_asset else ''
                    
                    # Extraer fecha del div.mod si existe
                    fecha_elem = item.select_one('.mod')
                    fecha = fecha_elem.get('data-inicio', '') if fecha_elem else ''
                    
                    episodio = {
                        "id": id_asset,
                        "titulo": titulo,
                        "url": url_episodio,
                        "fecha": fecha,
                    }
                    
                    # Intentar extraer descripción si existe
                    desc_elem = item.select_one('.description')
                    if desc_elem:
                        episodio["descripcion"] = desc_elem.text.strip()
                    
                    episodios.append(episodio)
                    
                except (json.JSONDecodeError, AttributeError) as e:
                    logger.warning(f"Error al procesar episodio: {str(e)}")
                    continue
            
            # Verificar si hay más páginas
            if not soup.select('.siguiente'):
                break
                
            page += 1
            
        except requests.RequestException as e:
            logger.error(f"Error al obtener la página {page}: {str(e)}")
            break
    
    return episodios

def formatear_salida(episodios: List[Dict[str, Any]], formato: str) -> str:
    """
    Formatea la lista de episodios según el formato especificado.
    
    Args:
        episodios: Lista de episodios a formatear
        formato: Formato deseado (json, csv, texto)
        
    Returns:
        String con los datos formateados
    """
    if formato == "json":
        return json.dumps(episodios, indent=2, ensure_ascii=False)
    
    elif formato == "csv":
        output = StringIO()
        if episodios:
            writer = csv.DictWriter(output, fieldnames=episodios[0].keys())
            writer.writeheader()
            writer.writerows(episodios)
        return output.getvalue()
    
    else:  # formato texto
        resultado = []
        for ep in episodios:
            resultado.append(f"Título: {ep['titulo']}")
            if ep.get('fecha'):
                resultado.append(f"Fecha: {ep['fecha']}")
            if ep.get('descripcion'):
                resultado.append(f"Descripción: {ep['descripcion']}")
            if ep.get('url'):
                resultado.append(f"URL: {ep['url']}")
            resultado.append("-" * 40)
        return "\n".join(resultado)

@click.group()
def cli() -> None:
    """
    DiscoCLI - Herramienta de línea de comandos para gestión del programa Discopolis.
    
    Esta herramienta permite interactuar con el archivo del programa de radio Discopolis
    a través de una interfaz de línea de comandos.
    """
    pass

@cli.command()
@click.option('--mes', '-m', type=click.IntRange(1, 12), required=True, 
              help='Mes a consultar (1-12)')
@click.option('--anio', '-a', type=int, required=True,
              help='Año a consultar')
@click.option('--formato', '-f', type=click.Choice(['json', 'csv', 'texto']),
              default='texto', help='Formato de salida')
def listar(mes: int, anio: int, formato: str) -> None:
    """
    Lista los episodios disponibles para un mes y año específicos.
    
    Args:
        mes: Número del mes (1-12)
        anio: Año a consultar
        formato: Formato de salida (json, csv, texto)
    """
    try:
        if not validar_fecha(mes, anio):
            click.echo(f"Error: La fecha especificada está fuera del rango válido.", err=True)
            click.echo(obtener_rango_fechas_valido(), err=True)
            return

        episodios = obtener_episodios(mes, anio)
        if not episodios:
            click.echo(f"No se encontraron episodios para {mes}/{anio}")
            return
            
        resultado = formatear_salida(episodios, formato)
        click.echo(resultado)
    except Exception as e:
        click.echo(f"Error al obtener los episodios: {str(e)}", err=True)

@cli.command()
def analizar():
    """
    Analiza la estructura de la API de RTVE para entender cómo obtener los datos.
    Este es un comando temporal para desarrollo.
    """
    click.echo("Analizando estructura de la API de RTVE...")
    analizar_estructura_api()

if __name__ == '__main__':
    cli()