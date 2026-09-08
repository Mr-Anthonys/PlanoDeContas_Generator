"""Persistência das últimas configurações usadas pelo usuário.

Os valores de referência (TipoArq, InterfaceComum, InterfaceFormaPgto) NÃO são
duplicados aqui — apenas as últimas escolhas do usuário, gravadas de volta no
mesmo config.json (chave "ultimas_configuracoes"), que é a única fonte de
verdade também para os dados de referência (ver reference_loader.py).
"""

import json

from src.models.account import GenerationSettings
from src.utils.constants import CONFIG_PATH

DEFAULTS = {
    "ultimo_diretorio": "",
    "ultimo_tipo_arq": "Emolumentos",
    "ultimo_tipo_conta": "Recebimento",
    "ultimo_regime": "Titular",
    "ultima_qtd_marcadores": 1,
    "ultimo_historico1": "Qtd",
    "ultimo_historico2": "",
    "ultimo_historico3": "",
    "ultimo_interface_comum": "Emolumentos",
    "ultimo_interface_forma_pgto": "Emolumentos",
}


def _read_config(caminho: str = None) -> dict:
    caminho = caminho or CONFIG_PATH
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_config(config: dict, caminho: str = None) -> None:
    caminho = caminho or CONFIG_PATH
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def load_last_settings(caminho: str = None) -> dict:
    """Retorna o dicionário 'ultimas_configuracoes', com valores padrão para
    chaves ausentes (não falha se o config.json estiver desatualizado)."""
    try:
        config = _read_config(caminho)
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULTS)
    salvo = config.get("ultimas_configuracoes", {})
    resultado = dict(DEFAULTS)
    resultado.update(salvo)
    return resultado


def save_last_settings(settings: GenerationSettings, ultimo_diretorio: str = "", caminho: str = None) -> None:
    config = _read_config(caminho)
    config["ultimas_configuracoes"] = {
        "ultimo_diretorio": ultimo_diretorio,
        "ultimo_tipo_arq": settings.tipo_arq,
        "ultimo_tipo_conta": settings.tipo_conta,
        "ultimo_regime": settings.regime,
        "ultima_qtd_marcadores": settings.qtd_marcadores,
        "ultimo_historico1": settings.historico1,
        "ultimo_historico2": settings.historico2,
        "ultimo_historico3": settings.historico3,
        "ultimo_interface_comum": settings.interface_comum,
        "ultimo_interface_forma_pgto": settings.interface_forma_pgto,
    }
    _write_config(config, caminho)


DEFAULTS_CONEXAO = {
    "ultimo_servidor": "",
    "ultimo_usuario": "",
    "ultimo_cliente_parametros": "",
}

DEFAULTS_CRIAR_BASE = {
    "prod_servidor": "",
    "prod_usuario": "",
    "dev_servidor": "",
    "dev_usuario": "",
    "nome_dev": "",
    "diretorio_dev": "",
}


def load_last_connection(caminho: str = None) -> dict:
    """Servidor/usuário do último login (nunca a senha — essa não é
    persistida em disco, é sempre digitada de novo)."""
    try:
        config = _read_config(caminho)
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULTS_CONEXAO)
    salvo = config.get("ultima_conexao", {})
    resultado = dict(DEFAULTS_CONEXAO)
    resultado.update(salvo)
    return resultado


def save_last_connection(servidor: str, usuario: str, caminho: str = None, ultimo_cliente_parametros: str = "") -> None:
    config = _read_config(caminho)
    config["ultima_conexao"] = {
        "ultimo_servidor": servidor,
        "ultimo_usuario": usuario,
        "ultimo_cliente_parametros": ultimo_cliente_parametros,
    }
    _write_config(config, caminho)


def load_last_criar_base_settings(caminho: str = None) -> dict:
    """Campos não-sensíveis do último provisionamento de base (servidor/
    usuário de produção e de dev, nome de exibição e diretório de dev).
    Nenhuma senha é persistida em disco."""
    try:
        config = _read_config(caminho)
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULTS_CRIAR_BASE)
    salvo = config.get("ultima_criacao_base", {})
    resultado = dict(DEFAULTS_CRIAR_BASE)
    resultado.update(salvo)
    return resultado


def save_last_criar_base_settings(dados: dict, caminho: str = None) -> None:
    config = _read_config(caminho)
    config["ultima_criacao_base"] = {
        "prod_servidor": dados.get("prod_servidor", ""),
        "prod_usuario": dados.get("prod_usuario", ""),
        "dev_servidor": dados.get("dev_servidor", ""),
        "dev_usuario": dados.get("dev_usuario", ""),
        "nome_dev": dados.get("nome_dev", ""),
        "diretorio_dev": dados.get("diretorio_dev", ""),
    }
    _write_config(config, caminho)


def restore_defaults(caminho: str = None) -> dict:
    config = _read_config(caminho)
    config["ultimas_configuracoes"] = dict(DEFAULTS)
    _write_config(config, caminho)
    return dict(DEFAULTS)


def settings_from_dict(dados: dict) -> GenerationSettings:
    return GenerationSettings(
        regime=dados.get("ultimo_regime", "Titular"),
        tipo_conta=dados.get("ultimo_tipo_conta", "Recebimento"),
        tipo_arq=dados.get("ultimo_tipo_arq", "Emolumentos"),
        interface_comum=dados.get("ultimo_interface_comum", "Emolumentos"),
        interface_forma_pgto=dados.get("ultimo_interface_forma_pgto", "Emolumentos"),
        qtd_marcadores=dados.get("ultima_qtd_marcadores", 1),
        historico1=dados.get("ultimo_historico1", ""),
        historico2=dados.get("ultimo_historico2", ""),
        historico3=dados.get("ultimo_historico3", ""),
    )
