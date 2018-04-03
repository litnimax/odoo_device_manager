# -*- coding: utf-8 -*-
{
    'name': "Device Manager",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['mosquitto'],
    'application': True,
    # always loaded
    'data': [
        'security/device/device.xml',
        'security/device/ir.model.access.csv',
        'security/device_admin/device_admin.xml',
        'security/device_admin/ir.model.access.csv',
        'views/application.xml',
        'views/device.xml',
        'views/service.xml',
        'views/image.xml',
        'views/environment.xml',
        'views/device_log.xml',
        'views/views.xml',
        'views/settings.xml',
        'data/settings.xml',
        'data/mqtt_accounts.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo_environment.xml',
        'demo/demo_services.xml',
        'demo/demo_application.xml',
        #'demo/demo_devices.xml',
        'demo/demo_images.xml',
    ],
}
