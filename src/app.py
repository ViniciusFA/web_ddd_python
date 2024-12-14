from flask import Flask, Blueprint, render_template,  g, session, request, flash, redirect, url_for, session

app = Flask(__name__)

# Criando o Blueprint para autenticação
auth_bp = Blueprint('auth', __name__, template_folder='templates/auth')

# Rota de login
@auth_bp.route('/login')
def login():
        username = request.form['username']
        password = request.form['password']
        
        # Verifique se as credenciais são válidas (exemplo simplificado)
        user = get_user_by_username(username)
        if user and check_password_hash(user.password, password):  # Verifica a senha
            session['user_id'] = user.id  # Armazena o ID do usuário na sessão
            return redirect(url_for('home'))
        else:
            flash('Login inválido')
            #return redirect(url_for('auth.login'))
            return render_template('auth/login.html')
    #return render_template('auth/login.html')

# Rota de registro
@auth_bp.route('/register')
def register():
    return render_template('auth/register.html')

# Registrando o Blueprint
app.register_blueprint(auth_bp, url_prefix='/auth')

@app.route('/')  # Define a URL raiz (/) para a função home.
def home():
    return render_template('base.html', title="Login", name="Usuário")

@app.route('/sobre')
def sobre():
    return "Esta é uma página sobre a aplicação."

#Criar uma camada que conversa com o banco de dados
def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

@app.before_request
def load_user():
    #Verifica se o usuário está autenticado e carrega os dados na variável global `g`.
    user_id = session.get('user_id')
    if user_id:
        g.user = get_user_by_id(user_id)  # Função para recuperar os dados do usuário a partir do ID
    else:
        g.user = None

if __name__ == '__main__':
    app.run(debug=True)  # Ativa o modo de desenvolvimento