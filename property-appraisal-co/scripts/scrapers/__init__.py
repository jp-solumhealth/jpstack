from . import fincaraiz, metrocuadrado, vivienda, mercadolibre  # noqa: F401

ALL = [fincaraiz, metrocuadrado, vivienda, mercadolibre]


def by_name(name: str):
    for m in ALL:
        if m.SOURCE == name:
            return m
    raise KeyError(name)
