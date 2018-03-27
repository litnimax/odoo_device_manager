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
    'depends': ['base'],
    'application': True,
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        #'views/templates.xml',
        'views/application.xml',
        'views/device.xml',
        'views/service.xml',
        'views/image.xml',
        'views/variable.xml',
        'views/views.xml',        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo_variables.xml',
        'demo/demo_images.xml',
        'demo/demo_services.xml',
        'demo/demo_devices.xml',
        'demo/demo_application.xml',
    ],
}