#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Funciones auxiliares para importaciones desde el módulo health
"""

def get_institution():
    """
    Obtiene la institución del usuario actual
    Importa desde el módulo health de GNUHealth
    """
    try:
        from trytond.modules.health.core import get_institution as health_get_institution
        return health_get_institution()
    except ImportError:
        # Fallback si no está disponible
        return None


def get_health_professional():
    """
    Obtiene el profesional de salud del usuario actual
    """
    try:
        from trytond.modules.health.core import get_health_professional as health_get_health_professional
        return health_get_health_professional()
    except ImportError:
        return None