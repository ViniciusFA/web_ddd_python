from flask import Flask, Blueprint, render_template,  g, session, request, flash, redirect, url_for, session
import os
from sys import path
from os.path import abspath, dirname, join

# Adicionar o caminho do diretório 5-Domain ao sys.path
BASE_DIR = dirname(dirname(abspath(__file__)))  # Caminho do diretório principal
path.append(join(BASE_DIR, "5-Domain/Model"))
# Mock database for messages
messages = []

from model import User, db  # Importa o db do arquivo model.py

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate random secret key 

# Configurar o banco de dados SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"


# Criando o Blueprint para autenticação
auth_template = Blueprint('auth', __name__, template_folder='templates/auth')

# Rota de login
@auth_template.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')  # Captura o valor do campo 'username'
        password = request.form.get('password')  # Captura o valor do campo 'password'

        existing_user = get_user_by_username_and_password(username, password)

        # Aqui você pode adicionar a lógica de autenticação
        if existing_user:  # If user exists
            session['user_id'] = username
            return redirect('/home')
        else:
            flash("Invalid username or password")
    return render_template('login.html')

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
            flash("Todos os campos são obrigatórios!", "error")
            return redirect(url_for('auth.register'))
        
        if password != confirmpassword:
            flash("A senha e a confirmação de senha não conferem!", "error")
            return redirect(url_for('auth.register'))      
        
        # Verificar se o usuário já existe
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Usuário já existe. Tente outro nome.", "error")
            return redirect(url_for('auth.register'))

        # Criar um novo usuário e salvar no banco
        new_user = User(username=username, password=password, email=email)
        db.session.add(new_user)
        db.session.commit()

        flash("Usuário registrado com sucesso!", "success")
        return redirect(url_for('auth.login'))  # Redirecionar para a página de login

    return render_template('register.html')

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

    return render_template('forgot_password.html')

# Registrando o Blueprint
app.register_blueprint(auth_template, url_prefix='/auth')

@app.route('/')  # Define a URL raiz (/) para a função home.
def home():
    return render_template('base.html', title="Login", name="Usuário")

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
    return render_template('home.html', messages=messages)

def ai_chat_response(user_message):
    """
    Mock AI response generator. Replace this with actual AI logic (e.g., OpenAI GPT).
    """
    responses = {
        "hello": "Hi there! How can I assist you today?",
        "how are you": "I'm just a bunch of code, but I'm here to help you!",
        "bye": "Goodbye! Have a great day!"
    }
    default_response = "I'm sorry, I didn't understand that. Can you rephrase?"
    return responses.get(user_message.lower(), default_response)

# Inicializar o SQLAlchemy com a aplicação
db.init_app(app)

with app.app_context():
    db.create_all()

#Criar uma camada que conversa com o banco de dados
def get_user_by_username_and_password(username, password):
    return User.query.filter_by(username=username, password=password).first()

#Criar uma camada que conversa com o banco de dados
def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

#Criar uma camada que conversa com o banco de dados
def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

# Simulação de um banco de dados para o exemplo
USERS = {
    1: {"username": "test_user"}
}
    
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')  # Suponha que 'user_id' é salvo na sessão
    if user_id is None:
        g.user = None
    else:
        g.user = USERS.get(user_id)  # Busca o usuário do "banco de dados" fictício

if __name__ == '__main__':
    app.run(debug=True)  # Ativa o modo de desenvolvimento