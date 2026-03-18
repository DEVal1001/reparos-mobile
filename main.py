"""
Sistema de Gerenciamento dos Reparos — Versão Mobile (Flet)
Banco SQLite local no tablet. Sincronização manual via arquivo .db
"""

import flet as ft
import sqlite3, hashlib, json, os, threading
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
        "Reparo de estruturas de madeira", "Travessia para pedestres", "Reparo de estruturas de concreto",
        "Reparo de abrigo de passageiros", "Fresagem de vias", "Reparo de telhado"],
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
    "CENTRO I": "1º DISTRITO - CENTRO", "CENTRO II": "1º DISTRITO - CENTRO",
    "CORDEIRINHO": "2º DISTRITO - PONTA NEGRA", "ESPRAIADO": "2º DISTRITO - PONTA NEGRA",
    "INOÃ": "3º DISTRITO - INOÃ", "SÃO JOSÉ": "3º DISTRITO - INOÃ",
    "ITAIPUAÇU I": "4º DISTRITO - ITAIPUAÇU", "ITAIPUAÇU II": "4º DISTRITO - ITAIPUAÇU",
}

DISTRITO_BAIRROS = {
    "CENTRO I":    ["Centro","Mumbuca","Araçatiba","Flamengo","Barra de Maricá"],
    "CENTRO II":   ["Centro","Mumbuca","Araçatiba","Flamengo","Barra de Maricá"],
    "CORDEIRINHO": ["Cordeirinho","Ponta Negra","Bambuí","Guaratiba","Bananal"],
    "ESPRAIADO":   ["Espraiado"],
    "INOÃ":        ["Inoã","São José"],
    "SÃO JOSÉ":    ["Inoã","São José"],
    "ITAIPUAÇU I": ["Itaipuaçu","Recanto","Jardim Atlântico","Barroco"],
    "ITAIPUAÇU II":["Itaipuaçu","Recanto","Jardim Atlântico","Barroco"],
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
WARNING = "#b5851a"

SIT_CORES = {
    "ABERTO":      ("#3a3000", "#ffdd66"),
    "EM EXECUÇÃO": ("#0d2a4a", "#88ccff"),
    "CANCELADO":   ("#3a0d0d", "#ff8888"),
    "FINALIZADO":  ("#0d3a1a", "#7aff9a"),
}

# ── Database ──────────────────────────────────────────────────────
_DB_PATH = None

def get_db_path(page: ft.Page = None) -> str:
    global _DB_PATH
    if _DB_PATH:
        return _DB_PATH
    if page:
        base = page.app_data_dir or os.path.expanduser("~")
    else:
        base = os.path.expanduser("~")
    _DB_PATH = os.path.join(base, "reparos.db")
    return _DB_PATH

def get_conn(page=None) -> sqlite3.Connection:
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
            solicitacao TEXT NOT NULL, nucleo TEXT, excluido_por TEXT,
            excluido_em TEXT NOT NULL, dados_json TEXT
        );
    """)
    conn.commit()
    conn.close()

def hash_senha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def autenticar(login: str, senha: str, page=None):
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

def gerar_proxima(page=None) -> str:
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
            try: num = int(row["solicitacao"].split("/")[0]) + 1
            except: pass
        return f"{num:05d}/{ano}"
    except:
        return f"00001/{ano}"

def tc(s: str) -> str:
    if not s: return s
    prepos = {"a","as","o","os","da","das","do","dos","de","em","no","na","nos","nas",
              "ao","aos","por","e","ou","com","sem","sob","sobre","entre","para",
              "pelo","pela","pelos","pelas","num","numa"}
    words = s.strip().split()
    return " ".join(w.capitalize() if i==0 or w.lower() not in prepos else w.lower()
                    for i, w in enumerate(words))

def salvar_historico(sol_id, sol_num, usuario, diff, page=None):
    if not diff: return
    try:
        conn = get_conn(page)
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        for campo, antes, depois in diff:
            conn.execute(
                "INSERT INTO historico (solicitacao_id,solicitacao_num,usuario,data_hora,campo,valor_anterior,valor_novo)"
                " VALUES (?,?,?,?,?,?,?)",
                (sol_id, sol_num, usuario, now, campo, antes or "", depois or "")
            )
        conn.commit()
        conn.close()
    except Exception as e:
        print("historico:", e)

# ── Helpers UI ────────────────────────────────────────────────────
def campo_label(texto: str) -> ft.Text:
    return ft.Text(texto, size=12, color=TEXT2, weight=ft.FontWeight.W_600)

def texto_field(hint="", value="", password=False, expand=True, width=None, read_only=False) -> ft.TextField:
    return ft.TextField(
        hint_text=hint, value=value, password=password,
        can_reveal_password=password,
        bgcolor=BG2, color=TEXT,
        border_color=BORDER, focused_border_color=ACCENT,
        border_radius=8, content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        text_size=14, expand=expand, width=width, read_only=read_only,
        hint_style=ft.TextStyle(color=TEXT3),
    )

def dropdown_field(options: list, value="", hint="— Selecione —", expand=True, width=None,
                   on_change=None) -> ft.Dropdown:
    return ft.Dropdown(
        options=[ft.dropdown.Option(o) for o in options],
        value=value or None, hint_text=hint,
        bgcolor=BG2, color=TEXT,
        border_color=BORDER, focused_border_color=ACCENT,
        border_radius=8, content_padding=ft.padding.symmetric(horizontal=12, vertical=4),
        text_size=14, expand=expand, width=width, on_change=on_change,
    )

def btn(texto, on_click=None, color=ACCENT, bgcolor=None, expand=False, icon=None) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        text=texto, on_click=on_click, expand=expand,
        icon=icon,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=bgcolor or {"": "#1a4a8c", ft.ControlState.HOVERED: "#1f5aad"},
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
        ),
    )

def sit_chip(situacao: str) -> ft.Container:
    sit = (situacao or "").upper()
    bg, fg = SIT_CORES.get(sit, (CARD, TEXT2))
    return ft.Container(
        content=ft.Text(situacao or "—", size=11, color=fg, weight=ft.FontWeight.W_700),
        bgcolor=bg, border_radius=12,
        padding=ft.padding.symmetric(horizontal=10, vertical=3),
    )

def secao(titulo: str, controles: list) -> ft.Container:
    return ft.Container(
        content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.LABEL, color=ACCENT, size=16),
                    ft.Text(titulo, size=13, color=ACCENT, weight=ft.FontWeight.W_700)]),
            ft.Divider(height=1, color=BORDER),
            *controles
        ], spacing=10),
        bgcolor=BG3, border_radius=10,
        border=ft.border.all(1, BORDER),
        padding=14, margin=ft.margin.only(bottom=10),
    )

# ── App principal ─────────────────────────────────────────────────
class App:
    def __init__(self, page: ft.Page):
        self.page = page
        self.usuario = None
        self.login_str = ""
        self._setup_page()
        init_db(page)
        self._ir_login()

    def _setup_page(self):
        p = self.page
        p.title = "Gerenciamento dos Reparos"
        p.theme_mode = ft.ThemeMode.DARK
        p.bgcolor = BG
        p.padding = 0
        p.fonts = {"Segoe UI": "https://fonts.googleapis.com/css2?family=Roboto"}
        p.theme = ft.Theme(color_scheme_seed=ACCENT)

    def _snack(self, msg: str, cor=ft.Colors.GREEN_700):
        self.page.snack_bar = ft.SnackBar(
            ft.Text(msg, color=ft.Colors.WHITE),
            bgcolor=cor, duration=3000
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _ir_login(self):
        self.page.controls.clear()
        self.page.appbar = None
        self.page.floating_action_button = None
        self.page.controls.append(self._tela_login())
        self.page.update()

    # ── TELA DE LOGIN ─────────────────────────────────────────────
    def _tela_login(self) -> ft.View:
        e_login = texto_field("Login", expand=True)
        e_senha = texto_field("Senha", password=True, expand=True)
        lbl_erro = ft.Text("", color="#ff6666", size=13)

        def entrar(e):
            l = e_login.value.strip()
            s = e_senha.value
            if not l or not s:
                lbl_erro.value = "⚠  Preencha login e senha."
                self.page.update(); return
            u = autenticar(l, s, self.page)
            if u:
                self.usuario = u
                self.login_str = l
                self._ir_lista()
            else:
                lbl_erro.value = "❌  Login ou senha inválidos."
                self.page.update()

        e_senha.on_submit = entrar

        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.CLIPBOARD_OUTLINED if hasattr(ft.Icons,"CLIPBOARD_OUTLINED")
                                else ft.Icons.LIST_ALT, color=ACCENT, size=56),
                        ft.Text("Gerenciamento dos Reparos", size=18, color=ACCENT,
                                weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        ft.Text("Desenvolvido por Valdemir Vieira Alves", size=11,
                                color=TEXT3, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    bgcolor=CARD, padding=28,
                    border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
                ),
                # Form
                ft.Container(
                    content=ft.Column([
                        ft.Text("🔐  Acesso ao Sistema", size=16, color=TEXT,
                                weight=ft.FontWeight.BOLD),
                        ft.Text("Informe seu login e senha", size=12, color=TEXT3),
                        ft.Container(height=8),
                        campo_label("Login"),
                        e_login,
                        campo_label("Senha"),
                        e_senha,
                        lbl_erro,
                        btn("▶  ENTRAR", on_click=entrar, expand=True,
                            bgcolor={"": SUCCESS, ft.ControlState.HOVERED: "#24934f"}),
                        ft.Divider(color=BORDER),
                        ft.TextButton(
                            "➕  Cadastrar Novo Usuário",
                            on_click=lambda e: self._ir_cadastro(),
                            style=ft.ButtonStyle(color=TEXT2),
                        ),
                        ft.TextButton(
                            "⚙️  Sobre / Info",
                            on_click=lambda e: self._dialog_sobre(),
                            style=ft.ButtonStyle(color=TEXT3),
                        ),
                    ], spacing=8),
                    padding=24, expand=True,
                ),
            ], spacing=0, expand=True),
            expand=True, bgcolor=BG,
        )

    # ── CADASTRO ──────────────────────────────────────────────────
    def _ir_cadastro(self):
        e_adm  = texto_field("Senha do administrador", password=True)
        e_nome = texto_field("Nome")
        e_sob  = texto_field("Sobrenome")
        e_log  = texto_field("Login")
        e_sen  = texto_field("Senha (mín. 4 caracteres)", password=True)
        e_con  = texto_field("Confirmar senha", password=True)
        lbl    = ft.Text("", color="#ff6666", size=13)

        def salvar(e):
            if e_adm.value != ADMIN_PASSWORD:
                lbl.value = "❌  Senha de administrador incorreta."
                self.page.update(); return
            n, s, l, p, c = (e_nome.value.strip(), e_sob.value.strip(),
                              e_log.value.strip(), e_sen.value, e_con.value)
            if not all([n, s, l, p, c]):
                lbl.value = "⚠  Preencha todos os campos."; self.page.update(); return
            if len(p) < 4:
                lbl.value = "⚠  Senha mínimo 4 caracteres."; self.page.update(); return
            if p != c:
                lbl.value = "❌  Senhas não coincidem."; self.page.update(); return
            ok, msg = cadastrar_usuario(n, s, l, p, self.page)
            if ok:
                self._snack(f"✅  Usuário '{n} {s}' cadastrado!")
                self._ir_login()
            else:
                lbl.value = f"❌  {msg}"; self.page.update()

        self.page.controls.clear()
        self.page.appbar = ft.AppBar(
            title=ft.Text("Cadastrar Usuário", color=TEXT),
            bgcolor=CARD, color=TEXT,
            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self._ir_login(),
                                  icon_color=TEXT),
        )
        self.page.controls.append(
            ft.ListView([
                ft.Container(
                    ft.Column([
                        ft.Text("👤  Novo Usuário", size=16, color=ACCENT, weight=ft.FontWeight.BOLD),
                        ft.Text("Requer senha do administrador", size=12, color=TEXT3),
                        ft.Container(height=4),
                        campo_label("Senha do Administrador *"), e_adm,
                        campo_label("Nome *"), e_nome,
                        campo_label("Sobrenome *"), e_sob,
                        campo_label("Login *"), e_log,
                        campo_label("Senha *"), e_sen,
                        campo_label("Confirmar Senha *"), e_con,
                        lbl,
                        btn("💾  Salvar Usuário", on_click=salvar, expand=True,
                            bgcolor={"": SUCCESS, ft.ControlState.HOVERED: "#24934f"}),
                    ], spacing=8),
                    padding=16,
                )
            ], expand=True, padding=0)
        )
        self.page.update()

    # ── LISTA DE SOLICITAÇÕES ─────────────────────────────────────
    def _ir_lista(self):
        self._filtros = {"q": "", "nucleo": "", "situacao": "", "categoria": ""}
        self._lista_page = 1
        self._per_page = 30

        self.page.controls.clear()
        self.page.appbar = ft.AppBar(
            title=ft.Text("Solicitações", color=TEXT),
            bgcolor=CARD,
            actions=[
                ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_color=ft.Colors.GREEN_400,
                              tooltip="Nova Solicitação",
                              on_click=lambda e: self._ir_formulario(modo="novo")),
                ft.IconButton(ft.Icons.SYNC, icon_color=ACCENT, tooltip="Info de Sincronização",
                              on_click=lambda e: self._dialog_sync()),
                ft.IconButton(ft.Icons.LOGOUT, icon_color=TEXT3, tooltip="Sair",
                              on_click=lambda e: self._ir_login()),
            ],
        )

        # Filtros
        self._f_q   = ft.TextField(
            hint_text="🔍  Buscar por nº, solicitante, endereço...",
            bgcolor=BG2, color=TEXT, border_color=BORDER, focused_border_color=ACCENT,
            border_radius=8, content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
            text_size=13, on_change=self._on_busca,
        )
        self._f_nuc = dropdown_field([""] + list(NUCLEO_DISTRITO.keys()), hint="Núcleo",
                                     expand=True, on_change=self._on_filtro)
        self._f_sit = dropdown_field([""] + SITUACOES, hint="Situação",
                                     expand=True, on_change=self._on_filtro)

        self._lbl_total = ft.Text("", size=12, color=TEXT3)
        self._lista_col = ft.Column([], spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)

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
        self._filtros["q"] = e.control.value.strip()
        self._lista_page = 1
        self._carregar_lista()

    def _on_filtro(self, e):
        self._filtros["nucleo"]   = self._f_nuc.value or ""
        self._filtros["situacao"] = self._f_sit.value or ""
        self._lista_page = 1
        self._carregar_lista()

    def _carregar_lista(self):
        q        = self._filtros.get("q","")
        nucleo   = self._filtros.get("nucleo","")
        situacao = self._filtros.get("situacao","")
        offset   = (self._lista_page - 1) * self._per_page

        where, params = ["1=1"], []
        if q:
            where.append("(solicitacao LIKE ? OR solicitante LIKE ? OR endereco LIKE ?)")
            params += [f"%{q}%"]*3
        if nucleo:
            where.append("nucleo=?"); params.append(nucleo)
        if situacao:
            where.append("situacao=?"); params.append(situacao)

        sql_w = " AND ".join(where)
        conn = get_conn(self.page)
        total = conn.execute(f"SELECT COUNT(*) FROM solicitacoes WHERE {sql_w}", params).fetchone()[0]
        rows  = conn.execute(
            f"SELECT id, data_abertura, solicitacao, nucleo, solicitante, "
            f"endereco, bairro, situacao, categoria, encarregado "
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
                ft.Container(ft.Text("Nenhum registro encontrado.", color=TEXT3,
                                     text_align=ft.TextAlign.CENTER),
                             alignment=ft.alignment.center, expand=True, padding=40)
            )
        else:
            for r in rows:
                self._lista_col.controls.append(self._card_solicitacao(dict(r)))

        # Paginação
        if total > self._per_page:
            total_pgs = (total + self._per_page - 1) // self._per_page
            self._lista_col.controls.append(
                ft.Row([
                    ft.IconButton(ft.Icons.CHEVRON_LEFT,
                                  disabled=self._lista_page <= 1,
                                  on_click=lambda e: self._pag(-1)),
                    ft.Text(f"{self._lista_page}/{total_pgs}", color=TEXT2),
                    ft.IconButton(ft.Icons.CHEVRON_RIGHT,
                                  disabled=self._lista_page >= total_pgs,
                                  on_click=lambda e: self._pag(1)),
                ], alignment=ft.MainAxisAlignment.CENTER)
            )

        self.page.update()

    def _pag(self, delta):
        self._lista_page += delta
        self._carregar_lista()

    def _card_solicitacao(self, r: dict) -> ft.Container:
        sit = (r.get("situacao") or "").upper()
        bg_map = {"ABERTO":"#2a2000","EM EXECUÇÃO":"#0a1a2e",
                  "CANCELADO":"#2a0d0d","FINALIZADO":"#0d2a18"}
        bg_card = bg_map.get(sit, BG3)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(r.get("solicitacao","—"), size=14, color="#a0c8ff",
                            weight=ft.FontWeight.BOLD, expand=True),
                    sit_chip(r.get("situacao","—")),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text(r.get("data_abertura",""), size=11, color=TEXT3),
                    ft.Text("·", color=TEXT3),
                    ft.Text(r.get("nucleo","—"), size=11, color=TEXT2),
                ], spacing=4),
                ft.Text(r.get("solicitante","—"), size=12, color=TEXT2),
                ft.Text(
                    f"{r.get('endereco','')}{', '+r.get('bairro','') if r.get('bairro') else ''}",
                    size=11, color=TEXT3, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS
                ),
                ft.Row([
                    ft.Text(r.get("categoria","—"), size=11, color=TEXT3, expand=True),
                    ft.TextButton("Editar →",
                        on_click=lambda e, rid=r["id"]: self._ir_formulario("editar", rid),
                        style=ft.ButtonStyle(color=ACCENT, padding=ft.padding.all(0)),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=4),
            bgcolor=bg_card, border_radius=10,
            border=ft.border.all(1, BORDER),
            padding=12,
            on_click=lambda e, rid=r["id"]: self._ir_formulario("editar", rid),
        )

    # ── FORMULÁRIO ────────────────────────────────────────────────
    def _ir_formulario(self, modo="novo", sol_id=None):
        dados = {}
        if modo == "editar" and sol_id:
            conn = get_conn(self.page)
            row = conn.execute("SELECT * FROM solicitacoes WHERE id=?", (sol_id,)).fetchone()
            conn.close()
            if row: dados = dict(row)

        self.page.controls.clear()

        titulo = "Nova Solicitação" if modo == "novo" else f"Editar — {dados.get('solicitacao','')}"
        self.page.appbar = ft.AppBar(
            title=ft.Text(titulo, color=TEXT, size=15),
            bgcolor=CARD,
            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self._ir_lista(),
                                  icon_color=TEXT),
            actions=[
                ft.IconButton(ft.Icons.SAVE, icon_color=ft.Colors.GREEN_400,
                              tooltip="Salvar", on_click=lambda e: _salvar(e)),
            ] + ([
                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400,
                              tooltip="Excluir", on_click=lambda e: _confirmar_excluir()),
            ] if modo == "editar" else []),
        )

        # Campos
        e_data = texto_field("DD/MM/AAAA", value=dados.get("data_abertura",""))
        e_sol  = texto_field("00001/2026", value=dados.get("solicitacao",""),
                             read_only=(modo=="editar"))
        e_sol2 = texto_field("Solicitante", value=dados.get("solicitante",""))
        e_end  = texto_field("Endereço", value=dados.get("endereco",""))
        e_loc  = texto_field("Ex: 22°57'43.6\"S 42°57'56.6\"W", value=dados.get("localizacao",""))
        e_obs  = ft.TextField(
            hint_text="Observações...", value=dados.get("observacao",""),
            bgcolor=BG2, color=TEXT, border_color=BORDER, focused_border_color=ACCENT,
            border_radius=8, multiline=True, min_lines=3, max_lines=6,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=10), text_size=14,
        )
        e_di   = texto_field("DD/MM/AAAA", value=dados.get("data_inicio",""))
        e_dc   = texto_field("DD/MM/AAAA", value=dados.get("data_conclusao",""))

        d_nuc = dropdown_field(list(NUCLEO_DISTRITO.keys()),
                               value=dados.get("nucleo",""))
        d_dis = texto_field("Distrito", value=dados.get("distrito",""), read_only=True)
        d_bai = dropdown_field(DISTRITO_BAIRROS.get(dados.get("nucleo",""), []),
                               value=dados.get("bairro",""))
        d_cat = dropdown_field(list(CAT_SUBCAT.keys()), value=dados.get("categoria",""))
        d_sub = dropdown_field(CAT_SUBCAT.get(dados.get("categoria",""),[]),
                               value=dados.get("subcategoria",""))
        d_sit = dropdown_field(SITUACOES, value=dados.get("situacao",""))
        e_enc = texto_field("Encarregado", value=dados.get("encarregado",""))

        lbl_erro = ft.Text("", color="#ff6666", size=13)

        def on_nucleo(e):
            nuc = d_nuc.value or ""
            d_dis.value = NUCLEO_DISTRITO.get(nuc, "")
            bairros = DISTRITO_BAIRROS.get(nuc, [])
            d_bai.options = [ft.dropdown.Option(b) for b in bairros]
            d_bai.value = None
            self.page.update()

        def on_cat(e):
            cat = d_cat.value or ""
            subs = CAT_SUBCAT.get(cat, [])
            d_sub.options = [ft.dropdown.Option(s) for s in subs]
            d_sub.value = None
            self.page.update()

        d_nuc.on_change = on_nucleo
        d_cat.on_change = on_cat

        if modo == "novo":
            e_data.value = datetime.now().strftime("%d/%m/%Y")
            e_sol.value  = gerar_proxima(self.page)

        def _snapshot():
            return {
                "Data Abertura":  e_data.value, "Solicitação":  e_sol.value,
                "Núcleo":         d_nuc.value,  "Solicitante":  e_sol2.value,
                "Endereço":       e_end.value,  "Bairro":       d_bai.value,
                "Distrito":       d_dis.value,  "Categoria":    d_cat.value,
                "Subcategoria":   d_sub.value,  "Encarregado":  e_enc.value,
                "Situação":       d_sit.value,  "Data Início":  e_di.value,
                "Data Conclusão": e_dc.value,   "Observação":   e_obs.value,
                "Localização":    e_loc.value,
            }

        _snap_orig = _snapshot() if modo == "editar" else {}

        def _salvar(e):
            data_ab = (e_data.value or "").strip()
            sol     = (e_sol.value or "").strip()
            if not data_ab or not sol:
                lbl_erro.value = "⚠  Data e Número são obrigatórios."
                self.page.update(); return

            sit = (d_sit.value or "").upper()
            if "EXECU" in sit and not (e_di.value or "").strip():
                lbl_erro.value = "⚠  Em Execução requer Data de Início."
                self.page.update(); return
            if "FINALIZ" in sit and not (e_dc.value or "").strip():
                lbl_erro.value = "⚠  Finalizado requer Data de Conclusão."
                self.page.update(); return

            reg = {
                "data_abertura":  data_ab,
                "solicitacao":    sol,
                "nucleo":         d_nuc.value or "",
                "solicitante":    tc(e_sol2.value or ""),
                "endereco":       tc(e_end.value or ""),
                "bairro":         d_bai.value or "",
                "distrito":       d_dis.value or "",
                "categoria":      d_cat.value or "",
                "subcategoria":   d_sub.value or "",
                "encarregado":    tc(e_enc.value or ""),
                "situacao":       (d_sit.value or "").upper(),
                "data_inicio":    (e_di.value or "").strip(),
                "data_conclusao": (e_dc.value or "").strip(),
                "observacao":     tc(e_obs.value or ""),
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
                    conn.commit(); conn.close()
                    self._snack(f"✅  Solicitação {sol} criada!")
                    self._ir_lista()
                else:
                    reg["id"] = sol_id
                    conn.execute("""
                        UPDATE solicitacoes SET
                            data_abertura=:data_abertura, nucleo=:nucleo,
                            solicitante=:solicitante, endereco=:endereco, bairro=:bairro,
                            distrito=:distrito, categoria=:categoria, subcategoria=:subcategoria,
                            encarregado=:encarregado, situacao=:situacao,
                            data_inicio=:data_inicio, data_conclusao=:data_conclusao,
                            observacao=:observacao, localizacao=:localizacao,
                            atualizado_em=datetime('now','localtime')
                        WHERE id=:id
                    """, reg)
                    conn.commit()
                    # Histórico
                    novo = _snapshot()
                    diff = [(k, _snap_orig.get(k,""), novo.get(k,""))
                            for k in novo if _snap_orig.get(k,"") != novo.get(k,"")]
                    conn.close()
                    salvar_historico(sol_id, sol, self.login_str, diff, self.page)
                    self._snack(f"✅  Solicitação {sol} atualizada!")
                    self._ir_lista()
            except sqlite3.IntegrityError:
                lbl_erro.value = f"❌  Solicitação '{sol}' já existe!"
                self.page.update()
            except Exception as ex:
                lbl_erro.value = f"❌  Erro: {ex}"
                self.page.update()

        def _confirmar_excluir():
            def _excluir(e):
                dlg.open = False; self.page.update()
                try:
                    conn = get_conn(self.page)
                    row = conn.execute("SELECT * FROM solicitacoes WHERE id=?", (sol_id,)).fetchone()
                    if row:
                        conn.execute(
                            "INSERT INTO excluidos (solicitacao, nucleo, excluido_por, excluido_em, dados_json)"
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
                    self._snack(f"Erro: {ex}", ft.Colors.RED_700)

            dlg = ft.AlertDialog(
                title=ft.Text("Confirmar Exclusão", color=TEXT),
                content=ft.Text(f"Excluir {dados.get('solicitacao','')}? Esta ação não pode ser desfeita.",
                                color=TEXT2),
                bgcolor=CARD,
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: (setattr(dlg,"open",False),
                                                                    self.page.update())),
                    ft.ElevatedButton("Excluir", on_click=_excluir,
                                      style=ft.ButtonStyle(bgcolor={"":DANGER}, color={"":ft.Colors.WHITE})),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.overlay.append(dlg)
            dlg.open = True; self.page.update()

        # Aba Materiais (só edição)
        def _aba_materiais():
            if modo != "editar" or not sol_id: return ft.Container()
            return secao("🧱  Materiais", [
                ft.ElevatedButton("Gerenciar Materiais",
                    icon=ft.Icons.INVENTORY_2,
                    on_click=lambda e: self._ir_materiais(sol_id, dados.get("solicitacao","")),
                    style=ft.ButtonStyle(
                        bgcolor={"":"#1a3a6b"},color={"":ft.Colors.WHITE},
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                ),
            ])

        # Histórico (só edição)
        def _aba_historico():
            if modo != "editar" or not sol_id: return ft.Container()
            conn = get_conn(self.page)
            hist = conn.execute(
                "SELECT usuario, data_hora, campo, valor_anterior, valor_novo "
                "FROM historico WHERE solicitacao_id=? ORDER BY id DESC LIMIT 20",
                (sol_id,)
            ).fetchall()
            conn.close()
            if not hist:
                return secao("📋  Histórico", [ft.Text("Sem alterações registradas.", color=TEXT3, size=12)])
            itens = [
                ft.Container(
                    ft.Column([
                        ft.Row([ft.Text(h["usuario"], size=11, color=ACCENT),
                                ft.Text(h["data_hora"], size=10, color=TEXT3)], spacing=6),
                        ft.Text(h["campo"], size=12, color=TEXT2, weight=ft.FontWeight.W_600),
                        ft.Row([
                            ft.Text(h["valor_anterior"] or "—", size=11, color="#ff8888"),
                            ft.Icon(ft.Icons.ARROW_FORWARD, size=12, color=TEXT3),
                            ft.Text(h["valor_novo"] or "—", size=11, color="#7aff9a"),
                        ], spacing=4, wrap=True),
                    ], spacing=3),
                    bgcolor=BG2, border_radius=6, padding=10,
                    border=ft.border.all(1, BORDER),
                ) for h in hist
            ]
            return secao("📋  Histórico", itens)

        form = ft.ListView([
            ft.Container(
                ft.Column([
                    # Identificação
                    secao("🪪  Identificação", [
                        ft.Row([
                            ft.Column([campo_label("Data de Abertura *"), e_data], expand=True),
                            ft.Column([campo_label("Nº Solicitação *"), e_sol], expand=True),
                        ], spacing=10),
                        campo_label("Solicitante"), e_sol2,
                    ]),
                    # Localização
                    secao("📍  Localização", [
                        campo_label("Endereço"), e_end,
                        ft.Row([
                            ft.Column([campo_label("Núcleo"), d_nuc], expand=True),
                            ft.Column([campo_label("Distrito"), d_dis], expand=True),
                        ], spacing=10),
                        campo_label("Bairro"), d_bai,
                        campo_label("Coordenadas"), e_loc,
                    ]),
                    # Serviço
                    secao("🔧  Serviço", [
                        ft.Row([
                            ft.Column([campo_label("Categoria"), d_cat], expand=True),
                            ft.Column([campo_label("Subcategoria"), d_sub], expand=True),
                        ], spacing=10),
                        campo_label("Encarregado"), e_enc,
                    ]),
                    # Status
                    secao("📊  Status", [
                        campo_label("Situação"), d_sit,
                        ft.Row([
                            ft.Column([campo_label("Data Início"), e_di], expand=True),
                            ft.Column([campo_label("Data Conclusão"), e_dc], expand=True),
                        ], spacing=10),
                        campo_label("Observação"), e_obs,
                    ]),
                    # Materiais (só edição)
                    _aba_materiais(),
                    # Histórico (só edição)
                    _aba_historico(),
                    # Erro e botão salvar
                    lbl_erro,
                    btn("💾  Salvar", on_click=_salvar, expand=True,
                        bgcolor={"": SUCCESS, ft.ControlState.HOVERED: "#24934f"}),
                    ft.Container(height=20),
                ], spacing=0),
                padding=12,
            )
        ], expand=True, padding=0)

        self.page.controls.append(form)
        self.page.update()

    # ── MATERIAIS ─────────────────────────────────────────────────
    def _ir_materiais(self, sol_id: int, sol_num: str):
        conn = get_conn(self.page)
        existentes = conn.execute(
            "SELECT id, nome, quantidade, tipo FROM materiais WHERE solicitacao_id=? ORDER BY id",
            (sol_id,)
        ).fetchall()
        conn.close()

        linhas: list[dict] = []

        col_linhas = ft.Column([], spacing=6, scroll=ft.ScrollMode.AUTO)
        lbl_erro = ft.Text("", color="#ff6666", size=13)

        def _add_linha(nome="", qtd="", tipo=""):
            e_nome = ft.TextField(value=nome, hint_text="Material",
                                  bgcolor=BG2, color=TEXT, border_color=BORDER,
                                  focused_border_color=ACCENT, border_radius=6,
                                  content_padding=ft.padding.symmetric(horizontal=8, vertical=8),
                                  text_size=13, expand=True)
            e_qtd  = ft.TextField(value=qtd, hint_text="Qtd",
                                  bgcolor=BG2, color=TEXT, border_color=BORDER,
                                  focused_border_color=ACCENT, border_radius=6,
                                  content_padding=ft.padding.symmetric(horizontal=8, vertical=8),
                                  text_size=13, width=80)
            e_tipo = ft.TextField(value=tipo, hint_text="Un/Tipo",
                                  bgcolor=BG2, color=TEXT, border_color=BORDER,
                                  focused_border_color=ACCENT, border_radius=6,
                                  content_padding=ft.padding.symmetric(horizontal=8, vertical=8),
                                  text_size=13, width=90)
            d = {"nome": e_nome, "qtd": e_qtd, "tipo": e_tipo}
            linhas.append(d)

            def rm(ev, _d=d):
                linhas.remove(_d)
                row_ctrl.visible = False
                self.page.update()

            row_ctrl = ft.Row([e_nome, e_qtd, e_tipo,
                               ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED_400,
                                             icon_size=20, on_click=rm)],
                              spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            col_linhas.controls.append(row_ctrl)
            self.page.update()

        for r in existentes:
            _add_linha(r["nome"], r["quantidade"] or "", r["tipo"] or "")
        if not existentes:
            _add_linha()

        def _salvar_mat(e):
            itens = []
            erros = []
            for i, l in enumerate(linhas):
                n = (l["nome"].value or "").strip()
                q = (l["qtd"].value or "").strip()
                t = (l["tipo"].value or "").strip()
                if not n: continue
                if not q:
                    erros.append(f"Linha {i+1}: '{n}' sem quantidade.")
                else:
                    itens.append((n, q, t))
            if erros:
                lbl_erro.value = "\n".join(erros)
                self.page.update(); return
            try:
                conn = get_conn(self.page)
                conn.execute("DELETE FROM materiais WHERE solicitacao_id=?", (sol_id,))
                for n, q, t in itens:
                    conn.execute(
                        "INSERT INTO materiais (solicitacao_id, nome, quantidade, tipo) VALUES (?,?,?,?)",
                        (sol_id, n, q, t)
                    )
                conn.commit(); conn.close()
                self._snack(f"✅  {len(itens)} material(is) salvo(s)!")
                self._ir_formulario("editar", sol_id)
            except Exception as ex:
                lbl_erro.value = f"❌  {ex}"; self.page.update()

        self.page.controls.clear()
        self.page.appbar = ft.AppBar(
            title=ft.Text(f"Materiais — {sol_num}", color=TEXT, size=14),
            bgcolor=CARD,
            leading=ft.IconButton(ft.Icons.ARROW_BACK, icon_color=TEXT,
                                  on_click=lambda e: self._ir_formulario("editar", sol_id)),
            actions=[
                ft.IconButton(ft.Icons.ADD, icon_color=ft.Colors.GREEN_400,
                              on_click=lambda e: _add_linha()),
                ft.IconButton(ft.Icons.SAVE, icon_color=ACCENT, on_click=_salvar_mat),
            ],
        )
        self.page.controls.append(ft.ListView([
            ft.Container(
                ft.Column([
                    ft.Text("Materiais utilizados na solicitação", size=12, color=TEXT3),
                    ft.Container(height=4),
                    col_linhas,
                    lbl_erro,
                    ft.Container(height=8),
                    btn("💾  Salvar Materiais", on_click=_salvar_mat, expand=True,
                        bgcolor={"": SUCCESS, ft.ControlState.HOVERED: "#24934f"}),
                    ft.Container(height=20),
                ], spacing=8),
                padding=14,
            )
        ], expand=True, padding=0))
        self.page.update()

    # ── DIALOG SYNC ───────────────────────────────────────────────
    def _dialog_sync(self):
        db_path = get_db_path(self.page)
        dlg = ft.AlertDialog(
            title=ft.Text("📂  Sincronização com o PC", color=ACCENT),
            bgcolor=CARD,
            content=ft.Column([
                ft.Text("O banco de dados do tablet está em:", color=TEXT2, size=13),
                ft.Container(
                    ft.Text(db_path, color=ACCENT, size=11, selectable=True),
                    bgcolor=BG2, border_radius=6, padding=10,
                    border=ft.border.all(1, BORDER),
                ),
                ft.Container(height=8),
                ft.Text("Para sincronizar com o PC:", color=TEXT2, size=13,
                        weight=ft.FontWeight.W_600),
                ft.Text("1. Conecte o tablet ao PC via cabo USB\n"
                        "2. Copie o arquivo reparos.db para o PC\n"
                        "3. O PC usa SOLICITACOES.db — os schemas são compatíveis\n"
                        "4. Para importar dados do PC para o tablet, copie "
                        "o .db do PC para o caminho acima e reinicie o app",
                        color=TEXT2, size=12),
            ], tight=True, width=320),
            actions=[ft.TextButton("Fechar",
                on_click=lambda e: (setattr(dlg,"open",False), self.page.update()))],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _dialog_sobre(self):
        dlg = ft.AlertDialog(
            title=ft.Text("Sobre o App", color=ACCENT),
            bgcolor=CARD,
            content=ft.Column([
                ft.Text("Sistema de Gerenciamento dos Reparos", color=TEXT,
                        weight=ft.FontWeight.BOLD, size=14),
                ft.Text("Versão Mobile — Flet", color=TEXT2, size=12),
                ft.Text("Desenvolvido por Valdemir Vieira Alves", color=TEXT2, size=12),
                ft.Text("(21) 99431-3049", color=ACCENT, size=12),
                ft.Container(height=8),
                ft.Text("Banco de dados local (SQLite)", color=TEXT3, size=11),
                ft.Text(f"Arquivo: {get_db_path(self.page)}", color=TEXT3, size=10, selectable=True),
            ], tight=True, spacing=6),
            actions=[ft.TextButton("OK",
                on_click=lambda e: (setattr(dlg,"open",False), self.page.update()))],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()


def main(page: ft.Page):
    App(page)

ft.app(target=main)
