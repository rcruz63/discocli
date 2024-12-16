""" Aplicación de Interfaz de Línea de Comandos (CLI) utilizando la biblioteca Click de Python """
from typing import Optional
import click

@click.group()
def cli() -> None:
    """
    DiscoCLI - Herramienta de línea de comandos para gestión de recursos.
    
    Esta herramienta permite interactuar con diferentes recursos a través
    de una interfaz de línea de comandos.
    """
    pass

@cli.command()
@click.option('--nombre', '-n', type=str, help='Nombre del recurso')
@click.option('--verbose', '-v', is_flag=True, help='Modo verboso')
def consultar(nombre: Optional[str], verbose: bool) -> None:
    """
    Consulta información sobre un recurso específico.
    
    Args:
        nombre: Nombre del recurso a consultar
        verbose: Activa el modo verboso para más detalles
    """
    if verbose:
        click.echo(f"Modo verboso activado")
    
    if nombre:
        click.echo(f"Consultando recurso: {nombre}")
    else:
        click.echo("Consultando todos los recursos")

if __name__ == '__main__':
    cli()