# -*- coding: utf-8 -*-
{
    'name': 'Eclipse Mosquitto™ Manager',
    'summary': 'An open source MQTT broker management interface',
    'description': '''An open source MQTT broker management interface for 
Eclipse Mosquitto, an open source (EPL/EDL licensed) message broker that implements the MQTT protocol versions 3.1 and 3.1.1. Mosquitto is lightweight and is suitable for use on all devices from low power single board computers to full servers.
The MQTT protocol provides a lightweight method of carrying out messaging using a publish/subscribe model. This makes it suitable for Internet of Things messaging such as with low power sensors or mobile devices such as phones, embedded computers or microcontrollers.
''',
    'version': '1.0',    
    'author': 'Odooino LLC',
    'website': 'http://odooino.com',
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
    'price': 101,
    'currency': 'EUR',
}