from flask import Blueprint, render_template, request, redirect, flash
from forms.Login import LoginForm
from forms.ResetPassword import ResetPasswordForm
from models.usuario import Usuario,loginLog
from models.histDB import PasswordHistories
from dotenv import load_dotenv
from db.db import db
import datetime

from lib.jwt import allowed_roles,token_required,createToken,decodeToken
login = Blueprint('login', __name__, template_folder='templates')
load_dotenv()

TIME_TO_BLOCK = 5

def save_login_log(user_id, estado):
    login_log = loginLog(user_id=user_id, estado=estado)
    db.session.add(login_log)
    db.session.commit()

def user_is_blocked(user):
    if user.is_blocked:
        if user.blocked_until:
            return True
        else:
            return False
    else:
        return False
    

def block_user_until(user, minutes):
    user.is_blocked = True
    user.blocked_until = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    db.session.commit()

def unblock_user(user):
    user.is_blocked = False
    user.blocked_until = None
    db.session.commit()

def check_user_blocked(user):
    if user.is_blocked:
        if user.blocked_until:
            if user.blocked_until < datetime.datetime.now():
                unblock_user(user)
            else:
                return True
        else:
            return False
    else:
        return False
    
def check_last_logins(user,intentos):
    last_logins = loginLog.query.filter_by(user_id=user.id).order_by(loginLog.fecha_login.desc()).limit(intentos).all()
    if len(last_logins) == 3:
        if last_logins[0].estado == 'incorrecto' and last_logins[1].estado == 'incorrecto' and last_logins[2].estado == 'incorrecto':
            block_user_until(user, TIME_TO_BLOCK)
            return True
        else:
            return False
    else:
        return False

def get_last_login_time(user):
    last_login = loginLog.query.filter_by(user_id=user.id).order_by(loginLog.fecha_login.desc()).first()
    return last_login.fecha_login

@login.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm(request.form)
    token = request.cookies.get('token')
    if token:
        return redirect('/home')

    if request.method == 'POST' and form.validate():
        email = form.correo.data
        contraseña = form.password.data

        # Consultar si el usuario existe
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario:
            # Verificar si el usuario está bloqueado
            if check_user_blocked(usuario):
                flash('Tu cuenta está bloqueada. Intenta más tarde.', 'danger')
                return render_template('pages/login/index.html', form=form)
            
            #advertir al usuario que su cuenta esta bloqueada
            if check_last_logins(usuario, 2):
                flash(f'Advertencia: Si fallas el siguiente intento de inicio de sesión, tu cuenta será bloqueada por {TIME_TO_BLOCK} minutos', 'warning')
                return render_template('pages/login/index.html', form=form)

            # Verificar si los últimos tres logins fueron incorrectos
            if check_last_logins(usuario, 3):
                flash(f'Tu cuenta ha sido bloqueada debido a múltiples intentos fallidos de inicio de sesión. Intenta en {TIME_TO_BLOCK} minutos', 'danger')
                return render_template('pages/login/index.html', form=form)

            if usuario.password == contraseña:
                # Guardar como cookie el token
                response = redirect('/home')
                response.set_cookie('correo', email)

                # Guardar en la tabla login_log
                save_login_log(usuario.id, 'correcto')

                #mostrar un flash con la fecha y hora del ultimo inicio de sesion
                last_login = get_last_login_time(usuario)
                flash(f'Bienvenido de vuelta. Tu último inicio de sesión fue el {last_login}', 'success')
                return response
            else:
                flash('Usuario o contraseña incorrectos', 'danger')
                # Guardar en la tabla login_log
                save_login_log(usuario.id, 'incorrecto')

                return render_template('pages/login/index.html', form=form)
        else:
            # Guardar en la tabla login_log
            save_login_log(0, 'incorrecto')
            flash('Usuario no existe', 'danger')

        return render_template('pages/login/index.html', form=form)
        
    return render_template('pages/login/index.html', form=form)




@login.route('/resetPassword', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm(request.form)
    try:
        token = request.cookies.get('token')
        if token:
            return redirect('/home')

        email = form.correo.data
        password = form.password.data
        confirm_password = form.confirm_password.data

        if request.method == 'POST':
            usuario = Usuario.query.filter_by(email=email).first()
            if not usuario:
                flash('Usuario no existe', 'danger')
            elif password != confirm_password:
                flash('Las contraseñas no coinciden', 'danger')
            else:
                can_continue = PasswordHistories.query.filter_by(user_id=usuario.id, password=password).all()
                if can_continue:
                    flash('La contraseña ya ha sido utilizada anteriormente', 'danger')
                else:
                    usuario.password = password
                    db.session.commit()
                    return redirect('/login')
        
    except Exception as e:
        print(e)
        flash('Error al enviar el email', 'danger')

    return render_template('pages/login/enviar_email.html', form=form)





@login.route('/404')
def not_found():
    return "Not found", 404



@login.route('/logout')
def logout():
    response = redirect('/login')
    response.set_cookie('token', '', expires=0)
    return response

