"""Tests para la aplicación DiscoCLI"""
import pytest
from click.testing import CliRunner
from discocli import cli

@pytest.fixture
def runner():
    """Fixture que proporciona un CliRunner para testing."""
    return CliRunner()

def test_cli_sin_comandos(runner):
    """Prueba la ejecución del CLI sin comandos."""
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "Usage:" in result.output

def test_consultar_sin_parametros(runner):
    """Prueba el comando consultar sin parámetros."""
    result = runner.invoke(cli, ['consultar'])
    assert result.exit_code == 0
    assert "Consultando todos los recursos" in result.output

def test_consultar_con_nombre(runner):
    """Prueba el comando consultar con un nombre específico."""
    result = runner.invoke(cli, ['consultar', '--nombre', 'test'])
    assert result.exit_code == 0
    assert "Consultando recurso: test" in result.output

def test_consultar_modo_verboso(runner):
    """Prueba el comando consultar en modo verboso."""
    result = runner.invoke(cli, ['consultar', '--verbose'])
    assert result.exit_code == 0
    assert "Modo verboso activado" in result.output

def test_consultar_nombre_y_verboso(runner):
    """Prueba el comando consultar con nombre y modo verboso."""
    result = runner.invoke(cli, ['consultar', '--nombre', 'test', '--verbose'])
    assert result.exit_code == 0
    assert "Modo verboso activado" in result.output
    assert "Consultando recurso: test" in result.output

def test_help_comando(runner):
    """Prueba la ayuda del comando consultar."""
    result = runner.invoke(cli, ['consultar', '--help'])
    assert result.exit_code == 0
    assert "Consulta información sobre un recurso específico" in result.output 