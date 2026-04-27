from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
import sqlite3, hashlib, os, json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)
DB = 'digiaudit.db'

# ── DB ──────────────────────────────────────────────────────────────────────
def get_db():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'auditor',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sector TEXT,
            size TEXT,
            contact TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            auditor_id INTEGER NOT NULL,
            status TEXT DEFAULT 'in_progress',
            global_score REAL,
            level TEXT,
            scores_json TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        );
    ''')
    # Admin por defecto
    pw = hashlib.sha256('admin123'.encode()).hexdigest()
    try:
        db.execute("INSERT INTO users (name, email, password, role) VALUES (?,?,?,?)",
                   ('Admin', 'admin@digiaudit.com', pw, 'admin'))
        db.commit()
    except:
        pass
    db.close()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ── Auth ─────────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Datos auditoría ──────────────────────────────────────────────────────────
DIMS = [
    {'id': 'est', 'name': 'Estrategia digital', 'color': '#7F77DD',
     'desc': 'Visión, liderazgo y planificación estratégica para la transformación digital.',
     'questions': [
         'La empresa tiene una estrategia digital documentada y revisada periódicamente.',
         'La alta dirección impulsa activamente la transformación digital.',
         'Existen KPIs digitales con seguimiento mensual.',
         'Se asigna presupuesto específico para iniciativas digitales.',
         'La estrategia digital está alineada con los objetivos de negocio.',
     ]},
    {'id': 'dat', 'name': 'Datos y analítica', 'color': '#1D9E75',
     'desc': 'Gobierno del dato, calidad, análisis y toma de decisiones basada en datos.',
     'questions': [
         'Los datos críticos están centralizados y son accesibles a los equipos relevantes.',
         'Existe un responsable de datos (CDO o equivalente).',
         'Se usan dashboards o herramientas de BI de forma habitual.',
         'La calidad del dato se mide y gestiona activamente.',
         'Se toman decisiones clave apoyadas en análisis cuantitativo.',
     ]},
    {'id': 'tec', 'name': 'Infraestructura tecnológica', 'color': '#378ADD',
     'desc': 'Sistemas, cloud, integración y modernización del stack tecnológico.',
     'questions': [
         'La infraestructura principal está en cloud o en proceso de migración.',
         'Los sistemas críticos están integrados entre sí (ERP, CRM, etc.).',
         'Existe un plan de modernización tecnológica activo.',
         'La disponibilidad de los sistemas se monitoriza continuamente.',
         'Los procesos de backup y recuperación ante desastres están probados.',
     ]},
    {'id': 'cx', 'name': 'Experiencia de cliente', 'color': '#D4537E',
     'desc': 'Canales digitales, personalización, atención y journey del cliente.',
     'questions': [
         'La empresa ofrece atención digital 24/7 (web, app, chatbot).',
         'Se mide el NPS o satisfacción del cliente de forma periódica.',
         'Los canales digitales y físicos están integrados (omnicanalidad).',
         'Se personalizan comunicaciones y ofertas usando datos del cliente.',
         'Existe un mapa del journey del cliente documentado y actualizado.',
     ]},
    {'id': 'ops', 'name': 'Operaciones y procesos', 'color': '#BA7517',
     'desc': 'Automatización, eficiencia operativa y digitalización de procesos internos.',
     'questions': [
         'Los procesos repetitivos clave están automatizados.',
         'Se usan herramientas de gestión documental digital.',
         'Existe trazabilidad digital en la cadena de suministro o producción.',
         'Los procesos operativos se miden con indicadores digitales en tiempo real.',
         'Se aplican metodologías ágiles o de mejora continua en los equipos.',
     ]},
    {'id': 'tal', 'name': 'Talento y cultura digital', 'color': '#639922',
     'desc': 'Capacidades digitales del equipo, formación y cultura de innovación.',
     'questions': [
         'Los empleados reciben formación digital al menos una vez al año.',
         'Existe un plan de desarrollo de competencias digitales por rol.',
         'La cultura interna favorece la experimentación y la innovación.',
         'Se contratan o desarrollan perfiles digitales de forma proactiva.',
         'La colaboración remota y digital está normalizada en los equipos.',
     ]},
]

LEVELS = ['Inicial', 'Básico', 'Definido', 'Avanzado', 'Líder']

def get_level(avg):
    if avg < 1.8: return 'Inicial'
    if avg < 2.6: return 'Básico'
    if avg < 3.4: return 'Definido'
    if avg < 4.2: return 'Avanzado'
    return 'Líder'

# ── Rutas auth ───────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        pw = hash_pw(request.form['password'])
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email=? AND password=?', (email, pw)).fetchone()
        db.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            return redirect(url_for('dashboard'))
        flash('Credenciales incorrectas.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        pw = hash_pw(request.form['password'])
        db = get_db()
        try:
            db.execute('INSERT INTO users (name, email, password) VALUES (?,?,?)', (name, email, pw))
            db.commit()
            flash('Cuenta creada. Inicia sesión.')
            return redirect(url_for('login'))
        except:
            flash('El email ya está registrado.')
        finally:
            db.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Dashboard ────────────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    uid = session['user_id']
    role = session['user_role']

    if role == 'admin':
        audits = db.execute('''
            SELECT a.*, c.name as company_name, c.sector, u.name as auditor_name
            FROM audits a JOIN companies c ON a.company_id=c.id JOIN users u ON a.auditor_id=u.id
            ORDER BY a.created_at DESC LIMIT 20
        ''').fetchall()
        total_audits = db.execute('SELECT COUNT(*) FROM audits').fetchone()[0]
        total_companies = db.execute('SELECT COUNT(*) FROM companies').fetchone()[0]
        total_users = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    else:
        audits = db.execute('''
            SELECT a.*, c.name as company_name, c.sector, u.name as auditor_name
            FROM audits a JOIN companies c ON a.company_id=c.id JOIN users u ON a.auditor_id=u.id
            WHERE a.auditor_id=?
            ORDER BY a.created_at DESC
        ''', (uid,)).fetchall()
        total_audits = db.execute('SELECT COUNT(*) FROM audits WHERE auditor_id=?', (uid,)).fetchone()[0]
        total_companies = db.execute('SELECT COUNT(DISTINCT company_id) FROM audits WHERE auditor_id=?', (uid,)).fetchone()[0]
        total_users = None

    completed = sum(1 for a in audits if a['status'] == 'completed')
    db.close()
    return render_template('dashboard.html', audits=audits,
                           total_audits=total_audits, total_companies=total_companies,
                           total_users=total_users, completed=completed)

# ── Empresas ──────────────────────────────────────────────────────────────────
@app.route('/companies')
@login_required
def companies():
    db = get_db()
    uid = session['user_id']
    role = session['user_role']
    if role == 'admin':
        rows = db.execute('SELECT * FROM companies ORDER BY created_at DESC').fetchall()
    else:
        rows = db.execute('SELECT * FROM companies WHERE created_by=? ORDER BY created_at DESC', (uid,)).fetchall()
    db.close()
    return render_template('companies.html', companies=rows)

@app.route('/companies/new', methods=['GET', 'POST'])
@login_required
def new_company():
    if request.method == 'POST':
        db = get_db()
        db.execute('INSERT INTO companies (name, sector, size, contact, created_by) VALUES (?,?,?,?,?)',
                   (request.form['name'], request.form['sector'],
                    request.form['size'], request.form['contact'], session['user_id']))
        db.commit()
        db.close()
        flash('Empresa creada correctamente.')
        return redirect(url_for('companies'))
    return render_template('company_form.html')

# ── Auditorías ────────────────────────────────────────────────────────────────
@app.route('/audits/new/<int:company_id>')
@login_required
def new_audit(company_id):
    db = get_db()
    company = db.execute('SELECT * FROM companies WHERE id=?', (company_id,)).fetchone()
    audit_id = db.execute('INSERT INTO audits (company_id, auditor_id) VALUES (?,?)',
                          (company_id, session['user_id'])).lastrowid
    db.commit()
    db.close()
    return redirect(url_for('audit', audit_id=audit_id))

@app.route('/audit/<int:audit_id>', methods=['GET'])
@login_required
def audit(audit_id):
    db = get_db()
    audit = db.execute('SELECT a.*, c.name as company_name, c.sector, c.size FROM audits a JOIN companies c ON a.company_id=c.id WHERE a.id=?', (audit_id,)).fetchone()
    db.close()
    if not audit:
        return redirect(url_for('dashboard'))
    scores = json.loads(audit['scores_json']) if audit['scores_json'] else {}
    return render_template('audit.html', audit=audit, dims=DIMS, scores=scores)

@app.route('/audit/<int:audit_id>/save', methods=['POST'])
@login_required
def save_audit(audit_id):
    data = request.get_json()
    scores = data.get('scores', {})
    complete = data.get('complete', False)
    notes = data.get('notes', '')

    # Calcular score global
    dim_avgs = []
    for i, d in enumerate(DIMS):
        vals = [scores.get(f'{i}-{j}') for j in range(len(d['questions']))]
        vals = [v for v in vals if v is not None]
        if vals:
            dim_avgs.append(sum(vals)/len(vals))

    global_score = round(sum(dim_avgs)/len(dim_avgs)*20, 1) if dim_avgs else 0
    level = get_level(sum(dim_avgs)/len(dim_avgs)) if dim_avgs else 'Inicial'

    db = get_db()
    if complete:
        db.execute('''UPDATE audits SET scores_json=?, global_score=?, level=?, notes=?,
                      status='completed', completed_at=? WHERE id=?''',
                   (json.dumps(scores), global_score, level, notes,
                    datetime.now().strftime('%Y-%m-%d %H:%M'), audit_id))
    else:
        db.execute('UPDATE audits SET scores_json=?, global_score=?, level=?, notes=? WHERE id=?',
                   (json.dumps(scores), global_score, level, notes, audit_id))
    db.commit()
    db.close()
    return jsonify({'ok': True, 'score': global_score, 'level': level})

@app.route('/audit/<int:audit_id>/results')
@login_required
def audit_results(audit_id):
    db = get_db()
    audit = db.execute('SELECT a.*, c.name as company_name, c.sector, c.size FROM audits a JOIN companies c ON a.company_id=c.id WHERE a.id=?', (audit_id,)).fetchone()
    db.close()
    if not audit or not audit['scores_json']:
        return redirect(url_for('audit', audit_id=audit_id))
    scores = json.loads(audit['scores_json'])

    dim_scores = []
    for i, d in enumerate(DIMS):
        vals = [scores.get(f'{i}-{j}') for j in range(len(d['questions']))]
        vals = [v for v in vals if v is not None]
        avg = sum(vals)/len(vals) if vals else 0
        dim_scores.append({'dim': d, 'avg': avg, 'pct': round(avg*20)})

    return render_template('results.html', audit=audit, dim_scores=dim_scores, dims=DIMS)

@app.route('/audit/<int:audit_id>/delete', methods=['POST'])
@login_required
def delete_audit(audit_id):
    db = get_db()
    db.execute('DELETE FROM audits WHERE id=?', (audit_id,))
    db.commit()
    db.close()
    return redirect(url_for('dashboard'))

# ── Admin: usuarios ───────────────────────────────────────────────────────────
@app.route('/admin/users')
@login_required
def admin_users():
    if session['user_role'] != 'admin':
        return redirect(url_for('dashboard'))
    db = get_db()
    users = db.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    db.close()
    return render_template('admin_users.html', users=users)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
