from flask import Flask, Blueprint, render_template,  g, session, request, flash, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate random secret key 

# Criando o Blueprint para autenticação
auth_template = Blueprint('auth', __name__, template_folder='templates/auth')

# Rota de login
@auth_template.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')  # Captura o valor do campo 'username'
        password = request.form.get('password')  # Captura o valor do campo 'password'
        
        # Aqui você pode adicionar a lógica de autenticação
        if username == "test" and password == "1234":  # Exemplo simplificado
            session['user_id'] = username
            return render_template('home.html')
        else:
            flash("Invalid username or password")
    return render_template('login.html')

# Rota de registro
@auth_template.route('/register')
def register():
    return render_template('register.html')

# Registrando o Blueprint
app.register_blueprint(auth_template, url_prefix='/auth')

@app.route('/')  # Define a URL raiz (/) para a função home.
def home():
    return render_template('base.html', title="Login", name="Usuário")

# Rota da Home
app.route('/home')
def register():
    return render_template('home.html')

@app.route('/sobre')
def sobre():
    return "Esta é uma página sobre a aplicação."

#Criar uma camada que conversa com o banco de dados
# def get_user_by_username(username):
#     return User.query.filter_by(username=username).first()

# @app.before_request # cada pagina faz uma resquisicao na base pra verificar se o usuario está autenticado
# def load_user():
    #Verifica se o usuário está autenticado e carrega os dados na variável global `g`.
    #user_id = session.get('user_id')
    #print(user_id)
    # if user_id:
    #     g.user = get_user_by_id(user_id)  # Função para recuperar os dados do usuário na base de dados a partir do ID
    # else:
    #     g.user = None

if __name__ == '__main__':
    app.run(debug=True)  # Ativa o modo de desenvolvimento