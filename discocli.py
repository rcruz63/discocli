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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        }
        
        # Obtener un mes de ejemplo dentro del rango válido
        url = f"{BASE_URL}?month=3&year=2020&search=&page=1"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # Analizar un elemento de ejemplo
        item = soup.select_one('li.elem_')
        if item:
            logger.info("=== Análisis detallado de un elemento de episodio ===")
            # Mostrar todos los atributos del elemento
            logger.info(f"Atributos del elemento: {item.attrs}")
            
            # Analizar data-setup
            data_setup = json.loads(item.get('data-setup', '{}'))
            logger.info(f"Contenido de data-setup: {json.dumps(data_setup, indent=2)}")
            
            # Buscar elementos específicos
            for elem in item.select('[class]'):
                logger.info(f"Elemento con clase '{elem.get('class')}': {elem.text.strip()}")
                logger.info(f"Atributos: {elem.attrs}")
            
    except Exception as e:
        logger.error(f"Error en el análisis: {str(e)}")

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
            
            items = soup.select('li.elem_')
            if not items:
                break
                
            for item in items:
                try:
                    data_setup = json.loads(item.get('data-setup', '{}'))
                    
                    # Extraer título y número de episodio
                    titulo_elem = item.select_one('.maintitle')
                    titulo = titulo_elem.text.strip() if titulo_elem else data_setup.get('title', 'Sin título')
                    
                    # Extraer fecha completa
                    fecha_elem = item.select_one('.datemi')
                    fecha = fecha_elem.get('aria-label', '').replace('Fecha de Emisión: ', '') if fecha_elem else ''
                    
                    # Extraer duración
                    duracion_elem = item.select_one('.duration')
                    duracion = duracion_elem.get('aria-label', '').replace('Duración: ', '') if duracion_elem else ''
                    
                    # Extraer URL completa
                    url_elem = item.select_one('.goto_media')
                    url_episodio = url_elem.get('href', '') if url_elem else ''
                    
                    # Extraer ID
                    id_asset = data_setup.get('idAsset', '')
                    
                    episodio = {
                        "id": id_asset,
                        "titulo": titulo,
                        "url": url_episodio,
                        "fecha": fecha,
                        "duracion": duracion
                    }
                    
                    # Extraer descripción si existe
                    desc_elem = item.select_one('.description')
                    if desc_elem:
                        episodio["descripcion"] = desc_elem.text.strip()
                    
                    episodios.append(episodio)
                    
                except (json.JSONDecodeError, AttributeError) as e:
                    logger.warning(f"Error al procesar episodio: {str(e)}")
                    continue
            
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
            if ep.get('duracion'):
                resultado.append(f"Duración: {ep['duracion']}")
            if ep.get('programa'):
                resultado.append(f"Programa: {ep['programa']}")
            if ep.get('emisora'):
                resultado.append(f"Emisora: {ep['emisora']}")
            if ep.get('descripcion'):
                resultado.append(f"Descripción: {ep['descripcion']}")
            if ep.get('url'):
                resultado.append(f"URL: {ep['url']}")
            resultado.append("-" * 40)
        return "\n".join(resultado)

def buscar_episodio_por_numero(numero: str) -> Dict[str, Any]:
    """
    Busca un episodio específico por su número.
    
    Args:
        numero: Número del episodio (ejemplo: '10939')
        
    Returns:
        Dict con la información del episodio o None si no se encuentra
    """
    # Normalizar el número (quitar puntos y espacios)
    numero_normalizado = numero.replace('.', '').strip()
    logger.info(f"Buscando episodio número: {numero_normalizado}")
    
    # Iteramos por los meses del rango válido
    fecha_actual = FECHA_INICIO
    while fecha_actual <= FECHA_FIN:
        logger.info(f"Buscando en {fecha_actual.strftime('%B %Y')}...")
        episodios = obtener_episodios(fecha_actual.month, fecha_actual.year)
        
        for episodio in episodios:
            titulo = episodio['titulo']
            # Extraer el número del título usando regex
            match = re.match(r'(\d+\.?\d*)', titulo)
            if match:
                numero_episodio = match.group(1).replace('.', '')
                logger.info(f"Comparando {numero_normalizado} con {numero_episodio} del título: {titulo}")
                if numero_episodio == numero_normalizado:
                    logger.info(f"¡Encontrado! Episodio: {titulo}")
                    return episodio
        
        # Avanzar al siguiente mes
        if fecha_actual.month == 12:
            fecha_actual = fecha_actual.replace(year=fecha_actual.year + 1, month=1)
        else:
            fecha_actual = fecha_actual.replace(month=fecha_actual.month + 1)
    
    logger.info("No se encontró el episodio después de buscar en todo el rango de fechas")
    return None

def obtener_url_audio(url_episodio: str) -> str:
    """
    Obtiene la URL del episodio para reproducir en el navegador.
    
    Args:
        url_episodio: URL de la página del episodio
        
    Returns:
        URL del episodio
    """
    return url_episodio

def descargar_episodio(url: str, numero: str) -> str:
    """
    Descarga un episodio de audio.
    
    Args:
        url: URL de descarga del episodio
        numero: Número del episodio para el nombre del archivo
        
    Returns:
        Ruta al archivo descargado
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'audio/webm,audio/ogg,audio/wav,audio/*;q=0.9,application/ogg;q=0.7,video/*;q=0.6,*/*;q=0.5',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        }
        
        # Crear directorio de descargas si no existe
        import os
        download_dir = os.path.expanduser("~/Downloads/discopolis")
        os.makedirs(download_dir, exist_ok=True)
        
        # Nombre del archivo
        filename = f"discopolis_{numero}.mp3"
        filepath = os.path.join(download_dir, filename)
        
        # Si ya existe el archivo, no lo descargamos de nuevo
        if os.path.exists(filepath):
            logger.info(f"El episodio ya está descargado en: {filepath}")
            return filepath
            
        # Descargar el archivo
        with requests.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f:
                with click.progressbar(length=total, label='Descargando episodio') as bar:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            bar.update(len(chunk))
                            
        logger.info(f"Episodio descargado en: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error al descargar el episodio: {str(e)}")
        raise

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

@cli.command()
@click.argument('numero')
@click.option('--debug/--no-debug', default=False,
              help='Mostrar información de depuración')
def reproducir(numero: str, debug: bool) -> None:
    """
    Reproduce un episodio específico por su número.
    
    Args:
        numero: Número del episodio (ejemplo: 10939)
        debug: Si se debe mostrar información de depuración
    """
    try:
        if debug:
            logging.getLogger().setLevel(logging.INFO)
        else:
            logging.getLogger().setLevel(logging.WARNING)
            
        click.echo(f"Buscando episodio {numero}...")
        episodio = buscar_episodio_por_numero(numero)
        
        if not episodio:
            click.echo(f"No se encontró el episodio número {numero}")
            return
            
        click.echo(f"\nEncontrado: {episodio['titulo']}")
        click.echo(f"Fecha: {episodio['fecha']}")
        click.echo(f"Duración: {episodio['duracion']}")
        click.echo(f"URL: {episodio['url']}\n")
        
        # Obtener URL del episodio
        url = obtener_url_audio(episodio['url'])
        
        click.echo("Abriendo episodio en el navegador web...")
        import webbrowser
        webbrowser.open(url)
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

if __name__ == '__main__':
    cli()