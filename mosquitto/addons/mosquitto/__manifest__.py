# -*- coding: utf-8 -*-
{
    'name': 'Mosquitto',
    'description': 'Mosquitto Odoo UI',
    'version': '1.0',
    'author': 'Max',
    'website': 'http://comlib.md',
    'license': 'AGPL-3',
    'category': 'Web',
    'depends': [
        'web',
    ],
    'installable': True,
    'application': True,
    'qweb': [],
    'data': [
        'views/menu.xml',
        'views/topic.xml',
        'views/account.xml',
        'views/acl.xml',
    ],
    'installable': True,
}
