# -*- coding: utf-8 -*-

{
    "name": "XXX 科技公司",
    "summary": "Latlng 公司",
    "sequence": "0",
    "version": "1.0",
    "author": "Latlng",
    "depends": ["hr", "survey"],
    "data": [
        "security/latlng_security.xml",
        "security/ir.model.access.csv",
        "views/work_log_view.xml",
        "views/passive_evaluate_view.xml",
        "views/start_survey_view.xml",
        "views/survey_view.xml",
        "views/countersign_view.xml",
        "views/latlng_menuitem.xml",
    ],
    "application": True,
    "auto_install": False,
    "installable": True,
}
