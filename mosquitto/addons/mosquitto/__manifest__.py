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
        'security/mqtt_admin.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/topic.xml',
        'views/account.xml',
        'views/acl.xml',
    ],
    'installable': True,
}
