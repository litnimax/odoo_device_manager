FROM odoo:10.0

WORKDIR /mnt/extra-addons
USER root

COPY odoo/requirements.txt /mnt/extra-addons
RUN pip install -r requirements.txt

COPY odoo/addons/ /mnt/extra-addons/

USER odoo

CMD ["odoo", "--workers=0", "--db-filter=test", "--database=test", "--log-level=debug_sql"]
