"""
Sistema de Gerenciamento dos Reparos — Versão Mobile (Flet)
Compatível com Flet 0.24.1 — Banco SQLite local no tablet.
"""

import flet as ft
import sqlite3, hashlib, json, os
from datetime import datetime

# ── Constantes ───────────────────────────────────────────────────
ADMIN_PASSWORD = "#Val1001"

CAT_SUBCAT = {
    "Calçada": ["Reparo e/ou adequação de calçada", "Reparo e/ou adequação de piso intertravado"],
    "Drenagem": ["Reparo e/ou adequação de Boca de Lobo", "Reparo e/ou adequação de caixa ralo",
                 "Reparo e/ou adequação de poço de visita (PV)", "Limpeza e desobstrução de rede",
                 "Reparo e/ou adequação de rede de drenagem", "Reparo e/ou adequação de caixa coletora",
                 "Reparo e/ou adequação de tampa de concreto", "Travessia de drenagem"],
    "Manutenções e Reparos específicos": ["Manutenções Gerais", "Manutenção de guarda-corpo",
        "Reparo de estruturas de madeira", "Travessia para pedestres",
        "Reparo de estruturas de concreto", "Reparo de abrigo de passageiros",
        "Fresagem de vias", "Reparo de telhado"],
    "Vias públicas": ["Tapa Buraco Emergencial (asfalto frio)", "Manutenção de vias",
        "Reparo de via com paralelepípedos", "Reparo de base para pavimentação asfáltica"],
    "Meio-fio": ["Reparo e/ou substituição de meio-fio"],
    "Muro e Mureta": ["Reparo de muro e/ou mureta"],
    "Base de concreto": ["Reparo de piso ou base de concreto"],
    "Retirada de Material": ["Retirada de resíduos de obra"],
    "Rios e Canais": ["Desobstrução de valas e córregos", "Limpeza de corpos hídricos"],
    "Movimentação de solo": ["Troca de solo", "Reconstituição de talude", "Reconstituição de solo"],
}

SITUACOES = ["Aberto", "Em execução", "Cancelado", "Finalizado"]

NUCLEO_DISTRITO = {
    "CENTRO I":     "1º DISTRITO - CENTRO",
    "CENTRO II":    "1º DISTRITO - CENTRO",
    "CORDEIRINHO":  "2º DISTRITO - PONTA NEGRA",
    "ESPRAIADO":    "2º DISTRITO - PONTA NEGRA",
    "INOÃ":         "3º DISTRITO - INOÃ",
    "SÃO JOSÉ":     "3º DISTRITO - INOÃ",
    "ITAIPUAÇU I":  "4º DISTRITO - ITAIPUAÇU",
    "ITAIPUAÇU II": "4º DISTRITO - ITAIPUAÇU",
}

DISTRITO_BAIRROS = {
    "CENTRO I":     ["Centro", "Mumbuca", "Araçatiba", "Flamengo", "Barra de Maricá"],
    "CENTRO II":    ["Centro", "Mumbuca", "Araçatiba", "Flamengo", "Barra de Maricá"],
    "CORDEIRINHO":  ["Cordeirinho", "Ponta Negra", "Bambuí", "Guaratiba", "Bananal"],
    "ESPRAIADO":    ["Espraiado"],
    "INOÃ":         ["Inoã", "São José"],
    "SÃO JOSÉ":     ["Inoã", "São José"],
    "ITAIPUAÇU I":  ["Itaipuaçu", "Recanto", "Jardim Atlântico", "Barroco"],
    "ITAIPUAÇU II": ["Itaipuaçu", "Recanto", "Jardim Atlântico", "Barroco"],
}

# Cores do tema dark
BG      = "#0d0d1a"
BG2     = "#12121f"
BG3     = "#16162e"
CARD    = "#1a1a38"
BORDER  = "#2e2e55"
ACCENT  = "#3d9be9"
TEXT    = "#d0d8f0"
TEXT2   = "#9aabcc"
TEXT3   = "#667799"
SUCCESS = "#1a6b3c"
DANGER  = "#b53030"
WHITE   = "#ffffff"

SIT_CORES = {
    "ABERTO":      ("#3a3000", "#ffdd66"),
    "EM EXECUÇÃO": ("#0d2a4a", "#88ccff"),
    "CANCELADO":   ("#3a0d0d", "#ff8888"),
    "FINALIZADO":  ("#0d3a1a", "#7aff9a"),
}

# ── Database ──────────────────────────────────────────────────────
_DB_PATH = None

def get_db_path(page=None):
    global _DB_PATH
    if _DB_PATH:
        return _DB_PATH
    try:
        if page and hasattr(page, "app_data_dir") and page.app_data_dir:
            base = page.app_data_dir
        else:
            base = os.path.expanduser("~")
    except Exception:
        base = os.path.expanduser("~")
    _DB_PATH = os.path.join(base, "reparos.db")
    return _DB_PATH

def get_conn(page=None):
    conn = sqlite3.connect(get_db_path(page), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def init_db(page=None):
    conn = get_conn(page)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS solicitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_abertura TEXT NOT NULL,
            solicitacao TEXT NOT NULL UNIQUE,
            nucleo TEXT, solicitante TEXT, endereco TEXT, bairro TEXT,
            distrito TEXT, categoria TEXT, subcategoria TEXT, encarregado TEXT,
            situacao TEXT, data_inicio TEXT, data_conclusao TEXT,
            observacao TEXT, localizacao TEXT,
            criado_em TEXT DEFAULT (datetime('now','localtime')),
            atualizado_em TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS materiais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            solicitacao_id INTEGER NOT NULL,
            nome TEXT NOT NULL, quantidade TEXT, tipo TEXT,
            FOREIGN KEY (solicitacao_id) REFERENCES solicitacoes(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL, sobrenome TEXT NOT NULL,
            login TEXT NOT NULL UNIQUE, senha_hash TEXT NOT NULL,
            criado_em TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            solicitacao_id INTEGER, solicitacao_num TEXT NOT NULL,
            usuario TEXT NOT NULL, data_hora TEXT NOT NULL,
            campo TEXT NOT NULL, valor_anterior TEXT, valor_novo TEXT
        );
        CREATE TABLE IF NOT EXISTS excluidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            solicitacao TEXT NOT NULL, nucleo TEXT,
            excluido_por TEXT, excluido_em TEXT NOT NULL, dados_json TEXT
        );
    """)
    conn.commit()
    conn.close()

def hash_senha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def autenticar(login, senha, page=None):
    try:
        conn = get_conn(page)
        row = conn.execute(
            "SELECT nome, sobrenome FROM usuarios WHERE login=? AND senha_hash=?",
            (login.strip(), hash_senha(senha))
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None

def cadastrar_usuario(nome, sobrenome, login, senha, page=None):
    try:
        conn = get_conn(page)
        conn.execute(
            "INSERT INTO usuarios (nome, sobrenome, login, senha_hash) VALUES (?,?,?,?)",
            (nome.strip(), sobrenome.strip(), login.strip(), hash_senha(senha))
        )
        conn.commit()
        conn.close()
        return True, "Usuário cadastrado!"
    except sqlite3.IntegrityError:
        return False, "Login já em uso."
    except Exception as e:
        return False, str(e)

def gerar_proxima(page=None):
    ano = datetime.now().year
    try:
        conn = get_conn(page)
        row = conn.execute(
            "SELECT solicitacao FROM solicitacoes WHERE solicitacao LIKE ? "
            "ORDER BY CAST(substr(solicitacao,1,5) AS INTEGER) DESC LIMIT 1",
            (f"%/{ano}",)
        ).fetchone()
        conn.close()
        num = 1
        if row:
            try:
                num = int(row["solicitacao"].split("/")[0]) + 1
            except Exception:
                pass
        return f"{num:05d}/{ano}"
    except Exception:
        return f"00001/{ano}"

def tc(s):
    if not s:
        return s
    prepos = {"a","as","o","os","da","das","do","dos","de","em","no","na",
              "nos","nas","ao","aos","por","e","ou","com","sem","sob","sobre",
              "entre","para","pelo","pela","pelos","pelas","num","numa"}
    words = s.strip().split()
    return " ".join(
        w.capitalize() if i == 0 or w.lower() not in prepos else w.lower()
        for i, w in enumerate(words)
    )

def salvar_historico(sol_id, sol_num, usuario, diff, page=None):
    if not diff:
        return
    try:
        conn = get_conn(page)
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        for campo, antes, depois in diff:
            conn.execute(
                "INSERT INTO historico "
                "(solicitacao_id,solicitacao_num,usuario,data_hora,campo,valor_anterior,valor_novo)"
                " VALUES (?,?,?,?,?,?,?)",
                (sol_id, sol_num, usuario, now, campo, antes or "", depois or "")
            )
        conn.commit()
        conn.close()
    except Exception as e:
        print("historico:", e)

# ── Helpers UI ────────────────────────────────────────────────────
def lbl(texto):
    return ft.Text(texto, size=12, color=TEXT2, weight=ft.FontWeight.W_600)

def inp(hint="", value="", password=False, expand=True, width=None, read_only=False):
    return ft.TextField(
        hint_text=hint, value=value,
        password=password, can_reveal_password=password,
        bgcolor=BG2, color=TEXT,
        border_color=BORDER, focused_border_color=ACCENT,
        border_radius=8,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        text_size=14, expand=expand, width=width, read_only=read_only,
        hint_style=ft.TextStyle(color=TEXT3),
    )

def ddrop(options, value="", hint="— Selecione —", expand=True, width=None, on_change=None):
    return ft.Dropdown(
        options=[ft.dropdown.Option(str(o)) for o in options],
        value=value if value else None,
        hint_text=hint,
        bgcolor=BG2, color=TEXT,
        border_color=BORDER, focused_border_color=ACCENT,
        border_radius=8,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=4),
        text_size=14, expand=expand, width=width, on_change=on_change,
    )

def botao(texto, on_click=None, bg=None, expand=False, icon=None):
    return ft.ElevatedButton(
        text=texto, on_click=on_click, expand=expand, icon=icon,
        style=ft.ButtonStyle(
            color={ft.ControlState.DEFAULT: WHITE},
            bgcolor={ft.ControlState.DEFAULT: bg or "#1a4a8c",
                     ft.ControlState.HOVERED: "#1f5aad"},
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
        ),
    )

def sit_chip(situacao):
    sit = (situacao or "").upper()
    bg, fg = SIT_CORES.get(sit, (CARD, TEXT2))
    return ft.Container(
        content=ft.Text(situacao or "—", size=11, color=fg, weight=ft.FontWeight.W_700),
        bgcolor=bg, border_radius=12,
        padding=ft.padding.symmetric(horizontal=10, vertical=3),
    )

def secao(titulo, controles):
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.LABEL, color=ACCENT, size=16),
                ft.Text(titulo, size=13, color=ACCENT, weight=ft.FontWeight.W_700),
            ]),
            ft.Divider(height=1, color=BORDER),
            *controles,
        ], spacing=10),
        bgcolor=BG3, border_radius=10,
        border=ft.border.all(1, BORDER),
        padding=14, margin=ft.margin.only(bottom=10),
    )

# ── App ───────────────────────────────────────────────────────────
class App:
    def __init__(self, page: ft.Page):
        self.page     = page
        self.usuario  = None
        self.login_str = ""
        self._setup_page()
        init_db(page)
        self._ir_login()

    def _setup_page(self):
        p = self.page
        p.title      = "Gerenciamento dos Reparos"
        p.theme_mode = ft.ThemeMode.DARK
        p.bgcolor    = BG
        p.padding    = 0
        p.theme      = ft.Theme(color_scheme_seed=ACCENT)

    def _snack(self, msg, cor="#2e7d32"):
        self.page.snack_bar = ft.SnackBar(
            ft.Text(msg, color=WHITE), bgcolor=cor, duration=3000
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _clear(self):
        self.page.controls.clear()
        self.page.appbar = None
        self.page.floating_action_button = None

    # ── LOGIN ─────────────────────────────────────────────────────
    def _ir_login(self):
        self._clear()
        e_login = inp("Login")
        e_senha = inp("Senha", password=True)
        lbl_err = ft.Text("", color="#ff6666", size=13)

        def entrar(e):
            l = (e_login.value or "").strip()
            s = (e_senha.value or "")
            if not l or not s:
                lbl_err.value = "⚠  Preencha login e senha."
                self.page.update()
                return
            u = autenticar(l, s, self.page)
            if u:
                self.usuario   = u
                self.login_str = l
                self._ir_lista()
            else:
                lbl_err.value = "❌  Login ou senha inválidos."
                self.page.update()

        e_senha.on_submit = entrar

        self.page.controls.append(ft.Column([
            ft.Container(
                ft.Column([
                    ft.Icon(ft.Icons.LIST_ALT, color=ACCENT, size=52),
                    ft.Text("Gerenciamento dos Reparos", size=18, color=ACCENT,
                            weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Text("Desenvolvido por Valdemir Vieira Alves",
                            size=11, color=TEXT3, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                bgcolor=CARD, padding=28,
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
            ),
            ft.Container(
                ft.Column([
                    ft.Text("🔐  Acesso ao Sistema", size=16, color=TEXT,
                            weight=ft.FontWeight.BOLD),
                    ft.Text("Informe seu login e senha", size=12, color=TEXT3),
                    ft.Container(height=6),
                    lbl("Login"), e_login,
                    lbl("Senha"), e_senha,
                    lbl_err,
                    botao("▶  ENTRAR", on_click=entrar, bg=SUCCESS, expand=True),
                    ft.Divider(color=BORDER),
                    ft.TextButton("➕  Cadastrar Novo Usuário",
                        on_click=lambda e: self._ir_cadastro(),
                        style=ft.ButtonStyle(color=TEXT2)),
                    ft.TextButton("⚙️  Configurar Banco",
                        on_click=lambda e: self._ir_config(),
                        style=ft.ButtonStyle(color=ACCENT)),
                    ft.TextButton("ℹ️  Sobre",
                        on_click=lambda e: self._dialog_sobre(),
                        style=ft.ButtonStyle(color=TEXT3)),
                ], spacing=8),
                padding=24, expand=True,
            ),
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO))
        self.page.update()

    # ── CADASTRO ─────────────────────────────────────────────────
    def _ir_cadastro(self):
        self._clear()
        e_adm  = inp("Senha do administrador", password=True)
        e_nome = inp("Nome")
        e_sob  = inp("Sobrenome")
        e_log  = inp("Login")
        e_sen  = inp("Senha (mín. 4 caracteres)", password=True)
        e_con  = inp("Confirmar senha", password=True)
        lbl_er = ft.Text("", color="#ff6666", size=13)

        def salvar(e):
            if (e_adm.value or "") != ADMIN_PASSWORD:
                lbl_er.value = "❌  Senha de administrador incorreta."
                self.page.update()
                return
            n = (e_nome.value or "").strip()
            s = (e_sob.value or "").strip()
            l = (e_log.value or "").strip()
            p = (e_sen.value or "")
            c = (e_con.value or "")
            if not all([n, s, l, p, c]):
                lbl_er.value = "⚠  Preencha todos os campos."
                self.page.update()
                return
            if len(p) < 4:
                lbl_er.value = "⚠  Senha mínimo 4 caracteres."
                self.page.update()
                return
            if p != c:
                lbl_er.value = "❌  Senhas não coincidem."
                self.page.update()
                return
            ok, msg = cadastrar_usuario(n, s, l, p, self.page)
            if ok:
                self._snack(f"✅  Usuário '{n} {s}' cadastrado!")
                self._ir_login()
            else:
                lbl_er.value = f"❌  {msg}"
                self.page.update()

        self.page.appbar = ft.AppBar(
            title=ft.Text("Cadastrar Usuário", color=TEXT),
            bgcolor=CARD,
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK, icon_color=TEXT,
                on_click=lambda e: self._ir_login()
            ),
        )
        self.page.controls.append(ft.ListView([
            ft.Container(ft.Column([
                ft.Text("👤  Novo Usuário", size=16, color=ACCENT, weight=ft.FontWeight.BOLD),
                ft.Text("Requer senha do administrador", size=12, color=TEXT3),
                ft.Container(height=4),
                lbl("Senha do Administrador *"), e_adm,
                lbl("Nome *"), e_nome,
                lbl("Sobrenome *"), e_sob,
                lbl("Login *"), e_log,
                lbl("Senha *"), e_sen,
                lbl("Confirmar Senha *"), e_con,
                lbl_er,
                botao("💾  Salvar Usuário", on_click=salvar, bg=SUCCESS, expand=True),
                ft.Container(height=20),
            ], spacing=8), padding=16)
        ], expand=True, padding=0))
        self.page.update()

    # ── CONFIGURAR BANCO ─────────────────────────────────────────
    def _ir_config(self):
        self._clear()
        lbl_status = ft.Text(
            f"✅ Banco atual: {os.path.basename(get_db_path())}" if has_config()
            else "⚠️ Nenhum banco configurado",
            color="#44cc88" if has_config() else "#ffaa44",
            size=12, text_align=ft.TextAlign.CENTER,
        )
        e_adm   = inp("Senha do administrador", password=True)
        e_path  = ft.TextField(
            hint_text="Toque em 🔍 Procurar para selecionar o arquivo .db",
            bgcolor=BG2, color=TEXT, border_color=BORDER,
            focused_border_color=ACCENT, border_radius=8,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
            text_size=13, expand=True, read_only=True,
            hint_style=ft.TextStyle(color=TEXT3),
            value=get_db_path() or "",
        )
        lbl_er  = ft.Text("", color="#ff6666", size=13)
        lbl_ok  = ft.Text("", color="#44cc88", size=13)

        # FilePicker para selecionar o .db
        def on_pick(ev):
            if ev.files and len(ev.files) > 0:
                e_path.value = ev.files[0].path or ""
                self.page.update()

        fp = ft.FilePicker(on_result=on_pick)
        if fp not in self.page.overlay:
            self.page.overlay.append(fp)
        self.page.update()

        def salvar(e):
            if (e_adm.value or "") != ADMIN_PASSWORD:
                lbl_er.value = "❌  Senha de administrador incorreta."
                lbl_ok.value = ""
                self.page.update()
                return
            p = (e_path.value or "").strip()
            if not p:
                lbl_er.value = "⚠  Selecione o arquivo .db primeiro."
                self.page.update()
                return
            save_config(self.page, p)
            ok = init_db()
            if ok:
                lbl_ok.value = f"✅ Banco configurado com sucesso!"
                lbl_er.value = ""
                lbl_status.value = f"✅ Banco: {os.path.basename(p)}"
                lbl_status.color = "#44cc88"
            else:
                lbl_er.value = "❌ Não foi possível inicializar o banco."
                lbl_ok.value = ""
            self.page.update()

        self.page.appbar = ft.AppBar(
            title=ft.Text("Configurar Banco", color=TEXT),
            bgcolor=CARD,
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK, icon_color=TEXT,
                on_click=lambda e: self._ir_login()
            ),
        )
        self.page.controls.append(ft.ListView([
            ft.Container(ft.Column([
                ft.Text("⚙️  Configuração do Banco de Dados",
                        size=16, color=ACCENT, weight=ft.FontWeight.BOLD),
                ft.Container(height=4),
                lbl_status,
                ft.Container(height=12),

                # Instruções
                ft.Container(
                    ft.Column([
                        ft.Text("📱 Como encontrar o .db no tablet:",
                                size=12, color=ACCENT, weight=ft.FontWeight.W_600),
                        ft.Text(
                            "1. Abra o OneDrive e baixe o SOLICITACOES.db\n"
                            "2. O arquivo vai para a pasta Downloads\n"
                            "3. Toque em 🔍 Procurar abaixo e navegue até Downloads\n"
                            "4. Selecione o arquivo SOLICITACOES.db",
                            size=11, color=TEXT2,
                        ),
                    ], spacing=4),
                    bgcolor=BG2, border_radius=8, padding=12,
                    border=ft.border.all(1, BORDER),
                ),
                ft.Container(height=12),

                lbl("Senha do Administrador *"), e_adm,
                ft.Container(height=8),

                lbl("Arquivo do Banco (.db) *"),
                ft.Row([
                    e_path,
                    ft.IconButton(
                        ft.Icons.SEARCH, icon_color=ACCENT,
                        tooltip="Procurar arquivo .db",
                        on_click=lambda e: fp.pick_files(
                            dialog_title="Selecionar banco de dados",
                            allowed_extensions=["db"],
                            allow_multiple=False,
                        ),
                    ),
                ], spacing=4),

                ft.Container(height=8),
                lbl_er,
                lbl_ok,
                botao("💾  Salvar Configuração", on_click=salvar,
                      bg=SUCCESS, expand=True),
                ft.Container(height=24),
            ], spacing=8), padding=16)
        ], expand=True))
        self.page.update()

    # ── LISTA ────────────────────────────────────────────────────
    def _ir_lista(self):
        self._clear()
        self._filtros   = {"q": "", "nucleo": "", "situacao": ""}
        self._pg        = 1
        self._per_page  = 30

        self._f_q   = ft.TextField(
            hint_text="🔍  Buscar nº, solicitante, endereço...",
            bgcolor=BG2, color=TEXT, border_color=BORDER,
            focused_border_color=ACCENT, border_radius=8,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
            text_size=13, on_change=self._on_busca,
        )
        self._f_nuc = ddrop([""] + list(NUCLEO_DISTRITO.keys()),
                            hint="Núcleo", expand=True, on_change=self._on_filtro)
        self._f_sit = ddrop([""] + SITUACOES,
                            hint="Situação", expand=True, on_change=self._on_filtro)
        self._lbl_total = ft.Text("", size=12, color=TEXT3)
        self._lista_col = ft.Column([], spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)

        self.page.appbar = ft.AppBar(
            title=ft.Text("Solicitações", color=TEXT),
            bgcolor=CARD,
            actions=[
                ft.IconButton(
                    ft.Icons.ADD_CIRCLE_OUTLINE, icon_color="#4caf50",
                    tooltip="Nova",
                    on_click=lambda e: self._ir_formulario("novo")
                ),
                ft.IconButton(
                    ft.Icons.INFO_OUTLINE, icon_color=ACCENT,
                    tooltip="Sincronização",
                    on_click=lambda e: self._dialog_sync()
                ),
                ft.IconButton(
                    ft.Icons.LOGOUT, icon_color=TEXT3,
                    tooltip="Sair",
                    on_click=lambda e: self._ir_login()
                ),
            ],
        )
        self.page.controls.append(ft.Column([
            ft.Container(
                ft.Column([
                    self._f_q,
                    ft.Row([self._f_nuc, self._f_sit], spacing=8),
                    self._lbl_total,
                ], spacing=8),
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                bgcolor=BG2,
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
            ),
            ft.Container(self._lista_col, expand=True, padding=8),
        ], spacing=0, expand=True))
        self.page.update()
        self._carregar_lista()

    def _on_busca(self, e):
        self._filtros["q"] = (e.control.value or "").strip()
        self._pg = 1
        self._carregar_lista()

    def _on_filtro(self, e):
        self._filtros["nucleo"]   = self._f_nuc.value or ""
        self._filtros["situacao"] = self._f_sit.value or ""
        self._pg = 1
        self._carregar_lista()

    def _carregar_lista(self):
        q        = self._filtros.get("q", "")
        nucleo   = self._filtros.get("nucleo", "")
        situacao = self._filtros.get("situacao", "")
        offset   = (self._pg - 1) * self._per_page

        where, params = ["1=1"], []
        if q:
            where.append("(solicitacao LIKE ? OR solicitante LIKE ? OR endereco LIKE ?)")
            params += [f"%{q}%"] * 3
        if nucleo:
            where.append("nucleo=?")
            params.append(nucleo)
        if situacao:
            where.append("situacao=?")
            params.append(situacao)

        sql_w = " AND ".join(where)
        conn  = get_conn(self.page)
        total = conn.execute(
            f"SELECT COUNT(*) FROM solicitacoes WHERE {sql_w}", params
        ).fetchone()[0]
        rows  = conn.execute(
            f"SELECT id, data_abertura, solicitacao, nucleo, solicitante, "
            f"endereco, bairro, situacao, categoria "
            f"FROM solicitacoes WHERE {sql_w} "
            f"ORDER BY CAST(substr(solicitacao,1,5) AS INTEGER) DESC "
            f"LIMIT ? OFFSET ?",
            params + [self._per_page, offset]
        ).fetchall()
        conn.close()

        self._lbl_total.value = f"{total} registro(s)"
        self._lista_col.controls.clear()

        if not rows:
            self._lista_col.controls.append(
                ft.Container(
                    ft.Text("Nenhum registro encontrado.", color=TEXT3,
                            text_align=ft.TextAlign.CENTER),
                    alignment=ft.alignment.center, expand=True, padding=40,
                )
            )
        else:
            for r in rows:
                self._lista_col.controls.append(self._card(dict(r)))

        # Paginação
        if total > self._per_page:
            total_pgs = (total + self._per_page - 1) // self._per_page
            self._lista_col.controls.append(
                ft.Row([
                    ft.IconButton(ft.Icons.CHEVRON_LEFT,
                                  disabled=self._pg <= 1,
                                  on_click=lambda e: self._pag(-1)),
                    ft.Text(f"{self._pg}/{total_pgs}", color=TEXT2),
                    ft.IconButton(ft.Icons.CHEVRON_RIGHT,
                                  disabled=self._pg >= total_pgs,
                                  on_click=lambda e: self._pag(1)),
                ], alignment=ft.MainAxisAlignment.CENTER)
            )
        self.page.update()

    def _pag(self, delta):
        self._pg += delta
        self._carregar_lista()

    def _card(self, r):
        sit = (r.get("situacao") or "").upper()
        bg_map = {
            "ABERTO":      "#2a2000",
            "EM EXECUÇÃO": "#0a1a2e",
            "CANCELADO":   "#2a0d0d",
            "FINALIZADO":  "#0d2a18",
        }
        bg_card = bg_map.get(sit, BG3)
        rid = r["id"]

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(r.get("solicitacao", "—"), size=14, color="#a0c8ff",
                            weight=ft.FontWeight.BOLD, expand=True),
                    sit_chip(r.get("situacao", "—")),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text(r.get("data_abertura", ""), size=11, color=TEXT3),
                    ft.Text("·", color=TEXT3),
                    ft.Text(r.get("nucleo", "—"), size=11, color=TEXT2),
                ], spacing=4),
                ft.Text(r.get("solicitante", "—"), size=12, color=TEXT2),
                ft.Text(
                    (r.get("endereco") or "") +
                    (", " + r.get("bairro", "") if r.get("bairro") else ""),
                    size=11, color=TEXT3,
                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Row([
                    ft.Text(r.get("categoria", "—"), size=11, color=TEXT3, expand=True),
                    ft.TextButton(
                        "Editar →",
                        on_click=lambda e, _id=rid: self._ir_formulario("editar", _id),
                        style=ft.ButtonStyle(color=ACCENT,
                                             padding=ft.padding.all(0)),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=4),
            bgcolor=bg_card, border_radius=10,
            border=ft.border.all(1, BORDER),
            padding=12,
            on_click=lambda e, _id=rid: self._ir_formulario("editar", _id),
        )

    # ── FORMULÁRIO ───────────────────────────────────────────────
    def _ir_formulario(self, modo="novo", sol_id=None):
        dados = {}
        if modo == "editar" and sol_id:
            conn = get_conn(self.page)
            row  = conn.execute(
                "SELECT * FROM solicitacoes WHERE id=?", (sol_id,)
            ).fetchone()
            conn.close()
            if row:
                dados = dict(row)

        self._clear()

        titulo = "Nova Solicitação" if modo == "novo" else f"Editar — {dados.get('solicitacao','')}"

        # campos
        e_data = inp("DD/MM/AAAA",  value=dados.get("data_abertura", ""))
        e_sol  = inp("00001/2026",   value=dados.get("solicitacao", ""),
                     read_only=(modo == "editar"))
        e_sol2 = inp("Solicitante", value=dados.get("solicitante", ""))
        e_end  = inp("Endereço",    value=dados.get("endereco", ""))
        e_loc  = inp('Coordenadas', value=dados.get("localizacao", ""))
        e_obs  = ft.TextField(
            hint_text="Observações...", value=dados.get("observacao", ""),
            bgcolor=BG2, color=TEXT, border_color=BORDER,
            focused_border_color=ACCENT, border_radius=8,
            multiline=True, min_lines=3, max_lines=6,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
            text_size=14,
        )
        e_di  = inp("DD/MM/AAAA", value=dados.get("data_inicio", ""))
        e_dc  = inp("DD/MM/AAAA", value=dados.get("data_conclusao", ""))

        d_nuc = ddrop(list(NUCLEO_DISTRITO.keys()),
                      value=dados.get("nucleo", ""), expand=True)
        d_dis = inp("Distrito", value=dados.get("distrito", ""),
                    read_only=True, expand=True)
        d_bai = ddrop(
            DISTRITO_BAIRROS.get(dados.get("nucleo", ""), []),
            value=dados.get("bairro", "")
        )
        d_cat = ddrop(list(CAT_SUBCAT.keys()),
                      value=dados.get("categoria", ""), expand=True)
        d_sub = ddrop(
            CAT_SUBCAT.get(dados.get("categoria", ""), []),
            value=dados.get("subcategoria", ""), expand=True
        )
        d_sit = ddrop(SITUACOES, value=dados.get("situacao", ""))
        e_enc = inp("Encarregado", value=dados.get("encarregado", ""))
        lbl_er = ft.Text("", color="#ff6666", size=13)

        def on_nucleo(e):
            nuc = d_nuc.value or ""
            d_dis.value = NUCLEO_DISTRITO.get(nuc, "")
            bairros = DISTRITO_BAIRROS.get(nuc, [])
            d_bai.options = [ft.dropdown.Option(b) for b in bairros]
            d_bai.value   = None
            self.page.update()

        def on_cat(e):
            cat  = d_cat.value or ""
            subs = CAT_SUBCAT.get(cat, [])
            d_sub.options = [ft.dropdown.Option(s) for s in subs]
            d_sub.value   = None
            self.page.update()

        d_nuc.on_change = on_nucleo
        d_cat.on_change = on_cat

        if modo == "novo":
            e_data.value = datetime.now().strftime("%d/%m/%Y")
            e_sol.value  = gerar_proxima(self.page)

        def _snap():
            return {
                "Data Abertura":  e_data.value or "",
                "Solicitação":    e_sol.value  or "",
                "Núcleo":         d_nuc.value  or "",
                "Solicitante":    e_sol2.value or "",
                "Endereço":       e_end.value  or "",
                "Bairro":         d_bai.value  or "",
                "Distrito":       d_dis.value  or "",
                "Categoria":      d_cat.value  or "",
                "Subcategoria":   d_sub.value  or "",
                "Encarregado":    e_enc.value  or "",
                "Situação":       d_sit.value  or "",
                "Data Início":    e_di.value   or "",
                "Data Conclusão": e_dc.value   or "",
                "Observação":     e_obs.value  or "",
                "Localização":    e_loc.value  or "",
            }

        _snap_orig = _snap() if modo == "editar" else {}

        def _salvar(e):
            data_ab = (e_data.value or "").strip()
            sol     = (e_sol.value  or "").strip()
            if not data_ab or not sol:
                lbl_er.value = "⚠  Data e Número são obrigatórios."
                self.page.update()
                return
            sit = (d_sit.value or "").upper()
            if "EXECU" in sit and not (e_di.value or "").strip():
                lbl_er.value = "⚠  Em Execução requer Data de Início."
                self.page.update()
                return
            if "FINALIZ" in sit and not (e_dc.value or "").strip():
                lbl_er.value = "⚠  Finalizado requer Data de Conclusão."
                self.page.update()
                return

            reg = {
                "data_abertura":  data_ab,
                "solicitacao":    sol,
                "nucleo":         d_nuc.value or "",
                "solicitante":    tc(e_sol2.value or ""),
                "endereco":       tc(e_end.value  or ""),
                "bairro":         d_bai.value or "",
                "distrito":       d_dis.value or "",
                "categoria":      d_cat.value or "",
                "subcategoria":   d_sub.value or "",
                "encarregado":    tc(e_enc.value  or ""),
                "situacao":       (d_sit.value or "").upper(),
                "data_inicio":    (e_di.value  or "").strip(),
                "data_conclusao": (e_dc.value  or "").strip(),
                "observacao":     tc(e_obs.value  or ""),
                "localizacao":    (e_loc.value or "").strip(),
            }
            try:
                conn = get_conn(self.page)
                if modo == "novo":
                    conn.execute("""
                        INSERT INTO solicitacoes
                        (data_abertura,solicitacao,nucleo,solicitante,endereco,bairro,
                         distrito,categoria,subcategoria,encarregado,situacao,
                         data_inicio,data_conclusao,observacao,localizacao)
                        VALUES
                        (:data_abertura,:solicitacao,:nucleo,:solicitante,:endereco,:bairro,
                         :distrito,:categoria,:subcategoria,:encarregado,:situacao,
                         :data_inicio,:data_conclusao,:observacao,:localizacao)
                    """, reg)
                    conn.commit()
                    conn.close()
                    self._snack(f"✅  Solicitação {sol} criada!")
                    self._ir_lista()
                else:
                    reg["id"] = sol_id
                    conn.execute("""
                        UPDATE solicitacoes SET
                            data_abertura=:data_abertura, nucleo=:nucleo,
                            solicitante=:solicitante, endereco=:endereco,
                            bairro=:bairro, distrito=:distrito,
                            categoria=:categoria, subcategoria=:subcategoria,
                            encarregado=:encarregado, situacao=:situacao,
                            data_inicio=:data_inicio, data_conclusao=:data_conclusao,
                            observacao=:observacao, localizacao=:localizacao,
                            atualizado_em=datetime('now','localtime')
                        WHERE id=:id
                    """, reg)
                    conn.commit()
                    novo  = _snap()
                    diff  = [
                        (k, _snap_orig.get(k, ""), novo.get(k, ""))
                        for k in novo
                        if _snap_orig.get(k, "") != novo.get(k, "")
                    ]
                    conn.close()
                    salvar_historico(sol_id, sol, self.login_str, diff, self.page)
                    self._snack(f"✅  Solicitação {sol} atualizada!")
                    self._ir_lista()
            except sqlite3.IntegrityError:
                lbl_er.value = f"❌  Solicitação '{sol}' já existe!"
                self.page.update()
            except Exception as ex:
                lbl_er.value = f"❌  Erro: {ex}"
                self.page.update()

        def _confirmar_excluir():
            def _excluir(ev):
                dlg.open = False
                self.page.update()
                try:
                    conn = get_conn(self.page)
                    row  = conn.execute(
                        "SELECT * FROM solicitacoes WHERE id=?", (sol_id,)
                    ).fetchone()
                    if row:
                        conn.execute(
                            "INSERT INTO excluidos "
                            "(solicitacao,nucleo,excluido_por,excluido_em,dados_json)"
                            " VALUES (?,?,?,?,?)",
                            (row["solicitacao"], row["nucleo"], self.login_str,
                             datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                             json.dumps(dict(row), ensure_ascii=False))
                        )
                        conn.execute("DELETE FROM solicitacoes WHERE id=?", (sol_id,))
                        conn.commit()
                    conn.close()
                    self._snack("🗑️  Solicitação excluída.")
                    self._ir_lista()
                except Exception as ex:
                    self._snack(f"Erro: {ex}", "#c62828")

            dlg = ft.AlertDialog(
                title=ft.Text("Confirmar Exclusão", color=TEXT),
                content=ft.Text(
                    f"Excluir {dados.get('solicitacao', '')}?\n"
                    "Esta ação não pode ser desfeita.",
                    color=TEXT2
                ),
                bgcolor=CARD,
                actions=[
                    ft.TextButton("Cancelar",
                        on_click=lambda ev: (
                            setattr(dlg, "open", False), self.page.update()
                        )
                    ),
                    ft.ElevatedButton(
                        "Excluir", on_click=_excluir,
                        style=ft.ButtonStyle(
                            bgcolor={ft.ControlState.DEFAULT: DANGER},
                            color={ft.ControlState.DEFAULT: WHITE},
                        ),
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

        # Botão de materiais (só edição)
        mat_btn = ft.Container()
        if modo == "editar" and sol_id:
            mat_btn = secao("🧱  Materiais", [
                botao("Gerenciar Materiais",
                      on_click=lambda e: self._ir_materiais(
                          sol_id, dados.get("solicitacao", "")
                      ),
                      bg="#1a3a6b", expand=True),
            ])

        # Histórico resumido (só edição)
        hist_ctrl = ft.Container()
        if modo == "editar" and sol_id:
            conn = get_conn(self.page)
            hist = conn.execute(
                "SELECT usuario, data_hora, campo, valor_anterior, valor_novo "
                "FROM historico WHERE solicitacao_id=? ORDER BY id DESC LIMIT 10",
                (sol_id,)
            ).fetchall()
            conn.close()
            if hist:
                itens = [
                    ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(h["usuario"], size=11, color=ACCENT),
                                ft.Text(h["data_hora"], size=10, color=TEXT3),
                            ], spacing=6),
                            ft.Text(h["campo"], size=12, color=TEXT2,
                                    weight=ft.FontWeight.W_600),
                            ft.Row([
                                ft.Text(h["valor_anterior"] or "—",
                                        size=11, color="#ff8888"),
                                ft.Icon(ft.Icons.ARROW_FORWARD, size=12, color=TEXT3),
                                ft.Text(h["valor_novo"] or "—",
                                        size=11, color="#7aff9a"),
                            ], spacing=4, wrap=True),
                        ], spacing=3),
                        bgcolor=BG2, border_radius=6, padding=10,
                        border=ft.border.all(1, BORDER),
                    )
                    for h in hist
                ]
                hist_ctrl = secao("📋  Histórico", itens)
            else:
                hist_ctrl = secao("📋  Histórico", [
                    ft.Text("Sem alterações registradas.", color=TEXT3, size=12)
                ])

        appbar_actions = [
            ft.IconButton(ft.Icons.SAVE, icon_color="#4caf50",
                          tooltip="Salvar", on_click=_salvar),
        ]
        if modo == "editar":
            appbar_actions.append(
                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="#ef5350",
                              tooltip="Excluir",
                              on_click=lambda e: _confirmar_excluir())
            )

        self.page.appbar = ft.AppBar(
            title=ft.Text(titulo, color=TEXT, size=15),
            bgcolor=CARD,
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK, icon_color=TEXT,
                on_click=lambda e: self._ir_lista()
            ),
            actions=appbar_actions,
        )

        self.page.controls.append(ft.ListView([
            ft.Container(ft.Column([
                secao("🪪  Identificação", [
                    ft.Row([
                        ft.Column([lbl("Data Abertura *"), e_data], expand=True),
                        ft.Column([lbl("Nº Solicitação *"), e_sol], expand=True),
                    ], spacing=10),
                    lbl("Solicitante"), e_sol2,
                ]),
                secao("📍  Localização", [
                    lbl("Endereço"), e_end,
                    ft.Row([
                        ft.Column([lbl("Núcleo"), d_nuc], expand=True),
                        ft.Column([lbl("Distrito"), d_dis], expand=True),
                    ], spacing=10),
                    lbl("Bairro"), d_bai,
                    lbl("Coordenadas"), e_loc,
                ]),
                secao("🔧  Serviço", [
                    ft.Row([
                        ft.Column([lbl("Categoria"), d_cat], expand=True),
                        ft.Column([lbl("Subcategoria"), d_sub], expand=True),
                    ], spacing=10),
                    lbl("Encarregado"), e_enc,
                ]),
                secao("📊  Status", [
                    lbl("Situação"), d_sit,
                    ft.Row([
                        ft.Column([lbl("Data Início"), e_di], expand=True),
                        ft.Column([lbl("Data Conclusão"), e_dc], expand=True),
                    ], spacing=10),
                    lbl("Observação"), e_obs,
                ]),
                mat_btn,
                hist_ctrl,
                lbl_er,
                botao("💾  Salvar", on_click=_salvar, bg=SUCCESS, expand=True),
                ft.Container(height=24),
            ], spacing=0), padding=12)
        ], expand=True, padding=0))
        self.page.update()

    # ── MATERIAIS ────────────────────────────────────────────────
    def _ir_materiais(self, sol_id, sol_num):
        self._clear()
        conn = get_conn(self.page)
        existentes = conn.execute(
            "SELECT id, nome, quantidade, tipo FROM materiais "
            "WHERE solicitacao_id=? ORDER BY id",
            (sol_id,)
        ).fetchall()
        conn.close()

        linhas     = []
        col_linhas = ft.Column([], spacing=6, scroll=ft.ScrollMode.AUTO)
        lbl_er     = ft.Text("", color="#ff6666", size=13)

        def _add(nome="", qtd="", tipo=""):
            e_n = ft.TextField(
                value=nome, hint_text="Material",
                bgcolor=BG2, color=TEXT, border_color=BORDER,
                focused_border_color=ACCENT, border_radius=6,
                content_padding=ft.padding.symmetric(horizontal=8, vertical=8),
                text_size=13, expand=True,
            )
            e_q = ft.TextField(
                value=qtd, hint_text="Qtd",
                bgcolor=BG2, color=TEXT, border_color=BORDER,
                focused_border_color=ACCENT, border_radius=6,
                content_padding=ft.padding.symmetric(horizontal=8, vertical=8),
                text_size=13, width=80,
            )
            e_t = ft.TextField(
                value=tipo, hint_text="Un/Tipo",
                bgcolor=BG2, color=TEXT, border_color=BORDER,
                focused_border_color=ACCENT, border_radius=6,
                content_padding=ft.padding.symmetric(horizontal=8, vertical=8),
                text_size=13, width=90,
            )
            d = {"n": e_n, "q": e_q, "t": e_t}
            linhas.append(d)

            row_ref = ft.Ref()

            def rm(ev, _d=d):
                linhas.remove(_d)
                row_ref.current.visible = False
                self.page.update()

            row = ft.Row(
                [e_n, e_q, e_t,
                 ft.IconButton(ft.Icons.DELETE, icon_color="#ef5350",
                               icon_size=20, on_click=rm)],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ref=row_ref,
            )
            col_linhas.controls.append(row)
            self.page.update()

        for r in existentes:
            _add(r["nome"], r["quantidade"] or "", r["tipo"] or "")
        if not existentes:
            _add()

        def _salvar_mat(e):
            itens, erros = [], []
            for i, d in enumerate(linhas):
                n = (d["n"].value or "").strip()
                q = (d["q"].value or "").strip()
                t = (d["t"].value or "").strip()
                if not n:
                    continue
                if not q:
                    erros.append(f"Linha {i+1}: '{n}' sem quantidade.")
                else:
                    itens.append((n, q, t))
            if erros:
                lbl_er.value = "\n".join(erros)
                self.page.update()
                return
            try:
                conn = get_conn(self.page)
                conn.execute(
                    "DELETE FROM materiais WHERE solicitacao_id=?", (sol_id,)
                )
                for n, q, t in itens:
                    conn.execute(
                        "INSERT INTO materiais "
                        "(solicitacao_id, nome, quantidade, tipo) VALUES (?,?,?,?)",
                        (sol_id, n, q, t)
                    )
                conn.commit()
                conn.close()
                self._snack(f"✅  {len(itens)} material(is) salvo(s)!")
                self._ir_formulario("editar", sol_id)
            except Exception as ex:
                lbl_er.value = f"❌  {ex}"
                self.page.update()

        self.page.appbar = ft.AppBar(
            title=ft.Text(f"Materiais — {sol_num}", color=TEXT, size=14),
            bgcolor=CARD,
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK, icon_color=TEXT,
                on_click=lambda e: self._ir_formulario("editar", sol_id)
            ),
            actions=[
                ft.IconButton(ft.Icons.ADD, icon_color="#4caf50",
                              on_click=lambda e: _add()),
                ft.IconButton(ft.Icons.SAVE, icon_color=ACCENT,
                              on_click=_salvar_mat),
            ],
        )
        self.page.controls.append(ft.ListView([
            ft.Container(ft.Column([
                ft.Text("Materiais utilizados na solicitação",
                        size=12, color=TEXT3),
                ft.Container(height=4),
                col_linhas,
                lbl_er,
                ft.Container(height=8),
                botao("💾  Salvar Materiais", on_click=_salvar_mat,
                      bg=SUCCESS, expand=True),
                ft.Container(height=24),
            ], spacing=8), padding=14)
        ], expand=True, padding=0))
        self.page.update()

    # ── DIALOGS ──────────────────────────────────────────────────
    def _dialog_sync(self):
        db_path = get_db_path(self.page)
        dlg = ft.AlertDialog(
            title=ft.Text("📂  Sincronização", color=ACCENT),
            bgcolor=CARD,
            content=ft.Column([
                ft.Text("Banco de dados do tablet:", color=TEXT2, size=13),
                ft.Container(
                    ft.Text(db_path, color=ACCENT, size=11, selectable=True),
                    bgcolor=BG2, border_radius=6, padding=10,
                    border=ft.border.all(1, BORDER),
                ),
                ft.Container(height=8),
                ft.Text("Para sincronizar com o PC:", color=TEXT2, size=13,
                        weight=ft.FontWeight.W_600),
                ft.Text(
                    "1. Conecte o tablet via cabo USB\n"
                    "2. Copie o arquivo reparos.db\n"
                    "3. Cole no PC substituindo o banco existente\n"
                    "4. O schema é compatível com o sistema desktop",
                    color=TEXT2, size=12,
                ),
            ], tight=True, width=300, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Fechar",
                    on_click=lambda e: (
                        setattr(dlg, "open", False), self.page.update()
                    )
                )
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _dialog_sobre(self):
        db_path = get_db_path(self.page)
        dlg = ft.AlertDialog(
            title=ft.Text("Sobre", color=ACCENT),
            bgcolor=CARD,
            content=ft.Column([
                ft.Text("Sistema de Gerenciamento dos Reparos",
                        color=TEXT, weight=ft.FontWeight.BOLD, size=14),
                ft.Text("Versão Mobile — Flet 0.24.1", color=TEXT2, size=12),
                ft.Text("Desenvolvido por Valdemir Vieira Alves",
                        color=TEXT2, size=12),
                ft.Text("(21) 99431-3049", color=ACCENT, size=12),
                ft.Container(height=6),
                ft.Text(f"Banco: {db_path}", color=TEXT3, size=10, selectable=True),
            ], tight=True, spacing=6, scroll=ft.ScrollMode.AUTO, width=280),
            actions=[
                ft.TextButton("OK",
                    on_click=lambda e: (
                        setattr(dlg, "open", False), self.page.update()
                    )
                )
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()


def main(page: ft.Page):
    App(page)


ft.app(target=main)
