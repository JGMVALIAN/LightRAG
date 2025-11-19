"""
Spanish Legal Corpus - Definitions and metadata for Spanish legislation
Covers procurement (LCSP), administrative law (LPAC), and defense legislation
"""
from datetime import date
from typing import Dict, List, Optional
from enum import Enum


class LegalHierarchy(Enum):
    """Spanish legal hierarchy levels (lower number = higher rank)"""
    CONSTITUCION = 1
    LEY_ORGANICA = 2
    LEY_ORDINARIA = 3
    REAL_DECRETO_LEGISLATIVO = 4
    REAL_DECRETO_LEY = 5
    REAL_DECRETO = 6
    ORDEN_MINISTERIAL = 7
    RESOLUCION = 8
    CIRCULAR = 9


class LegalArea(Enum):
    """Legal practice areas"""
    CONTRATACION = "contratacion"
    ADMINISTRATIVO = "administrativo"
    DEFENSA = "defensa"
    GENERAL = "general"


# Spanish Procurement Laws (Contratación Pública)
SPANISH_PROCUREMENT_LAWS = {
    "lcsp_2017": {
        "id": "ley-9-2017",
        "title": "Ley 9/2017, de Contratos del Sector Público",
        "short_title": "LCSP",
        "publication_date": date(2017, 11, 8),
        "entry_force_date": date(2018, 3, 9),
        "boe": "BOE-A-2017-12902",
        "hierarchy": LegalHierarchy.LEY_ORDINARIA,
        "area": LegalArea.CONTRATACION,
        "active": True,
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2017-12902",
        "key_articles": {
            "art_1": "Objeto y finalidad de la Ley",
            "art_99": "Procedimiento abierto",
            "art_131": "Procedimiento abierto simplificado",
            "art_159": "Procedimiento con negociación",
            "art_168": "Procedimiento de diálogo competitivo",
            "art_177": "Procedimiento de asociación para la innovación",
            "art_317": "Prerrogativas de la Administración",
            "art_190": "Garantías exigibles",
        },
        "keywords": ["contratación pública", "procedimientos", "garantías", "criterios adjudicación", "LCSP"]
    },
    "ley_concesiones_2003": {
        "id": "ley-24-2011",
        "title": "Ley 24/2011, de Contratos del Sector Público en los ámbitos de la defensa y de la seguridad",
        "short_title": "Ley Contratos Defensa",
        "publication_date": date(2011, 8, 1),
        "boe": "BOE-A-2011-13371",
        "hierarchy": LegalHierarchy.LEY_ORDINARIA,
        "area": LegalArea.DEFENSA,
        "active": True,
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2011-13371",
        "key_articles": {
            "art_1": "Objeto y ámbito de aplicación",
            "art_4": "Exclusiones del ámbito de aplicación",
            "art_13": "Procedimientos de adjudicación",
        },
        "keywords": ["defensa", "seguridad", "material de defensa", "contratos clasificados"]
    },
    "rd_reglamento_lcsp": {
        "id": "rd-1098-2001",
        "title": "Real Decreto 1098/2001, Reglamento General de la Ley de Contratos",
        "short_title": "RGLCAP",
        "publication_date": date(2001, 10, 12),
        "boe": "BOE-A-2001-19995",
        "hierarchy": LegalHierarchy.REAL_DECRETO,
        "area": LegalArea.CONTRATACION,
        "active": True,
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2001-19995",
        "key_articles": {
            "art_99": "Documentación inicial del expediente",
            "art_138": "Contenido de los pliegos",
        },
        "keywords": ["reglamento", "pliegos", "expediente", "procedimiento administrativo"]
    }
}

# Spanish Administrative Law
SPANISH_ADMINISTRATIVE_LAWS = {
    "lpac_2015": {
        "id": "ley-39-2015",
        "title": "Ley 39/2015, del Procedimiento Administrativo Común de las Administraciones Públicas",
        "short_title": "LPAC",
        "publication_date": date(2015, 10, 1),
        "entry_force_date": date(2016, 10, 2),
        "boe": "BOE-A-2015-10565",
        "hierarchy": LegalHierarchy.LEY_ORDINARIA,
        "area": LegalArea.ADMINISTRATIVO,
        "active": True,
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2015-10565",
        "key_articles": {
            "art_21": "Plazos",
            "art_30": "Términos y plazos",
            "art_82": "Iniciación del procedimiento",
            "art_121": "Principios de la potestad sancionadora",
            "art_63": "Requisitos de validez de los actos",
        },
        "keywords": ["procedimiento administrativo", "plazos", "notificaciones", "actos administrativos"]
    },
    "lrjsp_2015": {
        "id": "ley-40-2015",
        "title": "Ley 40/2015, de Régimen Jurídico del Sector Público",
        "short_title": "LRJSP",
        "publication_date": date(2015, 10, 1),
        "entry_force_date": date(2016, 10, 2),
        "boe": "BOE-A-2015-10566",
        "hierarchy": LegalHierarchy.LEY_ORDINARIA,
        "area": LegalArea.ADMINISTRATIVO,
        "active": True,
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2015-10566",
        "key_articles": {
            "art_3": "Principios generales",
            "art_9": "Funcionamiento electrónico del sector público",
        },
        "keywords": ["sector público", "administración electrónica", "competencias"]
    },
    "ljca_1998": {
        "id": "ley-29-1998",
        "title": "Ley 29/1998, reguladora de la Jurisdicción Contencioso-administrativa",
        "short_title": "LJCA",
        "publication_date": date(1998, 7, 13),
        "boe": "BOE-A-1998-16718",
        "hierarchy": LegalHierarchy.LEY_ORDINARIA,
        "area": LegalArea.ADMINISTRATIVO,
        "active": True,
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-1998-16718",
        "key_articles": {
            "art_1": "Extensión de la jurisdicción",
            "art_25": "Plazos de interposición del recurso",
            "art_45": "Medidas cautelares",
        },
        "keywords": ["contencioso-administrativo", "recursos", "jurisdicción"]
    }
}

# Spanish Defense and Security Laws
SPANISH_DEFENSE_LAWS = {
    "lodn_2005": {
        "id": "lo-5-2005",
        "title": "Ley Orgánica 5/2005, de la Defensa Nacional",
        "short_title": "LODN",
        "publication_date": date(2005, 11, 17),
        "boe": "BOE-A-2005-18933",
        "hierarchy": LegalHierarchy.LEY_ORGANICA,
        "area": LegalArea.DEFENSA,
        "active": True,
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2005-18933",
        "key_articles": {
            "art_1": "Fines de la Defensa Nacional",
            "art_31": "Consejo de Defensa Nacional",
        },
        "keywords": ["defensa nacional", "fuerzas armadas", "política de defensa"]
    },
    "ley_material_defensa": {
        "id": "ley-8-2014",
        "title": "Ley 8/2014, sobre el control del comercio exterior de material de defensa",
        "short_title": "Ley Control Material Defensa",
        "publication_date": date(2014, 12, 4),
        "boe": "BOE-A-2014-12628",
        "hierarchy": LegalHierarchy.LEY_ORDINARIA,
        "area": LegalArea.DEFENSA,
        "active": True,
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2014-12628",
        "key_articles": {
            "art_1": "Objeto y ámbito de aplicación",
            "art_7": "Autorizaciones de exportación",
        },
        "keywords": ["material de defensa", "comercio exterior", "exportación armamento"]
    },
    "lo_seg_nacional": {
        "id": "lo-14-2015",
        "title": "Ley Orgánica 14/2015, del Sistema de Seguridad Nacional",
        "short_title": "LSN",
        "publication_date": date(2015, 10, 14),
        "boe": "BOE-A-2015-11109",
        "hierarchy": LegalHierarchy.LEY_ORGANICA,
        "area": LegalArea.DEFENSA,
        "active": True,
        "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2015-11109",
        "key_articles": {
            "art_1": "Objeto de la Ley",
            "art_6": "Consejo de Seguridad Nacional",
        },
        "keywords": ["seguridad nacional", "infraestructuras críticas", "ciberseguridad"]
    }
}


def get_all_laws() -> Dict[str, Dict]:
    """Get all Spanish laws from all areas"""
    return {
        **SPANISH_PROCUREMENT_LAWS,
        **SPANISH_ADMINISTRATIVE_LAWS,
        **SPANISH_DEFENSE_LAWS
    }


def get_laws_by_area(area: LegalArea) -> Dict[str, Dict]:
    """Get laws filtered by legal area"""
    all_laws = get_all_laws()
    return {
        key: law for key, law in all_laws.items()
        if law.get("area") == area
    }


def get_law_by_id(law_id: str) -> Optional[Dict]:
    """Get law by BOE identifier"""
    all_laws = get_all_laws()
    for law in all_laws.values():
        if law.get("id") == law_id or law.get("boe") == law_id:
            return law
    return None


def get_laws_by_hierarchy(hierarchy: LegalHierarchy) -> Dict[str, Dict]:
    """Get laws filtered by hierarchy level"""
    all_laws = get_all_laws()
    return {
        key: law for key, law in all_laws.items()
        if law.get("hierarchy") == hierarchy
    }
