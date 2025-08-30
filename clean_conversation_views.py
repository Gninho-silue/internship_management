#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de nettoyage des vues en base de données
Supprime les références au champ conversation_id supprimé
"""

import xml.etree.ElementTree as ET
import re

def clean_view_arch(arch_string):
    """Nettoie l'architecture XML d'une vue"""
    if not arch_string:
        return arch_string
    
    # Supprime les références à conversation_id
    cleaned = re.sub(r'<field name="conversation_id"[^>]*/>', '', arch_string)
    cleaned = re.sub(r'<field name="conversation_id"[^>]*>.*?</field>', '', cleaned)
    
    return cleaned

def main():
    print("Script de nettoyage des vues conversation_id")
    print("=" * 50)
    
    # Ce script doit être exécuté dans Odoo avec l'API
    print("Ce script doit être exécuté dans Odoo avec l'API")
    print("Utilisez la commande suivante dans Odoo :")
    print("")
    print("python -c \"")
    print("import odoo")
    print("odoo.cli.main()")
    print("\" shell -d odoo17 -c config/odoo.conf")
    print("")
    print("Puis exécutez le code de nettoyage dans le shell Odoo")

if __name__ == "__main__":
    main()
