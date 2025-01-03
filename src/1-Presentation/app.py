from flask import Flask, Blueprint, render_template, session, request, flash, redirect, url_for, session
from google.cloud.dialogflow_v2 import SessionsClient, types    
import os
from sys import path
from os.path import abspath, dirname, join
from dotenv import load_dotenv
from flask_babel import Babel, _
import aiohttp
import asyncio


load_dotenv()  # Isso carrega automaticamente as variáveis do arquivo .env

base_backend_url_user = "https://localhost:44359/api/User/";

# Adicionar o caminho do diretório 5-Domain ao sys.path
BASE_DIR = dirname(dirname(abspath(__file__)))  # Caminho do diretório principal
path.append(join(BASE_DIR, "5-Domain/Model"))
# Mock database for messages
messages = []

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate random secret key 

#region: Translate Babel

app.config['BABEL_DEFAULT_LOCALE'] = 'pt'
app.config['BABEL_SUPPORTED_LOCALES'] = ['pt', 'en']

babel = Babel(app)

# Função para detectar o idioma
def get_locale():
    # Usar o parâmetro `lang` na URL para detectar o idioma (ex: ?lang=pt)
    lang = request.args.get('lang')
    if lang in app.config['BABEL_SUPPORTED_LOCALES']:
        return lang
    return 'pt'  # Definir o idioma padrão

babel.locale_selector_func = get_locale

#endregion

#region:: Secrets and Configurations

# Configurar o banco de dados SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('DATABASE_URL')

# Configurar as credenciais do Dialogflow
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "dialogflow_credentials.json"

#endregion

#region:: auth_template

# Criando o Blueprint para autenticação
auth_template = Blueprint('auth', __name__, template_folder='templates/auth')

# Rota de login
@auth_template.route('/login', methods=['GET', 'POST'])
def login():
    
    if request.method == 'POST':
        username = request.form.get('username')  # Get the username value
        password = request.form.get('password')  # Get the password value

        # Async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            existing_user = loop.run_until_complete(get_user_by_username_and_password(username, password))
            if(existing_user is None):
                flash(_("UserPasswordInvalid"))
            else:
                session['user_id'] = username
                return redirect('/home')
        except Exception as e:
            flash(f"Error connecting to backend: {str(e)}")
            return render_template('login.html',
                                   login=_("Log In"), username=_("Username"), password=_("Password"),
                                   dontHaveAccount=_("Don't have an account?"), registerHere=_("Register here"),
                                   forgotYourPassword=_("Forgot your password?"), resetItHere=_("Reset it here"))

    return render_template('login.html',
                           login=_("Log In"), username=_("Username"),password=_("Password"), 
                           dontHaveAccount=_("Don't have an account?"), registerHere=_("Register here"),
                           forgotYourPassword=_("Forgot your password?"), resetItHere=_("Reset it here"))

@auth_template.route('/logout')
def logout():
     return render_template('logout.html')

# Rota de registro
@auth_template.route('/register', methods=['GET', 'POST'])
def register():
    #TO DO - Refactorung to insert the code below in their respective layers
    if request.method == 'POST':
        # Captura os dados do formulário
        username = request.form.get('username')
        password = request.form.get('password')
        confirmpassword = request.form.get('confirmpassword') 
        email = request.form.get('email')      

        # Validação básica (campos obrigatórios)
        if not username or not password or not confirmpassword or not email:
            flash(_("AllFieldsMandatory"), "error")
            return redirect(url_for('auth.register'))
        
        if password != confirmpassword:
            flash(_("PasswordConfirmationDoNotMatch"), "error")
            return redirect(url_for('auth.register'))      
        
        # Async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            existing_user = loop.run_until_complete(exists_user_by_username(username))
            if(existing_user):
                flash(_("UserAlreadyExists"))
            else:
                #registrar no back end o usuario
                result = loop.run_until_complete(add_user(username, password, email))
                flash(_("SuccessfullyRegisteredUser"), "success")
                return redirect(url_for('auth.login'))  # Redirect to Login Page
        except Exception as e:
            flash(f"Error connecting to backend: {str(e)}")
            return render_template('login.html',
                                   login=_("Log In"), username=_("Username"), password=_("Password"),
                                   dontHaveAccount=_("Don't have an account?"), registerHere=_("Register here"),
                                   forgotYourPassword=_("Forgot your password?"), resetItHere=_("Reset it here"))

    return render_template('register.html', 
                           register=_("Register"), username=_("Username"),
                           email=_("Email"),password=_("Password"),
                           confirmPassword=_("confirmPassword"))

@auth_template.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    email = None  # Inicialize a variável para evitar o erro de escopo

    if request.method == 'POST':
        email = request.form.get('email')  # Obtenha o e-mail do formulário

        if not email:  # Validação básica
            flash("O campo E-mail é obrigatório!", "error")
        else:
            existing_user = get_user_by_email(email)
            if existing_user:  # Se o usuário existir
                # Lógica para enviar o e-mail de redefinição de senha
                flash('Password reset instructions have been sent to your email.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('No account found with this email address.', 'error')



    return render_template('forgot_password.html', 
                           forgotYourPassword=_("Forgot your password?"), enterYourEmailAddress=_("EnterYourEmailAddress"),
                           email=_("Email"), enterYourEmail=_("EnterYourEmail"))

# Registrando o Blueprint
app.register_blueprint(auth_template, url_prefix='/auth')

#endregion

#region:: app

@app.route('/')  # Define a URL raiz (/) para a função home.
def home():
    welcome = _("Welcome!")
    hello = _("Hello")
    logout = _("Log Out")
    register = _("Register")
    login = _("Log In")
    return render_template('base.html', welcome=welcome, hello=hello, logout=logout, register=register, login=login)

# Rota da Home
@app.route('/home')
def main():
    return render_template('home.html')

@app.route('/sobre')
def sobre():
    return "Esta é uma página sobre a aplicação."

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    global messages

    if request.method == 'POST':
        user_message = request.form.get('message')
        if user_message:
            # Append the user's message
            messages.append({"sender": "You", "text": user_message})

            # Generate a response from the AI
            ai_response = ai_chat_response(user_message)
            messages.append({"sender": "AI", "text": ai_response}) 
        elif request.method == 'GET':
            # Mensagem inicial do agente
            initial_message = ai_chat_response("Oi")
            messages.append({"sender": "AI", "text": initial_message})

    return render_template('home.html', messages=messages)

def ai_chat_response(user_message):
    print(user_message)
    """
    Envia a mensagem do usuário para o Dialogflow e retorna a resposta.
    """
    project_id = os.getenv('PROJECT_ID')  # Substitua pelo ID do seu projeto Dialogflow
    session_id = 10  # Pode ser um identificador único (ex: ID do usuário ou sessão)
    language_code = "pt-BR"  # Substitua pelo idioma configurado no agente

    # Inicializa a sessão do Dialogflow
    session_client = SessionsClient()
    session = session_client.session_path(project_id, session_id)

    # Cria a consulta
    text_input = types.TextInput(text=user_message, language_code=language_code)
    query_input = types.QueryInput(text=text_input)

    # Envia a consulta para o Dialogflow
    response = session_client.detect_intent(session=session, query_input=query_input)

    # Extrai a resposta do agente
    return response.query_result.fulfillment_text

#endregion

#region:: Database Methods - Move it to correct layers

async def get_user_by_username_and_password(username, password):
     connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL 
     async with aiohttp.ClientSession(connector=connector) as session:
        params = {'username': username, 'password': password}
        async with session.get(base_backend_url_user + "GetUserByUsernameAndPassword", params=params) as response:
            if response.status == 200:
                return await response.json()  # User Found
            elif response.status == 204:
                return None  # User was not found
            elif response.status == 404:
                return None  # User was not found
            else:
                raise Exception(f"Backend error: {response.status}")

async def exists_user_by_username(username):
     connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL 
     async with aiohttp.ClientSession(connector=connector) as session:
        params = {'username': username}
        async with session.get(base_backend_url_user + "ExistsUserByUsername", params=params) as response:
            if response.status == 200:
                return await response.json()  # Returns the API Response - True or False
            elif response.status == 204:
                return None  # 
            elif response.status == 404:
                return None  # 
            else:
                raise Exception(f"Backend error: {response.status}")
            
async def add_user(username, password, email):
     connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL 
     async with aiohttp.ClientSession(connector=connector) as session:
        headers = {
            'accept': '*/*',
            'Content-Type': 'application/json'
        }
        data = {
            "username": username,
            "password": password,
            "email": email
        }

        async with session.post(base_backend_url_user, headers=headers, json=data) as response:
            if response.status == 200:
                return await response.json()  # Returns the API Response - True or False
            elif response.status == 204:
                return None  # 
            elif response.status == 404:
                return None  # 
            else:
                raise Exception(f"Backend error: {response.status}")
                        
#endregion
    
# @app.before_request
# def load_logged_in_user():
#     user_id = session.get('user_id')  # Suponha que 'user_id' é salvo na sessão
#     if user_id is None:
#         g.user = None
#     else:
#         g.user = USERS.get(user_id)  # Busca o usuário do "banco de dados" fictício

if __name__ == '__main__':
    app.run(debug=True)  # Ativa o modo de desenvolvimento