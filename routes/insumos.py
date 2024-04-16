from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    Response,
    jsonify,
    g,
)
from forms.ProveedorForm import (
    ProveedorForm, ProveedorEditForm, ProveedorDelForm)
from forms.InsumoForm import (InsumoForm, InsumoEditForm, InsumoDelForm)
from forms.MateriaPrimaProveedorForm import (
    MateriaPrimaProveedorForm,
    MateriaPrimaProveedorEditForm,
    MateriaPrimaProveedorDelForm
)
from models.proveedor import Proveedor
from models.usuario import Usuario
from models.Recetas import MateriaPrima
from models.materia_prima_proveedor import MateriaPrimaProveedor
from datetime import datetime
from db.db import db
from lib.jwt import token_required, allowed_roles, createToken, decodeToken
from lib.security import safe

insumos = Blueprint("insumos", __name__, template_folder="templates")


@insumos.route("/insumos", methods=["GET"])
@token_required
@allowed_roles(roles=["admin"])
def index():
    insumos = MateriaPrima.query.all()
    mpp = MateriaPrimaProveedor.query.all()
    proveedores = Proveedor.query.all()

    form = InsumoForm(request.form)
    formEditInsumo = InsumoEditForm(request.form)
    formDelInsumo = InsumoDelForm(request.form)
    formMPP = MateriaPrimaProveedorForm(request.form)
    formMPP.proveedor_id.choices = [
        (p.id, p.nombre_empresa) for p in proveedores]
    formEditMPP = MateriaPrimaProveedorEditForm(request.form)
    formDMPP = MateriaPrimaProveedorDelForm(request.form)

    all_insumos = []
    prov = []

    for p in proveedores:
        prov.append(
            {
                "id": p.id,
                "nombre_empresa": p.nombre_empresa,
            }
        )

    for mp in mpp:
        insumo = MateriaPrima.query.filter_by(id=mp.materiaprima_id).first()
        proveedor = Proveedor.query.filter_by(id=mp.proveedor_id).first()

        if insumo.estatus == False:
            continue
        all_insumos.append(
            {
                "proveedor_id": mp.proveedor_id,
                "materiaprima_id": mp.materiaprima_id,
                "precio": mp.precio,
                "cantidad": mp.cantidad,
                "material": insumo.material,
                "medida": insumo.tipo,
                "presentacion": mp.tipo,
                "empresa": proveedor.nombre_empresa,
            }
        )

    return render_template(
        "pages/insumos/index.html",
        insumos=all_insumos,
        form=form,
        formEditInsumo=formEditInsumo,
        formDelInsumo=formDelInsumo,
        formMPP=formMPP,
        formEditMPP=formEditMPP,
        formDMPP=formDMPP,
        prov=prov,
    )


@insumos.route("/addinsumo", methods=["POST"])
@token_required
@allowed_roles(roles=["admin"])
def new_insumo():
    try:
        form = InsumoForm(request.form)
        formMPP = MateriaPrimaProveedorForm(request.form)

        insumo = MateriaPrima(
            material=safe(form.material.data),
            tipo=safe(form.tipo.data),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        db.session.add(insumo)
        db.session.commit()

        precio = formMPP.precio.data
        precio = float(precio)

        cantidad = formMPP.cantidad.data
        cantidad = int(cantidad)

        presentation = formMPP.tipo.data
        presentation.lower()

        mpp = MateriaPrimaProveedor(
            materiaprima_id=insumo.id,
            proveedor_id=safe(formMPP.proveedor_id.data),
            precio=safe(precio),
            cantidad=safe(cantidad),
            tipo=safe(presentation),
            created_at=datetime.now(),
        )

        db.session.add(mpp)
        db.session.commit()

        flash("Insumo agregado correctamente", "success")
        return redirect("/insumos")
        return redirect("/insumos")
    except Exception as e:
        print(e)
        return e


@insumos.route("/editinsumo", methods=["POST"])
@token_required
@allowed_roles(roles=["admin"])
def ed_insumo():
    try:
        material_id = request.form.get("id")
        mat = MateriaPrima.query.filter_by(id=material_id).first()
        material = safe(request.form.get("material"))
        proveedor = safe(request.form.get("proveedor"))
        medida = safe(request.form.get("medida"))
        presentacion = safe(request.form.get("presentacion"))
        precio = safe(request.form.get("precio"))
        cantidad = safe(request.form.get("cantidad"))
        mpp = MateriaPrimaProveedor.query.filter_by(
            materiaprima_id=mat.id).first()

        mat.material = material if material is not None else mat.material
        mat.tipo = medida if medida is not None else mat.tipo

        mpp.proveedor_id = proveedor if proveedor is not None else mpp.proveedor_id
        mpp.materiaprima_id = mat.id
        mpp.precio = precio if precio is not None else mpp.precio
        mpp.cantidad = cantidad if cantidad is not None else mpp.cantidad
        mpp.tipo = presentacion if presentacion is not None else mpp.tipo
        db.session.commit()

        flash("Insumo editado correctamente", "success")
        return redirect("/insumos")
    except Exception as e:
        flash("Error al editar el insumo", "danger")
        print(e)
        return redirect("/insumos")


@insumos.route("/deleteinsumo", methods=["POST"])
@token_required
@allowed_roles(roles=["admin"])
def del_insumo():
    try:
        materiaprima_id = request.form.get("id")
        mat = MateriaPrima.query.filter_by(id=materiaprima_id).first()

        mat.estatus = False
        db.session.commit()
        flash("Insumo eliminado correctamente", "success")
        return redirect("/insumos")
    except Exception as e:
        print(e)
        flash("Error al eliminar el insumo", "danger")
        return redirect("/insumos")
