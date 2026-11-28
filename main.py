"""FrutiDesafío - Caso 3 (PyQt5). Ejecutar en Spyder con F5.
Carpeta: main.py | ui/*.ui | datos/ | recursos/ (música: cualquier .mp3/.wav) | recursos/frutas/ (imágenes PNG opcionales)"""
import sys, os, json, random
from datetime import date, datetime, timedelta
from PyQt5 import QtWidgets as W, QtCore as C, QtGui as G, uic
try:
    from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QSoundEffect
except ImportError:
    QMediaPlayer = QSoundEffect = None

# BASE: donde están ui/ y recursos/ (dentro del .exe de PyInstaller es la carpeta temporal _MEIPASS)
BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
# Datos del usuario: instalado (.exe) -> %APPDATA%\MemoriceFrutas (Program Files no permite escribir); en desarrollo -> ./datos
if getattr(sys, "frozen", False):
    _DATOS = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "MemoriceFrutas")
else:
    _DATOS = os.path.join(BASE, "datos")
RUTA = os.path.join(_DATOS, "datos.json")
FRUTAS = [("🍎","MANZANA","la"),("🍌","PLÁTANO","el"),("🍇","UVAS","las"),("🍓","FRUTILLA","la"),("🍊","NARANJA","la"),
          ("🍉","SANDÍA","la"),("🍐","PERA","la"),("🍒","CEREZAS","las"),("🍑","DURAZNO","el"),("🍍","PIÑA","la"),
          ("🍋","LIMÓN","el"),("🥝","KIWI","el"),("🥭","MANGO","el"),("🍈","MELÓN","el"),("🥑","PALTA","la"),("🥥","COCO","el")]  # (emoji, nombre, artículo)
CASI = ["Casi... ¡hasta las mejores manzanas se caen del árbol! 🍎", "¡Uy, casi! Esa fruta se escondió bien 🙈 ¡Tú puedes!",
        "Ni la sandía sale perfecta a la primera 🍉 ¡Otra vez!", "¡Casi! Hasta las uvas tardan en madurar 🍇 ¡Sigue!"]
BIEN = ["¡Muy bien! 🎉", "¡Pareja encontrada! Más unidos que un racimo de uvas 🍇", "¡Qué jugada tan dulce! 🍓", "¡Más fresco que una naranja recién exprimida! 🍊"]
FINAL = ["Tu memoria está más madura que un mango 🥭", "¡Hoy tu FrutiDesafío quedó en jugo! 🍹", "¡Eres la fruta más dulce del frutero! 🍓",
         "Eso estuvo más dulce que una sandía en verano 🍉", "¡Un día más cuidando tu mente! 😊"]
AVISOS = ["Tu nivel del día ya está maduro 🍎", "¡Las frutas te esperan! No las dejes pasar de maduras 🍌", "Tu cerebro pidió una ensalada... de frutas mentales 🥗"]
MODOS = {"memoria": "🃏 Memoria", "asociacion": "🍎 Asociación fruta-palabra", "atencion": "🔍 Atención"}
TAM = [(2,2),(2,3),(3,4),(3,4),(4,4),(4,4),(4,5),(4,5),(4,6),(4,6),(5,6),(5,6)]   # memoria: (filas, columnas)
# asociación: (pares, disposición, dibujos de más sin palabra). "col" = palabras a la izquierda y dibujos a la derecha; "mezcla" = todo revuelto
ASOC = [(2,"col",0),(3,"col",0),(4,"col",0),(4,"col",0),(5,"mezcla",0),(5,"mezcla",0),(6,"mezcla",0),(6,"mezcla",0),
        (6,"mezcla",2),(7,"mezcla",2),(8,"mezcla",2),(8,"mezcla",3)]
ATENCION = [(2,2,3,"especifica"),(2,3,3,"distinta"),(3,3,4,"especifica"),(3,3,4,"distinta"),(3,4,5,"especifica"),(3,4,5,"distinta"),
            (4,4,5,"distinta"),(4,4,6,"especifica"),(4,5,6,"distinta"),(4,5,7,"especifica"),(5,6,7,"distinta"),(5,6,8,"distinta")]  # (filas, cols, rondas, tipo)
NIV = 12
PERFILES = {"participante": "Jugador", "profesional": "Administrador"}   # nombres que ve la persona
TUTO = {"memoria": ("🍎 ❓ ❓ 🍎", "Toca una carta para darla vuelta y luego toca otra. Si son iguales, se quedan a la vista. "
                    "Encuentra todas las parejas. Si te equivocas no pasa nada: se tapan de nuevo. Puedes usar 💡 Ayuda o ⏸ Pausa cuando quieras."),
        "asociacion": ("🍓 ↔ FRUTILLA", "Verás palabras y dibujos de frutas, todos a la vista. Toca una palabra y luego el dibujo que le corresponde. "
                       "Si coinciden, quedan en verde. Ojo: a veces sobran dibujos sin palabra. Sin apuro: puedes usar 💡 Ayuda o ⏸ Pausa."),
        "atencion": ("👀 🍎 🍎 🍋 🍎", "Mira bien todas las frutas. Te pediremos tocar una fruta específica, o encontrar la que es diferente a las demás. "
                     "Si tocas otra, esa se apaga y puedes intentar de nuevo. Puedes usar 💡 Ayuda.")}

def hoy(): return date.today().isoformat()
def ayer(): return (date.today() - timedelta(days=1)).isoformat()

def imagen(nombre):
    f = os.path.join(BASE, "recursos", "frutas", nombre.lower().translate(str.maketrans("áéíóúñ", "aeioun")) + ".png")
    return f if os.path.exists(f) else None

def asegurar(u):
    u.setdefault("progreso", {})
    for m in MODOS: u["progreso"].setdefault(m, {"max": 0, "fecha": None})
    for k, v in (("tutorial", []), ("fuente", 18), ("ayuda", True), ("desbloqueo_prof", 1), ("sesiones", []), ("racha", 0), ("ultimo_juego", None)):
        u.setdefault(k, v)
    return u

def cargar():
    try:
        with open(RUTA, encoding="utf-8") as f: d = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): d = {"usuarios": {}}
    for u in d["usuarios"].values(): asegurar(u)
    return d

def guardar(d):
    try:
        os.makedirs(os.path.dirname(RUTA), exist_ok=True)
        with open(RUTA, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=1)
        return True
    except OSError: return False

def nuevo_usuario(perfil): return asegurar({"perfil": perfil})

def disponibles(u, modo):  # un nivel nuevo por día; el profesional puede desbloquear más; los superados se repiten
    p = u["progreso"][modo]; n = p["max"] + (0 if p["fecha"] == hoy() else 1)
    return max(1, min(NIV, max(n, u["desbloqueo_prof"])))

def racha_vigente(u): return u["racha"] if u["ultimo_juego"] in (hoy(), ayer()) else 0   # si dejó de jugar, la racha vale 0

def actualizar_racha(u):
    if u["ultimo_juego"] == hoy(): return
    u["racha"] = u["racha"] + 1 if u["ultimo_juego"] == ayer() else 1
    u["ultimo_juego"] = hoy()

class Juego:
    def __init__(s, ui, al_terminar, sonar=lambda n: None, al_practica=lambda e: None, al_tranquilo=lambda ok: False):
        s.ui, s.al_terminar, s.sonar, s.al_practica, s.al_tranquilo = ui, al_terminar, sonar, al_practica, al_tranquilo; s.practica = False; s.guiadas = []
        s.grid = ui.frameTablero.layout()
        if s.grid is None: s.grid = W.QGridLayout(ui.frameTablero)
        s.crono = C.QTimer(ui); s.crono.timeout.connect(s.tick)
        ui.btnAyuda.clicked.connect(s.ayuda); ui.btnPausa.clicked.connect(s.pausar)
        ui.btnSalir.clicked.connect(lambda: s.terminar("interrumpida")); s.gen = 0; s.activo = False

    def iniciar(s, nivel, modo, ayuda_ok, fuente, practica=False):
        s.gen += 1; s.nivel, s.modo, s.fz, s.practica = nivel, modo, fuente, practica
        s.m = dict(aciertos=0, errores=0, intentos=0, ayudas=0); s.seg = 0; s.hechas = set(); s.primera = None
        s.bloq = False; s.en_pausa = False; s.activo = True; s.ronda = 0; s.ayuda_ok = ayuda_ok; s.prox_aviso = 120
        s.ui.btnAyuda.setVisible(ayuda_ok); s.ui.frameTablero.setEnabled(True); s.ui.btnPausa.setText("⏸ Pausa"); s.ui.btnSalir.setText("⏭ Saltar tutorial" if practica else "Salir")
        s.ui.lblConsigna.setVisible(modo == "atencion")
        s.sel = None; s.total = 0
        if modo == "atencion": s.f, s.c, s.rondas, s.tipo = ATENCION[nivel - 1]; s.ico = 100 if s.f <= 4 else 70; s.rondas = 2 if practica else s.rondas; s.nueva_ronda()
        elif modo == "asociacion": s.iniciar_asociacion()
        else:
            s.f, s.c = TAM[nivel - 1]; s.ico = 100 if s.f <= 4 else 70; fr = random.sample(FRUTAS, s.f * s.c // 2); cartas = []
            for i, x in enumerate(fr): cartas += [(i, "img", x), (i, "img", x)]
            random.shuffle(cartas); s.total = len(cartas); s.armar(cartas, "oculta"); s.ui.lblMensaje.setText("Toca una carta para empezar. Busca las parejas 🔍")
        s.guia(); s.crono.start(1000); s.tick(False)

    def iniciar_asociacion(s):  # todo a la vista: se toca una palabra y luego su dibujo (sin dar vuelta cartas)
        n, disp, dist = ASOC[s.nivel - 1]; fr = random.sample(FRUTAS, n + dist)
        pal = [(i, "txt", x) for i, x in enumerate(fr[:n])]
        dib = [(i, "img", x) for i, x in enumerate(fr[:n])] + [(100 + i, "img", x) for i, x in enumerate(fr[n:])]   # pid>=100: dibujo sin pareja
        random.shuffle(pal); random.shuffle(dib)
        if disp == "col": s.f, s.c = n, 2; cartas = [c for par in zip(pal, dib) for c in par]
        else:
            cartas = pal + dib; random.shuffle(cartas); s.c = 4 if len(cartas) <= 12 else 5; s.f = -(-len(cartas) // s.c)
        s.total = 2 * n; s.ico = 100 if s.f <= 4 else 70; s.armar(cartas, "visible")
        s.ui.lblMensaje.setText("Toca una palabra y luego su dibujo 🔍")

    def armar(s, cartas, est):
        s.cartas = cartas
        while s.grid.count(): s.grid.takeAt(0).widget().deleteLater()
        s.btns = []
        for k in range(len(cartas)):
            b = W.QPushButton(); b.setSizePolicy(W.QSizePolicy.Expanding, W.QSizePolicy.Expanding)
            b.clicked.connect(lambda _, k=k: s.tocar(k)); s.grid.addWidget(b, k // s.c, k % s.c); s.btns.append(b); s.estilo(k, est)

    def nueva_ronda(s):  # modo atención: pid 1 = carta correcta
        n = s.f * s.c; s.bloq = False
        if s.practica: s.tipo = "especifica" if s.ronda == 0 else "distinta"
        if s.tipo == "especifica":
            objetivo = random.choice(FRUTAS); resto = [x for x in FRUTAS if x != objetivo]
            cartas = [(1, "img", objetivo)] + [(0, "img", random.choice(resto)) for _ in range(n - 1)]
            s.ui.lblConsigna.setText(f"Toca {objetivo[2]} {objetivo[0]} {objetivo[1].lower()}")   # "las uvas", "el plátano"...
        else:
            a, b = random.sample(FRUTAS, 2); cartas = [(1, "img", b)] + [(0, "img", a) for _ in range(n - 1)]
            s.ui.lblConsigna.setText("Encuentra la fruta diferente 👀")
        random.shuffle(cartas); s.armar(cartas, "visible"); s.ui.lblMensaje.setText("Mira con calma 😊"); s.tick(False); s.guia()

    def estilo(s, k, est):
        b = s.btns[k]; _, tipo, fr = s.cartas[k]
        if est in ("oculta", "oculta_guia"): b.setIcon(G.QIcon()); b.setText("❓"); css = "background:#7E57C2;color:white;font-size:40pt;" + ("border:6px solid #FFB300;" if est == "oculta_guia" else ""); tam = 40
        else:
            if tipo == "img":
                ruta = imagen(fr[1]); tam = 40
                if ruta: b.setText(""); b.setIcon(G.QIcon(ruta)); b.setIconSize(C.QSize(s.ico, s.ico))
                else: b.setIcon(G.QIcon()); b.setText(fr[0])
            else: b.setIcon(G.QIcon()); b.setText(fr[1]); tam = s.fz + 2
            css = {"visible": "background:white;color:#311B92;border:4px solid #81D4FA;", "ok": "background:#B3E5FC;color:#01579B;",
                   "dim": "background:#E0E0E0;color:#999;", "sel": "background:#EDE7F6;color:#311B92;border:4px solid #7E57C2;", "guia": "background:#FFF59D;color:#311B92;border:5px solid #FFB300;"}[est] + f"font-size:{tam}pt;font-weight:bold;"
        b.setEnabled(est != "dim"); b.setStyleSheet(css + "border-radius:16px;")

    def tick(s, sumar=True):
        if sumar: s.seg += 1
        prog = f"Ronda {min(s.ronda + 1, s.rondas)}/{s.rondas}" if s.modo == "atencion" else f"Parejas: {len(s.hechas) // 2}/{s.total // 2}"
        s.ui.lblInfo.setText(f"{'🎯 Práctica' if s.practica else 'Nivel ' + str(s.nivel)}   ⏱ {s.seg // 60}:{s.seg % 60:02d}   {prog}")
        if sumar and s.activo and not s.practica and s.seg >= s.prox_aviso:   # lleva rato jugando: mensaje tranquilo (el tiempo del aviso no cuenta)
            s.prox_aviso += 180; s.crono.stop()
            if s.al_tranquilo(s.ayuda_ok): s.ayuda()
            if s.activo and not s.en_pausa: s.crono.start(1000)

    def tocar(s, k):
        if s.en_pausa or s.bloq or k in s.hechas: return
        if s.modo == "atencion": s.tocar_atencion(k)
        elif s.modo == "asociacion": s.tocar_asociacion(k)
        else: s.tocar_memoria(k)
        if s.practica and s.activo and not s.bloq: s.guia()

    def tocar_asociacion(s, k):
        if s.sel is None: s.sel = k; s.estilo(k, "sel"); return
        if k == s.sel: s.estilo(k, "visible"); s.sel = None; return             # tocarla otra vez = quitar la selección
        a, b = s.sel, k
        if s.cartas[a][1] == s.cartas[b][1]: s.estilo(a, "visible"); s.sel = k; s.estilo(k, "sel"); return   # dos palabras o dos dibujos: solo cambia la selección
        s.sel = None; s.m["intentos"] += 1
        if s.cartas[a][0] == s.cartas[b][0]:
            s.m["aciertos"] += 1; s.hechas |= {a, b}; s.estilo(a, "ok"); s.estilo(b, "ok"); s.ui.lblMensaje.setText(random.choice(BIEN)); s.tick(False)
            if len(s.hechas) == s.total: s.terminar("completada")
        else: s.m["errores"] += 1; s.estilo(a, "visible"); s.ui.lblMensaje.setText(random.choice(CASI))

    def tocar_atencion(s, k):
        s.m["intentos"] += 1
        if s.cartas[k][0] == 1:
            s.m["aciertos"] += 1; s.ronda += 1; s.estilo(k, "ok"); s.ui.lblMensaje.setText(random.choice(BIEN)); s.tick(False)
            if s.ronda >= s.rondas: s.terminar("completada")
            else: s.bloq = True; C.QTimer.singleShot(900, lambda g=s.gen: s.nueva_ronda() if g == s.gen else None)
        else:
            s.m["errores"] += 1; s.estilo(k, "dim"); s.hechas.add(k); s.ui.lblMensaje.setText(random.choice(CASI))

    def tocar_memoria(s, k):
        if k == s.primera: return
        s.estilo(k, "visible")
        if s.primera is None: s.primera = k; return
        a, b = s.primera, k; s.primera = None; s.m["intentos"] += 1
        if s.cartas[a][0] == s.cartas[b][0]:
            s.m["aciertos"] += 1; s.hechas |= {a, b}; s.estilo(a, "ok"); s.estilo(b, "ok"); s.ui.lblMensaje.setText(random.choice(BIEN)); s.tick(False)
            if len(s.hechas) == len(s.cartas): s.terminar("completada")
        else:
            s.m["errores"] += 1; s.bloq = True; s.ui.lblMensaje.setText(random.choice(CASI))
            C.QTimer.singleShot(1000, lambda g=s.gen: s.restaurar(g, [a, b], "oculta"))

    def restaurar(s, g, ks, est):
        if g != s.gen: return
        for k in ks: s.estilo(k, est)
        s.bloq = False; s.guia()

    def guia(s):  # modo práctica: mensajes paso a paso y carta resaltada en amarillo
        s.guiadas = []
        if not s.practica or not s.activo: return
        base = "oculta" if s.modo == "memoria" else "visible"
        for k in range(len(s.cartas)):
            if k not in s.hechas and k != s.primera and k != s.sel: s.estilo(k, base)
        ks = []
        if s.modo == "atencion":
            if s.ronda == 0: ks = [k for k, c in enumerate(s.cartas) if c[0] == 1]; msg = "👆 Lee la consigna de arriba y toca la fruta que brilla"
            else: msg = "¡Muy bien! Ahora tú: encuentra la fruta diferente 👀"
        elif s.m["aciertos"] >= 1: msg = "¡Muy bien! 🎉 Ahora inténtalo tú: busca la otra pareja 🔍"
        else:
            ref = s.primera if s.modo == "memoria" else s.sel
            if ref is None:
                ks = [next(k for k, c in enumerate(s.cartas) if k not in s.hechas and (s.modo == "memoria" or c[1] == "txt"))]
                msg = "👆 Toca la carta que brilla" + (" para darla vuelta" if s.modo == "memoria" else " (es una palabra)")
            else: ks = [k for k, c in enumerate(s.cartas) if c[0] == s.cartas[ref][0] and k != ref]; msg = "¡Bien! 👏 Ahora toca la que brilla: ¡es su pareja!"
        for k in ks: s.estilo(k, "oculta_guia" if s.modo == "memoria" else "guia")
        s.guiadas = ks; s.ui.lblMensaje.setText(msg)

    def ayuda(s):  # NO penaliza: solo se registra
        if not s.ayuda_ok or s.en_pausa or s.bloq or s.primera is not None or s.sel is not None: return
        if s.modo == "atencion": ks, vuelta = [k for k, c in enumerate(s.cartas) if c[0] == 1], "visible"
        else:
            pend = [k for k in range(len(s.cartas)) if k not in s.hechas and s.cartas[k][0] < 100]; pid = s.cartas[random.choice(pend)][0]
            ks, vuelta = [k for k in pend if s.cartas[k][0] == pid], ("oculta" if s.modo == "memoria" else "visible")
        for k in ks: s.estilo(k, "visible" if s.modo == "memoria" else "ok")
        s.bloq = True; s.m["ayudas"] += 1; s.ui.lblMensaje.setText("Mira bien estas 👀")
        C.QTimer.singleShot(1500, lambda g=s.gen: s.restaurar(g, ks, vuelta))

    def pausar(s):
        s.en_pausa = not s.en_pausa; s.ui.frameTablero.setEnabled(not s.en_pausa)
        s.ui.btnPausa.setText("▶ Continuar" if s.en_pausa else "⏸ Pausa")
        s.crono.stop() if s.en_pausa else s.crono.start(1000)
        s.ui.lblMensaje.setText("En pausa. Tómate el tiempo que necesites 😌" if s.en_pausa else "¡Sigamos!")

    def terminar(s, estado):
        if not s.activo: return
        s.activo = False; s.crono.stop(); s.gen += 1
        if s.practica: s.al_practica(estado); return   # la práctica no se guarda ni cuenta para la racha
        s.al_terminar(dict(modo=s.modo, nivel=s.nivel, estado=estado, tiempo_s=s.seg, fecha=hoy(), hora=datetime.now().strftime("%H:%M"), **s.m))

class App(W.QMainWindow):
    def __init__(s):
        super().__init__(); s.setWindowTitle("FrutiDesafío 🍓")
        s.datos = cargar(); s.sembrar(); s.sembrar_ranking(); s.conf = s.datos.setdefault("config", {"fuente": 18, "musica": True}); s.user = None; s.modo = None; s.repasar = False; s.cargando = False
        s.pila = W.QStackedWidget(); cen = W.QWidget(); v = W.QVBoxLayout(cen); s.setCentralWidget(cen)
        cen.setStyleSheet("QWidget{background:#E1F5FE;color:#311B92;}QPushButton{background:#7E57C2;color:white;border-radius:12px;padding:6px 14px;font-weight:bold;}")
        barra = W.QHBoxLayout(); barra.addStretch(1); barra.addWidget(W.QLabel("Letra:"))   # barra fija: visible en todas las pantallas
        s.bMenos, s.bMas, s.bMusica = (W.QPushButton(t) for t in ("A−", "A+", "🔊 Música"))
        for b in (s.bMenos, s.bMas, s.bMusica): b.setMinimumHeight(44); barra.addWidget(b)
        v.addLayout(barra); v.addWidget(s.pila, 1)
        L = lambda n: uic.loadUi(os.path.join(BASE, "ui", n + ".ui"))
        s.login, s.mod, s.niv, s.tut, s.jug, s.panel, s.rank = (L(n) for n in ("login", "modo", "niveles", "tutorial", "juego", "panel", "ranking"))
        for p in (s.login, s.mod, s.niv, s.tut, s.jug, s.panel, s.rank): s.pila.addWidget(p)
        s.juego = Juego(s.jug, s.fin_juego, s.sonido, s.fin_practica, s.tranquilo)
        bp = getattr(s.tut, "btnPracticar", None)   # si no existe en tutorial.ui, se crea aquí
        if bp is None: bp = W.QPushButton("🎯 Practicar un ratito (recomendado)"); lay = s.tut.layout(); lay.insertWidget(lay.indexOf(s.tut.btnEmpezar), bp)
        bp.clicked.connect(s.practicar)
        s.login.lblTitulo.setText("🍓 FrutiDesafío")
        s.login.cmbPerfil.setItemText(0, "🎮 Jugador"); s.login.cmbPerfil.setItemText(1, "🛠 Administrador")   # nombres claros (el .ui puede decir otra cosa)
        if hasattr(s.panel, "lblP"): s.panel.lblP.setText("Jugador:")
        t = s.rank.tablaRanking; t.setColumnCount(5); t.setEditTriggers(W.QAbstractItemView.NoEditTriggers); t.horizontalHeader().setStretchLastSection(True)
        t.setHorizontalHeaderLabels(["Puesto", "Jugador", "Racha (días)", "Aciertos totales", "Niveles completados"])
        s.rank.btnPorRacha.clicked.connect(lambda: s.mostrar_ranking("racha")); s.rank.btnPorAciertos.clicked.connect(lambda: s.mostrar_ranking("aciertos"))
        s.rank.btnVolverRank.clicked.connect(s.mostrar_modo)
        br = getattr(s.mod, "btnRanking", None) or W.QPushButton()   # si no existe en modo.ui, se crea aquí
        br.setText("🏆 Ver ranking completo"); br.clicked.connect(lambda: s.mostrar_ranking("racha"))
        if s.mod.findChild(W.QFrame, "panelJuegos") is None: s.dividir_modo(br)   # modo.ui antiguo: se divide por código
        else:   # modo.ui nuevo: los dos paneles ya vienen hechos en Qt Designer
            t = s.miniRank = s.mod.tablaMiniRanking; t.setColumnCount(3); t.setHorizontalHeaderLabels(["Puesto", "Jugador", "Racha"]); t.verticalHeader().setVisible(False)
            t.setEditTriggers(W.QAbstractItemView.NoEditTriggers); t.setSelectionMode(W.QAbstractItemView.NoSelection); t.horizontalHeader().setStretchLastSection(True)
        s.login.btnEntrar.clicked.connect(s.entrar); s.login.txtUsuario.returnPressed.connect(s.entrar)
        for m, b in (("memoria", s.mod.btnMemoria), ("asociacion", s.mod.btnAsociacion), ("atencion", s.mod.btnAtencion)):
            b.clicked.connect(lambda _, m=m: s.elegir_modo(m))
        s.bMenos.clicked.connect(lambda: s.cambiar_fuente(-2)); s.bMas.clicked.connect(lambda: s.cambiar_fuente(2))
        s.mod.btnCambiar.clicked.connect(lambda: s.ir(s.login)); s.niv.btnVolverModo.clicked.connect(s.mostrar_modo)
        s.niv.btnComoJugar.clicked.connect(lambda: s.mostrar_tutorial(False)); s.niv.btnComoJugar.setText("📖 Ver tutorial de nuevo")
        s.tut.btnVolverTut.clicked.connect(s.mostrar_modo); s.tut.btnEmpezar.clicked.connect(s.empezar_desde_tutorial)
        s.musica(); s.bMusica.setVisible(s.player is not None); s.bMusica.clicked.connect(s.alternar_musica); s.aplicar_musica()
        t = s.panel.tablaSesiones; t.setColumnCount(9)
        t.setHorizontalHeaderLabels(["Fecha", "Hora", "Modo", "Nivel", "Estado", "Aciertos", "Errores", "Ayudas", "Tiempo (s)"])
        s.panel.spinNivel.setRange(1, NIV); s.panel.cmbParticipante.currentTextChanged.connect(s.ver_participante)
        s.panel.chkAyuda.toggled.connect(s.cfg); s.panel.spinNivel.valueChanged.connect(s.cfg); s.panel.btnSalirPanel.clicked.connect(lambda: s.ir(s.login))
        s.tray = W.QSystemTrayIcon(s.style().standardIcon(W.QStyle.SP_MessageBoxInformation), s); s.resize(950, 780); s.aplicar_fuente()

    def closeEvent(s, e):  # al cerrar la ventana, la música debe detenerse (en Spyder la consola sigue viva)
        if s.player: s.player.stop()
        s.juego.crono.stop(); e.accept()

    def ir(s, p): s.pila.setCurrentWidget(p)

    def sembrar(s):  # datos ficticios de demostración
        if "Demo" in s.datos["usuarios"]: return
        u = nuevo_usuario("participante"); u.update(ultimo_juego=ayer(), racha=2); u["progreso"]["memoria"] = {"max": 2, "fecha": ayer()}
        u["sesiones"] = [dict(modo="memoria", nivel=1, estado="completada", tiempo_s=38, fecha=ayer(), hora="10:05", aciertos=2, errores=1, intentos=3, ayudas=0),
                         dict(modo="memoria", nivel=2, estado="completada", tiempo_s=71, fecha=ayer(), hora="10:20", aciertos=3, errores=4, intentos=7, ayudas=1)]
        s.datos["usuarios"]["Demo"] = u; s.datos["usuarios"]["Profesional"] = nuevo_usuario("profesional"); guardar(s.datos)

    def dividir_modo(s, br):  # pantalla dividida: juegos a la izquierda; racha y ranking a la derecha
        m = s.mod; lay = m.layout()
        for w in (m.lblSaludo, m.lblRacha, m.lblPregunta, m.btnMemoria, m.btnAsociacion, m.btnAtencion, m.btnCambiar, br): lay.removeWidget(w)
        def panel(nombre, titulo):
            f = W.QFrame(); f.setObjectName(nombre)
            f.setStyleSheet("QFrame#" + nombre + "{background:rgba(255,255,255,0.65);border:2px solid #81D4FA;border-radius:18px;}")
            v = W.QVBoxLayout(f); t = W.QLabel(titulo); t.setAlignment(C.Qt.AlignCenter)
            t.setStyleSheet("font-size:20pt;font-weight:bold;background:transparent;border:none;"); v.addWidget(t); return f, v
        izq, vi = panel("panelJuegos", "🎮 Juegos"); der, vd = panel("panelRachas", "🏆 Rachas")
        for w in (m.lblSaludo, m.lblPregunta, m.lblRacha): w.setAlignment(C.Qt.AlignCenter); w.setWordWrap(True)
        for w in (m.lblPregunta, m.btnMemoria, m.btnAsociacion, m.btnAtencion): vi.addWidget(w)
        vi.addStretch(1)
        t = s.miniRank = W.QTableWidget(0, 3); t.setHorizontalHeaderLabels(["Puesto", "Jugador", "Racha"]); t.verticalHeader().setVisible(False)
        t.setEditTriggers(W.QAbstractItemView.NoEditTriggers); t.setSelectionMode(W.QAbstractItemView.NoSelection); t.horizontalHeader().setStretchLastSection(True)
        for w in (m.lblRacha, t, br): vd.addWidget(w)
        cols = W.QHBoxLayout(); cols.addWidget(izq, 3); cols.addWidget(der, 2)
        lay.addWidget(m.lblSaludo); lay.addLayout(cols, 1); lay.addWidget(m.btnCambiar)

    def llenar_mini(s):  # panel de rachas de la pantalla principal (los 5 primeros)
        t = s.miniRank; t.setRowCount(0)
        for i, f in enumerate(s.ranking_filas("racha")[:5]):
            t.insertRow(i)
            for j, v in enumerate([["🥇", "🥈", "🥉"][i] if i < 3 else str(i + 1), f[0] + (" (tú)" if f[0] == s.user else ""), f"🔥 {f[1]}"]): t.setItem(i, j, W.QTableWidgetItem(v))

    def sembrar_ranking(s):  # jugadores FICTICIOS solo para mostrar el ranking en la demo (se pueden borrar de datos.json)
        for nom, racha, aciertos in (("Ana", 5, 40), ("Luis", 2, 55), ("Marta", 8, 31)):
            if nom in s.datos["usuarios"]: continue
            u = nuevo_usuario("participante"); u.update(ultimo_juego=hoy(), racha=racha)
            u["sesiones"] = [dict(modo="memoria", nivel=1, estado="completada", tiempo_s=60, fecha=ayer(), hora="09:00", aciertos=aciertos, errores=2, intentos=aciertos + 2, ayudas=0)]
            s.datos["usuarios"][nom] = u
        guardar(s.datos)

    def ranking_filas(s, criterio):  # premia constancia y esfuerzo, no rapidez
        filas = []
        for n, u in s.datos["usuarios"].items():
            if u["perfil"] != "participante": continue
            filas.append((n, racha_vigente(u), sum(x.get("aciertos", 0) for x in u["sesiones"]), sum(1 for x in u["sesiones"] if x["estado"] == "completada")))
        filas.sort(key=(lambda f: (-f[1], -f[2], f[0])) if criterio == "racha" else (lambda f: (-f[2], -f[1], f[0])))
        return filas

    def mostrar_ranking(s, criterio="racha"):
        t = s.rank.tablaRanking; t.setRowCount(0)
        for i, f in enumerate(s.ranking_filas(criterio)):
            t.insertRow(i)
            vals = [["🥇", "🥈", "🥉"][i] if i < 3 else str(i + 1), f[0] + (" (tú)" if f[0] == s.user else ""), f"🔥 {f[1]}", f"⭐ {f[2]}", str(f[3])]
            for j, v in enumerate(vals): t.setItem(i, j, W.QTableWidgetItem(v))
        s.ir(s.rank)

    def preguntar(s, titulo, texto, si_txt="Sí, otro nivel", no_txt="No, por hoy"):
        m = W.QMessageBox(s); m.setWindowTitle(titulo); m.setText(texto)
        si = m.addButton(si_txt, W.QMessageBox.YesRole); m.addButton(no_txt, W.QMessageBox.NoRole)
        m.exec_(); return m.clickedButton() is si

    def musica(s):
        s.player = None; d = os.path.join(BASE, "recursos")
        a = [f for f in os.listdir(d) if f.lower().endswith((".mp3", ".wav", ".ogg"))] if os.path.isdir(d) else []
        if QMediaPlayer and a:
            s.player = QMediaPlayer(); s.player.setVolume(30); s.player.setMedia(QMediaContent(C.QUrl.fromLocalFile(os.path.join(d, a[0]))))
            s.player.mediaStatusChanged.connect(lambda st: s.player.play() if st == QMediaPlayer.EndOfMedia else None); s.player.play()

    def guardar_o_avisar(s):
        if not guardar(s.datos): s.sonido("error.wav"); W.QMessageBox.warning(s, "Aviso", "No se pudo guardar tu progreso. Avisa al profesional.")

    def sonido(s, nombre):  # efecto corto desde recursos/sonidos/; si falta el archivo, pitido del sistema
        if not s.conf["musica"]: return
        ruta = os.path.join(BASE, "recursos", "sonidos", nombre)
        if QSoundEffect and os.path.exists(ruta):
            if not hasattr(s, "_efectos"): s._efectos = {}
            e = s._efectos.get(nombre)
            if e is None: e = s._efectos[nombre] = QSoundEffect(s); e.setSource(C.QUrl.fromLocalFile(ruta)); e.setVolume(0.8)
            e.play()
        else: W.QApplication.beep()

    def error_login(s, texto): s.login.lblError.setText(texto); s.sonido("error.wav")

    def aviso(s, titulo, texto, sonido):  # ventana emergente con sonido
        s.sonido(sonido); W.QMessageBox.information(s, titulo, texto)

    def U(s): return s.datos["usuarios"][s.user]

    def aplicar_fuente(s): W.QApplication.instance().setStyleSheet(f"QWidget{{font-size:{s.conf['fuente']}pt;}}")

    def cambiar_fuente(s, d):
        s.conf["fuente"] = max(12, min(32, s.conf["fuente"] + d)); s.aplicar_fuente(); s.guardar_o_avisar()

    def alternar_musica(s): s.conf["musica"] = not s.conf["musica"]; s.aplicar_musica(); s.guardar_o_avisar()

    def aplicar_musica(s):
        if s.player: s.player.setMuted(not s.conf["musica"])
        s.bMusica.setText("🔊 Música" if s.conf["musica"] else "🔇 Música")

    def entrar(s):
        nom = s.login.txtUsuario.text().strip(); perfil = "participante" if s.login.cmbPerfil.currentIndex() == 0 else "profesional"; us = s.datos["usuarios"]
        if not nom or len(nom) > 20: s.error_login("Escribe un nombre de 1 a 20 letras"); return
        if nom in us and us[nom]["perfil"] != perfil: s.error_login(f"'{nom}' está registrado como {PERFILES[us[nom]['perfil']]}"); return
        if nom not in us: us[nom] = nuevo_usuario(perfil); s.guardar_o_avisar()
        s.user = nom; s.login.lblError.setText(""); s.aplicar_fuente()
        if perfil == "profesional": s.mostrar_panel(); return
        s.mostrar_modo()
        if us[nom]["ultimo_juego"] != hoy() and s.tray.isSystemTrayAvailable():
            s.tray.show(); s.tray.showMessage("¡Hora de tu FrutiDesafío del día! 🍓", random.choice(AVISOS))

    def mostrar_modo(s):
        u = s.U()
        if not u["ultimo_juego"]: r = "¡Empieza tu racha frutal hoy! 🌱"
        elif u["ultimo_juego"] in (hoy(), ayer()): r = f"🔥 ¡{u['racha']} día(s) seguidos! Tu racha está madurando 🍑"
        else: r = "¡Qué bueno verte de vuelta! El FrutiDesafío te extrañaba 🍎"
        s.mod.lblSaludo.setText(f"¡Hola, {s.user}! 👋\n¡Hora de tu FrutiDesafío del día! 🍓"); s.mod.lblRacha.setText(r); s.llenar_mini(); s.ir(s.mod)

    def elegir_modo(s, m):
        s.modo = m; s.repasar = False
        if m in s.U()["tutorial"]: s.mostrar_niveles(); return
        if s.preguntar("¡Bienvenido/a! 😊", "Antes de jugar, practiquemos un ratito.\nTe iremos guiando paso a paso.", "🎯 Practicar", "⏭ Saltar tutorial"): s.practicar()
        else: s.fin_practica("saltada")   # primera vez: la práctica se ofrece sola, pero se puede saltar

    def mostrar_tutorial(s, primera):
        ej, txt = TUTO[s.modo]; s.tut.lblTituloTut.setText("Cómo se juega: " + MODOS[s.modo]); s.tut.lblEjemplo.setText(ej); s.tut.lblTexto.setText(txt)
        s.tut.btnEmpezar.setText("¡Entendido, a jugar!" if primera else "Seguir"); s.ir(s.tut)

    def tranquilo(s, ayuda_ok):
        t, x = "¡Tranquilo/a, vas bien! 😊", "Tómate el tiempo que necesites, no hay apuro."
        if not ayuda_ok: W.QMessageBox.information(s, t, x); return False
        return s.preguntar(t, x + "\n¿Necesitas ayuda? Te muestro una pista.", "💡 Sí, una pista", "No, sigo yo")

    def practicar(s): s.juego.iniciar(1, s.modo, True, s.conf["fuente"], True); s.ir(s.jug)

    def fin_practica(s, estado):
        u = s.U()
        if s.modo not in u["tutorial"]: u["tutorial"].append(s.modo); s.guardar_o_avisar()   # completada o saltada: ya no se ofrece sola
        if estado != "completada": s.mostrar_niveles(); return
        s.aviso("¡Práctica lista! 🎉", "¡Muy bien! Ya sabes cómo se juega.\nAhora elige tu nivel.", "aviso.wav"); s.mostrar_niveles()

    def empezar_desde_tutorial(s):
        u = s.U()
        if s.modo not in u["tutorial"]: u["tutorial"].append(s.modo); s.guardar_o_avisar()
        s.mostrar_niveles()

    def mostrar_niveles(s):  # solo se ofrecen los niveles nuevos; los completados quedan resumidos (se pueden repasar)
        u = s.U(); p = u["progreso"][s.modo]; s.niv.lblModo.setText(MODOS[s.modo]); lay = s.niv.frameNiveles.layout()
        while lay.count(): lay.takeAt(0).widget().deleteLater()
        disp = disponibles(u, s.modo); hechos = p["max"]; hay_nuevo = disp > hechos
        if hay_nuevo: info = f"⭐ Tu nivel de hoy: {hechos + 1}" if disp == hechos + 1 else f"⭐ Niveles disponibles: del {hechos + 1} al {disp}"
        elif hechos >= NIV: info = "🏆 ¡Completaste todos los niveles! Puedes repasarlos cuando quieras"
        else: info = "🎉 ¡Ya cumpliste tu nivel de hoy! Vuelve mañana para el siguiente"
        et = W.QLabel(f"{info}\n✅ {hechos} de {NIV} niveles completados"); et.setAlignment(C.Qt.AlignCenter); et.setWordWrap(True); lay.addWidget(et)
        cont = W.QWidget(); g = W.QGridLayout(cont); lay.addWidget(cont)
        for n, i in enumerate(list(range(hechos + 1, disp + 1)) + (list(range(1, hechos + 1)) if s.repasar else [])):
            b = W.QPushButton(("⭐ Nivel " if i > hechos else "✅ Nivel ") + str(i)); b.clicked.connect(lambda _, i=i: s.jugar(i)); g.addWidget(b, n // 3, n % 3)
        if not hay_nuevo and hechos < NIV:
            bx = W.QPushButton("➕ Quiero desbloquear otro nivel hoy"); bx.clicked.connect(s.desbloquear_otro); lay.addWidget(bx)
        if hechos > 0:
            br = W.QPushButton("🔼 Ocultar niveles anteriores" if s.repasar else "🔁 Repasar niveles anteriores"); br.clicked.connect(s.alternar_repaso); lay.addWidget(br)
        s.ir(s.niv)

    def desbloquear_otro(s): s.U()["progreso"][s.modo]["fecha"] = None; s.guardar_o_avisar(); s.mostrar_niveles()

    def alternar_repaso(s): s.repasar = not s.repasar; s.mostrar_niveles()

    def jugar(s, nivel):
        s.repasar = False; u = s.U(); s.juego.iniciar(nivel, s.modo, u["ayuda"], s.conf["fuente"]); s.ir(s.jug)

    def fin_juego(s, reg):
        u = s.U(); u["sesiones"].append(reg); nuevo = False
        if reg["estado"] == "completada":
            actualizar_racha(u); p = u["progreso"][reg["modo"]]
            if reg["nivel"] == p["max"] + 1: p["max"] = reg["nivel"]; p["fecha"] = hoy(); nuevo = True
        s.guardar_o_avisar()
        if reg["estado"] == "completada":
            msg = "¡Excelente trabajo! 🌟 " + random.choice(FINAL)
            s.aviso("¡Nivel completado!", f"{msg}\n\nTiempo: {reg['tiempo_s']} s · Errores: {reg['errores']}", "ganar.wav")
        else: s.aviso("Sesión guardada", "Tu sesión quedó guardada como interrumpida. ¡Vuelve cuando quieras!", "aviso.wav")
        if nuevo and p["max"] < NIV and s.preguntar("¿Otro nivel hoy?", f"¡Ya cumpliste tu nivel del día! 🎉\n¿Quieres desbloquear el nivel {p['max'] + 1} ahora?"):
            p["fecha"] = None; s.guardar_o_avisar()   # el nivel del día es obligatorio; los extra son opcionales
        s.mostrar_niveles()

    # ---------- Panel profesional ----------
    def mostrar_panel(s):
        s.cargando = True; s.panel.cmbParticipante.clear()
        s.panel.cmbParticipante.addItems([n for n, u in s.datos["usuarios"].items() if u["perfil"] == "participante"]); s.cargando = False
        s.ver_participante(s.panel.cmbParticipante.currentText()); s.ir(s.panel)

    def ver_participante(s, nom):
        if not nom or s.cargando: return
        u = s.datos["usuarios"][nom]; s.cargando = True; s.panel.chkAyuda.setChecked(u["ayuda"]); s.panel.spinNivel.setValue(u["desbloqueo_prof"]); s.cargando = False
        t = s.panel.tablaSesiones; t.setRowCount(0)
        for r in reversed(u["sesiones"]):
            i = t.rowCount(); t.insertRow(i)
            for j, k in enumerate(["fecha", "hora", "modo", "nivel", "estado", "aciertos", "errores", "ayudas", "tiempo_s"]):
                t.setItem(i, j, W.QTableWidgetItem(str(r.get(k, "memoria" if k == "modo" else "-"))))

    def cfg(s):
        nom = s.panel.cmbParticipante.currentText()
        if s.cargando or not nom: return
        u = s.datos["usuarios"][nom]; u["ayuda"] = s.panel.chkAyuda.isChecked(); u["desbloqueo_prof"] = s.panel.spinNivel.value(); s.guardar_o_avisar()

if __name__ == "__main__":
    app = W.QApplication.instance() or W.QApplication(sys.argv)  # evita error al re-ejecutar en Spyder
    if "ventana" in globals():  # re-ejecución en Spyder: cierra la ventana anterior (y su música)
        try: ventana.close()
        except Exception: pass
    app.setFont(G.QFont("Segoe UI", 14)); ventana = App(); ventana.show(); app.aboutToQuit.connect(ventana.close); app.exec_()