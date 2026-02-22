from flask import render_template
from flask_login import login_required

from flaskr.modules import bp


@bp.route("/modules")
@login_required
def modules_page():
    return render_template("modules/module.html", title="Modules")


# @bp.route("/modules/<module_name>")
# @login_required
# def module():
