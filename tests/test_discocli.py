"""Tests para la aplicación DiscoCLI"""
import pytest
from click.testing import CliRunner
from discocli import cli, obtener_episodios, formatear_salida

@pytest.fixture
def runner():
    """Fixture que proporciona un CliRunner para testing."""
    return CliRunner()

@pytest.fixture
def episodios_ejemplo():
    """Fixture que proporciona datos de ejemplo para las pruebas."""
    return obtener_episodios(1, 2024)

def test_cli_sin_comandos(runner):
    """Prueba la ejecución del CLI sin comandos."""
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "Usage:" in result.output

def test_listar_parametros_requeridos(runner):
    """Prueba que el comando listar requiere mes y año."""
    result = runner.invoke(cli, ['listar'])
    assert result.exit_code != 0
    assert "Missing option" in result.output

def test_listar_mes_invalido(runner):
    """Prueba que el mes debe estar entre 1 y 12."""
    result = runner.invoke(cli, ['listar', '--mes', '13', '--anio', '2024'])
    assert result.exit_code != 0
    assert "Invalid value" in result.output

def test_listar_formato_texto(runner):
    """Prueba el listado en formato texto."""
    result = runner.invoke(cli, ['listar', '--mes', '1', '--anio', '2024'])
    assert result.exit_code == 0
    assert "Título:" in result.output
    assert "Fecha:" in result.output

def test_listar_formato_json(runner):
    """Prueba el listado en formato JSON."""
    result = runner.invoke(cli, ['listar', '--mes', '1', '--anio', '2024', '--formato', 'json'])
    assert result.exit_code == 0
    assert '"titulo":' in result.output
    assert '"fecha":' in result.output

def test_listar_formato_csv(runner):
    """Prueba el listado en formato CSV."""
    result = runner.invoke(cli, ['listar', '--mes', '1', '--anio', '2024', '--formato', 'csv'])
    assert result.exit_code == 0
    assert "titulo,fecha" in result.output

def test_formatear_salida_texto(episodios_ejemplo):
    """Prueba la función de formateo en texto."""
    resultado = formatear_salida(episodios_ejemplo, 'texto')
    assert "Título:" in resultado
    assert "Fecha:" in resultado
    assert "Descripción:" in resultado

def test_formatear_salida_json(episodios_ejemplo):
    """Prueba la función de formateo en JSON."""
    resultado = formatear_salida(episodios_ejemplo, 'json')
    assert '"titulo":' in resultado
    assert '"fecha":' in resultado

def test_formatear_salida_csv(episodios_ejemplo):
    """Prueba la función de formateo en CSV."""
    resultado = formatear_salida(episodios_ejemplo, 'csv')
    assert "titulo,fecha" in resultado 