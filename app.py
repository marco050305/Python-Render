
from flask import Flask, render_template, request, session, redirect
import sqlite3

app = Flask(__name__, template_folder='templates')
app.secret_key = 'superkey'

def get_db_connection():
    conn = sqlite3.connect('bd02.db')
    conn.row_factory = sqlite3.Row
    return conn


def crear_tablas():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Crear tabla TIPOCARTERA
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS TIPOCARTERA (
        CODTIPCAR INTEGER PRIMARY KEY AUTOINCREMENT,
        NOMBTIPCAR TEXT NOT NULL
    )
    ''')

    # Crear tabla USUARIO
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS USUARIO (
        IDUSUARIO INTEGER PRIMARY KEY AUTOINCREMENT,
        CORREO TEXT NOT NULL UNIQUE,
        CONTRASENA TEXT NOT NULL
    )
    ''')

    # Crear tabla CARTERA sin IDUSUARIO
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS CARTERA (
        CODCAR INTEGER PRIMARY KEY AUTOINCREMENT,
        DESCRIPCAR TEXT NOT NULL,
        PRECIOCAR TEXT NOT NULL,
        FECHACAR TEXT NOT NULL,
        CODTIPCAR INTEGER NOT NULL,
        FOREIGN KEY (CODTIPCAR) REFERENCES TIPOCARTERA(CODTIPCAR) ON DELETE RESTRICT ON UPDATE RESTRICT
    )
    ''')

    conn.commit()
    conn.close()
    print("Tablas creadas correctamente.")


def insertar_registros_tipocartera():
    conexion = sqlite3.connect('bd02.db')
    cursor = conexion.cursor()

    cursor.execute("SELECT COUNT(*) FROM TIPOCARTERA;")
    count = cursor.fetchone()[0]

    if count == 0:
        datos = [
            (1, 'ANDINO'),
            (2, 'TRADICIONAL'),
            (3, 'SELVATICO'),
            (4, 'COSTEÑO')
        ]
        cursor.executemany("INSERT INTO TIPOCARTERA VALUES (?, ?);", datos)
        conexion.commit()
        print("Registros insertados en TIPOCARTERA.")
    else:
        print("La tabla TIPOCARTERA ya tiene datos. No se insertó nada.")

    conexion.close()

#*===========================================================================================================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def iniciar():
    return render_template('login.html')

@app.route('/acceso-login', methods=["GET","POST"])
def login():
    if request.method == 'POST':
        correo = request.form.get('txtCorreo')
        password = request.form.get('txtPassword')

        if correo and password:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT * FROM USUARIO WHERE CORREO = ? AND CONTRASENA = ?', (correo, password))
            account = cur.fetchone()
            conn.close()

            if account:
                session['logueado'] = True
                session['id'] = account['IDUSUARIO']
                return redirect('/bienvenida')
            else:
                return render_template('login.html', mensaje="Usuario o contraseña INCORRECTOS")
        else:
            return render_template('login.html', mensaje="Por favor, complete todos los campos.")
    return render_template('login.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/crear-registro', methods=['POST'])
def crear_registro():
    correo = request.form.get('txtCorreo')
    password = request.form.get('txtPassword')

    if correo and password:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO USUARIO (CORREO, CONTRASENA) VALUES (?, ?)", (correo, password))
            conn.commit()
            conn.close()
            return render_template('login.html', mensaje2='Usuario Registrado Correctamente')
        except sqlite3.IntegrityError:
            return render_template('registro.html', mensaje="Correo ya registrado")
    else:
        return render_template('registro.html', mensaje="Por favor, complete todos los campos.")

@app.route('/bienvenida')
def bienevida2():
    return render_template('bienvenida.html')

@app.route('/registrar-cartera')
def registrarCartera():
    if 'logueado' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM TIPOCARTERA')
        tipos = cursor.fetchall()
        conn.close()
        return render_template('RegistrarCartera.html', tipos=tipos)
    else:
        return redirect('/')

@app.route('/guardar-cartera', methods=['POST'])
def guardar_cartera():
    descripcion = request.form['descripcion']
    precio = request.form['precio']
    fecha = request.form['fecha']
    tipo = request.form['tipo']

    if descripcion and precio and fecha and tipo:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO CARTERA (DESCRIPCAR, PRECIOCAR, FECHACAR, CODTIPCAR)
            VALUES (?, ?, ?, ?)
        ''', (descripcion, precio, fecha, tipo))
        conn.commit()
        cursor.execute('SELECT * FROM TIPOCARTERA')
        tipos = cursor.fetchall()
        conn.close()
        return render_template('RegistrarCartera.html', tipos=tipos, mensaje="Registro insertado correctamente.")
    else:
        return "Faltan datos obligatorios", 400


@app.route('/consultar-carteras')
def consultar_carteras():
    if 'logueado' in session:
        tipo_filtro = request.args.get('tipoFiltro', default='', type=str)

        conn = get_db_connection()
        cur = conn.cursor()

        # Obtener todos los tipos para llenar el select
        cur.execute('SELECT * FROM TIPOCARTERA')
        tipos = cur.fetchall()

        if tipo_filtro and tipo_filtro.isdigit():
            # Filtrar por tipo
            cur.execute('''
                SELECT C.CODCAR, C.DESCRIPCAR, C.PRECIOCAR, C.FECHACAR, 
                       C.CODTIPCAR, T.NOMBTIPCAR
                FROM CARTERA C
                JOIN TIPOCARTERA T ON C.CODTIPCAR = T.CODTIPCAR
                WHERE C.CODTIPCAR = ?
                ORDER BY C.CODCAR
            ''', (tipo_filtro,))
        else:
            # Sin filtro
            cur.execute('''
                SELECT C.CODCAR, C.DESCRIPCAR, C.PRECIOCAR, C.FECHACAR, 
                       C.CODTIPCAR, T.NOMBTIPCAR
                FROM CARTERA C
                JOIN TIPOCARTERA T ON C.CODTIPCAR = T.CODTIPCAR
                ORDER BY C.CODCAR
            ''')

        carteras = cur.fetchall()
        conn.close()

        return render_template('ConsultarCartera.html', carteras=carteras, tipos=tipos, tipoFiltro=int(tipo_filtro) if tipo_filtro.isdigit() else '')

    else:
        return redirect('/')


@app.route('/editar-cartera/<int:id>')
def editar_cartera(id):
    if 'logueado' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM CARTERA WHERE CODCAR = ?', (id,))
    cartera = cur.fetchone()

    cur.execute('SELECT * FROM TIPOCARTERA')
    tipos = cur.fetchall()
    conn.close()

    return render_template('ActualizarCartera.html', cartera=cartera, tipos=tipos)

@app.route('/actualizar-cartera/<int:id>', methods=['POST'])
def actualizar_cartera(id):
    descripcion = request.form['descripcion']
    precio = request.form['precio']
    fecha = request.form['fecha']
    tipo = request.form['tipo']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        UPDATE CARTERA 
        SET DESCRIPCAR = ?, PRECIOCAR = ?, FECHACAR = ?, CODTIPCAR = ?
        WHERE CODCAR = ?
    ''', (descripcion, precio, fecha, tipo, id))
    conn.commit()
    conn.close()

    return redirect('/consultar-carteras')

@app.route('/eliminar-cartera/<int:id>')
def eliminar_cartera(id):
    if 'logueado' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM CARTERA WHERE CODCAR = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/consultar-carteras')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    crear_tablas()
    insertar_registros_tipocartera()
    app.run(debug=True, port=5000)
