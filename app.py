import os
import uuid
import json
import urllib.parse as up
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, send_from_directory)
from werkzeug.utils import secure_filename
import pg8000

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'adpi-secret-2026')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
DATABASE_URL = os.environ.get('DATABASE_URL', '')
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'docx', 'xlsx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

SECTORS = [
    'Imobiliário & Regeneração Urbana',
    'Infraestrutura & Logística',
    'Energias Renováveis',
    'Private Equity',
    'Blue Economy & Mar',
    'Agricultura & Segurança Alimentar',
    'Digital & Conectividade',
    'Créditos de Carbono & Floresta',
]
MUNICIPIOS = [
    'Lisboa','Porto','Cascais','Setúbal','Évora','Beja','Portalegre',
    'Serpa','Moura','Grândola','Alcácer do Sal','Elvas','Estremoz',
    'Montemor-o-Novo','Vidigueira','Santiago do Cacém','Sines','Outro',
]

# ---------- DB ----------

def get_conn():
    r = up.urlparse(DATABASE_URL)
    return pg8000.connect(
        host=r.hostname,
        port=r.port or 5432,
        database=r.path[1:],
        user=r.username,
        password=r.password,
        ssl_context=True
    )

def fetchall_dict(cur):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def fetchone_dict(cur):
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    return dict(zip(cols, row)) if row else None

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id SERIAL PRIMARY KEY,
            titulo TEXT NOT NULL,
            sector TEXT NOT NULL,
            municipio TEXT NOT NULL,
            descricao TEXT,
            investimento BIGINT DEFAULT 0,
            area FLOAT DEFAULT 0,
            jobs INTEGER DEFAULT 0,
            retorno TEXT,
            horizonte TEXT,
            fase TEXT DEFAULT 'Phase 1.0',
            estado TEXT DEFAULT 'Disponível',
            photos TEXT DEFAULT '[]',
            docs TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("SELECT COUNT(*) FROM opportunities")
    count = cur.fetchone()[0]
    if count == 0:
        seeds = [
            ("Herdade Vale do Guadiana","Agricultura & Segurança Alimentar","Serpa",
             "Propriedade de 450 ha com aptidão agrícola e olivicultura intensiva. Infraestruturas de rega e armazéns modernos. Potencial para produção de azeite premium com certificação DOP, criação de emprego local e exportação alinhada com a estratégia de segurança alimentar dos Emirados Árabes Unidos.",
             3500000,450,35,"12-16% ao ano","5-7 anos","Phase 1.0 — Real Estate","Disponível"),
            ("Corredor Logístico Porto de Sines","Infraestrutura & Logística","Sines",
             "Oportunidade de co-investimento no corredor logístico do Porto de Sines — porta atlântica da Europa. Alinhado com a expansão das infraestruturas portuárias e programas de concessão nacionais.",
             15000000,0,80,"8-12% ao ano","15-20 anos","Phase 2.0 — Representação","Em análise"),
            ("Parque Solar Alentejo Sul — 50MW","Energias Renováveis","Beja",
             "Terreno com licença prévia aprovada para parque solar fotovoltaico de 50 MW. Contrato de ligação à rede garantido. Estrutura PPA disponível para retorno estável a longo prazo.",
             28000000,120,8,"8-10% ao ano","20-25 anos","Phase 2.0 — Representação","Disponível"),
            ("Regeneração Urbana — Lisboa Premium","Imobiliário & Regeneração Urbana","Lisboa",
             "Conjunto de ativos em Lisboa para regeneração brown-to-green: student living, senior living e ativos mistos. Yields estáveis e valorização do capital no médio prazo.",
             5000000,0,22,"10-15% ao ano","4-6 anos","Phase 1.0 — Real Estate","Disponível"),
        ]
        for s in seeds:
            cur.execute("""INSERT INTO opportunities
                (titulo,sector,municipio,descricao,investimento,area,jobs,retorno,horizonte,fase,estado)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", s)
    conn.commit()
    cur.close()
    conn.close()

try:
    init_db()
except Exception as e:
    print(f"DB init error: {e}")

def get_all_opps(sector='', fase='', q=''):
    conn = get_conn()
    cur = conn.cursor()
    sql = "SELECT * FROM opportunities WHERE 1=1"
    params = []
    if sector:
        sql += " AND LOWER(sector) LIKE %s"
        params.append(f'%{sector.lower()}%')
    if fase:
        sql += " AND fase LIKE %s"
        params.append(f'%{fase}%')
    if q:
        sql += " AND (LOWER(titulo) LIKE %s OR LOWER(municipio) LIKE %s OR LOWER(descricao) LIKE %s)"
        params += [f'%{q.lower()}%']*3
    sql += " ORDER BY id DESC"
    cur.execute(sql, params)
    rows = fetchall_dict(cur)
    cur.close()
    conn.close()
    return rows

def get_opp(opp_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM opportunities WHERE id=%s", (opp_id,))
    row = fetchone_dict(cur)
    cur.close()
    conn.close()
    return row

def create_opp(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO opportunities
        (titulo,sector,municipio,descricao,investimento,area,jobs,retorno,horizonte,fase,estado,photos,docs)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (data['titulo'],data['sector'],data['municipio'],data['descricao'],
         data['investimento'],data['area'],data['jobs'],data['retorno'],
         data['horizonte'],data['fase'],data['estado'],
         json.dumps(data['photos']),json.dumps(data['docs'])))
    opp_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return opp_id

def update_opp(opp_id, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""UPDATE opportunities SET
        titulo=%s,sector=%s,municipio=%s,descricao=%s,investimento=%s,area=%s,
        jobs=%s,retorno=%s,horizonte=%s,fase=%s,estado=%s WHERE id=%s""",
        (data['titulo'],data['sector'],data['municipio'],data['descricao'],
         data['investimento'],data['area'],data['jobs'],data['retorno'],
         data['horizonte'],data['fase'],data['estado'],opp_id))
    conn.commit()
    cur.close()
    conn.close()

def update_opp_photos(opp_id, photos):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE opportunities SET photos=%s WHERE id=%s", (json.dumps(photos), opp_id))
    conn.commit()
    cur.close()
    conn.close()

def update_opp_docs(opp_id, docs):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE opportunities SET docs=%s WHERE id=%s", (json.dumps(docs), opp_id))
    conn.commit()
    cur.close()
    conn.close()

def delete_opp(opp_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM opportunities WHERE id=%s", (opp_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total, COALESCE(SUM(investimento),0) as invest, COALESCE(SUM(jobs),0) as jobs, COUNT(DISTINCT sector) as sectors FROM opportunities")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {'total': row[0], 'investimento': row[1], 'jobs': row[2], 'sectors': row[3]}

def parse_opp(o):
    if o and isinstance(o.get('photos'), str):
        o['photos'] = json.loads(o['photos'])
    if o and isinstance(o.get('docs'), str):
        o['docs'] = json.loads(o['docs'])
    return o

# ---------- Auth ----------

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def allowed_file(fn):
    return '.' in fn and fn.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploads(files_key, existing=None):
    result = list(existing or [])
    for f in request.files.getlist(files_key):
        if f and f.filename and allowed_file(f.filename):
            ext = f.filename.rsplit('.',1)[1].lower()
            fname = f"{uuid.uuid4().hex}.{ext}"
            f.save(os.path.join(UPLOAD_FOLDER, fname))
            result.append({'filename': fname, 'original': secure_filename(f.filename)})
    return result

# ---------- Portal ----------

@app.route('/')
def index():
    sector = request.args.get('sector','')
    fase = request.args.get('fase','')
    q = request.args.get('q','')
    opps = [parse_opp(o) for o in get_all_opps(sector, fase, q)]
    used_sectors = sorted(set(o['sector'].split(' ')[0] for o in get_all_opps()))
    return render_template('portal.html', opportunities=opps,
                           sectors=used_sectors, sector=sector, fase=fase, q=q)

@app.route('/oportunidade/<int:opp_id>')
def oportunidade(opp_id):
    opp = parse_opp(get_opp(opp_id))
    if not opp: return redirect(url_for('index'))
    return render_template('detalhe.html', opp=opp)

# ---------- Admin ----------

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Password incorreta.','error')
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    opps = [parse_opp(o) for o in get_all_opps()]
    stats = get_stats()
    return render_template('admin_dashboard.html', opportunities=opps, stats=stats)

@app.route('/admin/nova', methods=['GET','POST'])
@login_required
def admin_nova():
    if request.method == 'POST':
        photos = save_uploads('photos')
        docs = save_uploads('docs')
        data = {
            'titulo': request.form.get('titulo',''),
            'sector': request.form.get('sector',''),
            'municipio': request.form.get('municipio',''),
            'descricao': request.form.get('descricao',''),
            'investimento': int(request.form.get('investimento') or 0),
            'area': float(request.form.get('area') or 0),
            'jobs': int(request.form.get('jobs') or 0),
            'retorno': request.form.get('retorno',''),
            'horizonte': request.form.get('horizonte',''),
            'fase': request.form.get('fase','Phase 1.0 — Real Estate'),
            'estado': request.form.get('estado','Disponível'),
            'photos': photos,
            'docs': docs,
        }
        create_opp(data)
        flash('Oportunidade publicada com sucesso!','success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_form.html', opp=None, sectors=SECTORS, municipios=MUNICIPIOS)

@app.route('/admin/editar/<int:opp_id>', methods=['GET','POST'])
@login_required
def admin_editar(opp_id):
    opp = parse_opp(get_opp(opp_id))
    if not opp: return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        photos = save_uploads('photos', opp['photos'])
        docs = save_uploads('docs', opp['docs'])
        data = {
            'titulo': request.form.get('titulo',''),
            'sector': request.form.get('sector',''),
            'municipio': request.form.get('municipio',''),
            'descricao': request.form.get('descricao',''),
            'investimento': int(request.form.get('investimento') or 0),
            'area': float(request.form.get('area') or 0),
            'jobs': int(request.form.get('jobs') or 0),
            'retorno': request.form.get('retorno',''),
            'horizonte': request.form.get('horizonte',''),
            'fase': request.form.get('fase','Phase 1.0 — Real Estate'),
            'estado': request.form.get('estado','Disponível'),
        }
        update_opp(opp_id, data)
        update_opp_photos(opp_id, photos)
        update_opp_docs(opp_id, docs)
        flash('Oportunidade atualizada!','success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_form.html', opp=opp, sectors=SECTORS, municipios=MUNICIPIOS)

@app.route('/admin/eliminar/<int:opp_id>', methods=['POST'])
@login_required
def admin_eliminar(opp_id):
    delete_opp(opp_id)
    flash('Oportunidade eliminada.','success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/remover-foto/<int:opp_id>/<filename>', methods=['POST'])
@login_required
def remover_foto(opp_id, filename):
    opp = parse_opp(get_opp(opp_id))
    if opp:
        photos = [p for p in opp['photos'] if p['filename'] != filename]
        update_opp_photos(opp_id, photos)
        try: os.remove(os.path.join(UPLOAD_FOLDER, filename))
        except: pass
    return redirect(url_for('admin_editar', opp_id=opp_id))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
