"""Memorice de Frutas - Caso 3 (PyQt5). Ejecutar en Spyder con F5.
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
FRUTAS = [("🍎","MANZANA"),("🍌","PLÁTANO"),("🍇","UVAS"),("🍓","FRUTILLA"),("🍊","NARANJA"),
          ("🍉","SANDÍA"),("🍐","PERA"),("🍒","CEREZAS"),("🍑","DURAZNO"),("🍍","PIÑA")]
MODOS = {"memoria": "🃏 Memoria", "asociacion": "🍎 Asociación fruta-palabra", "atencion": "🔍 Atención"}
TAM = [(2,2),(2,3),(3,4),(3,4),(4,4),(4,4),(4,5)]          # memoria y asociación: (filas, columnas)
ATENCION = [(2,2,3,"especifica"),(2,3,3,"distinta"),(3,3,4,"especifica"),(3,3,4,"distinta"),
            (3,4,5,"especifica"),(3,4,5,"distinta"),(4,4,5,"distinta")]  # (filas, cols, rondas, tipo)
NIV = 7
TUTO = {"memoria": ("🍎 ❓ ❓ 🍎", "Toca una carta para darla vuelta y luego toca otra. Si son iguales, se quedan a la vista. "
                    "Encuentra todas las parejas. Si te equivocas no pasa nada: se tapan de nuevo. Puedes usar 💡 Ayuda o ⏸ Pausa cuando quieras."),
        "asociacion": ("🍓 ↔ FRUTILLA", "Cada fruta tiene su nombre. Da vuelta una carta con la fruta y busca la carta con su nombre. "
                       "Si coinciden, ¡hiciste una pareja! Sin apuro: puedes usar 💡 Ayuda o ⏸ Pausa."),
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

def actualizar_racha(u):
    if u["ultimo_juego"] == hoy(): return
    u["racha"] = u["racha"] + 1 if u["ultimo_juego"] == ayer() else 1
    u["ultimo_juego"] = hoy()

class Juego:
    def __init__(s, ui, al_terminar, sonar=lambda n: None):
        s.ui, s.al_terminar, s.sonar = ui, al_terminar, sonar
        s.grid = ui.frameTablero.layout()
        if s.grid is None: s.grid = W.QGridLayout(ui.frameTablero)
        s.crono = C.QTimer(ui); s.crono.timeout.connect(s.tick)
        ui.btnAyuda.clicked.connect(s.ayuda); ui.btnPausa.clicked.connect(s.pausar)
        ui.btnSalir.clicked.connect(lambda: s.terminar("interrumpida")); s.gen = 0; s.activo = False

    def iniciar(s, nivel, modo, ayuda_ok, fuente):
        s.gen += 1; s.nivel, s.modo, s.fz = nivel, modo, fuente
        s.m = dict(aciertos=0, errores=0, intentos=0, ayudas=0); s.seg = 0; s.hechas = set(); s.primera = None
        s.bloq = False; s.en_pausa = False; s.activo = True; s.ronda = 0; s.ayuda_ok = ayuda_ok
        s.ui.btnAyuda.setVisible(ayuda_ok); s.ui.frameTablero.setEnabled(True); s.ui.btnPausa.setText("⏸ Pausa")
        s.ui.lblConsigna.setVisible(modo == "atencion")
        if modo == "atencion": s.f, s.c, s.rondas, s.tipo = ATENCION[nivel - 1]; s.nueva_ronda()
        else:
            s.f, s.c = TAM[nivel - 1]; fr = random.sample(FRUTAS, s.f * s.c // 2); cartas = []
            for i, x in enumerate(fr): cartas += [(i, "img", x), (i, "img" if modo == "memoria" else "txt", x)]
            random.shuffle(cartas); s.armar(cartas, "oculta"); s.ui.lblMensaje.setText("Toca una carta para empezar. Busca las parejas 🔍")
        s.crono.start(1000); s.tick(False)

    def armar(s, cartas, est):
        s.cartas = cartas
        while s.grid.count(): s.grid.takeAt(0).widget().deleteLater()
        s.btns = []
        for k in range(len(cartas)):
            b = W.QPushButton(); b.setSizePolicy(W.QSizePolicy.Expanding, W.QSizePolicy.Expanding)
            b.clicked.connect(lambda _, k=k: s.tocar(k)); s.grid.addWidget(b, k // s.c, k % s.c); s.btns.append(b); s.estilo(k, est)

    def nueva_ronda(s):  # modo atención: pid 1 = carta correcta
        n = s.f * s.c; s.bloq = False
        if s.tipo == "especifica":
            objetivo = random.choice(FRUTAS); resto = [x for x in FRUTAS if x != objetivo]
            cartas = [(1, "img", objetivo)] + [(0, "img", random.choice(resto)) for _ in range(n - 1)]
            s.ui.lblConsigna.setText(f"Toca la {objetivo[0]} {objetivo[1]}")
        else:
            a, b = random.sample(FRUTAS, 2); cartas = [(1, "img", b)] + [(0, "img", a) for _ in range(n - 1)]
            s.ui.lblConsigna.setText("Encuentra la fruta diferente 👀")
        random.shuffle(cartas); s.armar(cartas, "visible"); s.ui.lblMensaje.setText("Mira con calma 😊"); s.tick(False)

    def estilo(s, k, est):
        b = s.btns[k]; _, tipo, fr = s.cartas[k]
        if est == "oculta": b.setIcon(G.QIcon()); b.setText("❓"); css = "background:#7E57C2;color:white;font-size:40pt;"; tam = 40
        else:
            if tipo == "img":
                ruta = imagen(fr[1]); tam = 40
                if ruta: b.setText(""); b.setIcon(G.QIcon(ruta)); b.setIconSize(C.QSize(100, 100))
                else: b.setIcon(G.QIcon()); b.setText(fr[0])
            else: b.setIcon(G.QIcon()); b.setText(fr[1]); tam = s.fz + 2
            css = {"visible": "background:white;color:#311B92;border:4px solid #81D4FA;", "ok": "background:#B3E5FC;color:#01579B;",
                   "dim": "background:#E0E0E0;color:#999;"}[est] + f"font-size:{tam}pt;font-weight:bold;"
        b.setEnabled(est != "dim"); b.setStyleSheet(css + "border-radius:16px;")

    def tick(s, sumar=True):
        if sumar: s.seg += 1
        prog = f"Ronda {min(s.ronda + 1, s.rondas)}/{s.rondas}" if s.modo == "atencion" else f"Parejas: {len(s.hechas) // 2}/{len(s.cartas) // 2}"
        s.ui.lblInfo.setText(f"Nivel {s.nivel}   ⏱ {s.seg // 60}:{s.seg % 60:02d}   {prog}")

    def tocar(s, k):
        if s.en_pausa or s.bloq or k in s.hechas: return
        if s.modo == "atencion": s.tocar_atencion(k)
        else: s.tocar_memoria(k)

    def tocar_atencion(s, k):
        s.m["intentos"] += 1
        if s.cartas[k][0] == 1:
            s.m["aciertos"] += 1; s.ronda += 1; s.estilo(k, "ok"); s.ui.lblMensaje.setText("¡Muy bien! 🎉"); s.tick(False)
            if s.ronda >= s.rondas: s.terminar("completada")
            else: s.bloq = True; C.QTimer.singleShot(900, lambda g=s.gen: s.nueva_ronda() if g == s.gen else None)
        else:
            s.m["errores"] += 1; s.estilo(k, "dim"); s.hechas.add(k); s.ui.lblMensaje.setText("Casi... ¡prueba con otra! 💪")

    def tocar_memoria(s, k):
        if k == s.primera: return
        s.estilo(k, "visible")
        if s.primera is None: s.primera = k; return
        a, b = s.primera, k; s.primera = None; s.m["intentos"] += 1
        if s.cartas[a][0] == s.cartas[b][0]:
            s.m["aciertos"] += 1; s.hechas |= {a, b}; s.estilo(a, "ok"); s.estilo(b, "ok"); s.ui.lblMensaje.setText("¡Muy bien! 🎉"); s.tick(False)
            if len(s.hechas) == len(s.cartas): s.terminar("completada")
        else:
            s.m["errores"] += 1; s.bloq = True; s.ui.lblMensaje.setText("Casi... ¡tú puedes! 💪")
            C.QTimer.singleShot(1000, lambda g=s.gen: s.restaurar(g, [a, b], "oculta"))

    def restaurar(s, g, ks, est):
        if g != s.gen: return
        for k in ks: s.estilo(k, est)
        s.bloq = False

    def ayuda(s):  # NO penaliza: solo se registra
        if not s.ayuda_ok or s.en_pausa or s.bloq or s.primera is not None: return
        if s.modo == "atencion": ks, vuelta = [k for k, c in enumerate(s.cartas) if c[0] == 1], "visible"
        else:
            pend = [k for k in range(len(s.cartas)) if k not in s.hechas]; pid = s.cartas[random.choice(pend)][0]
            ks, vuelta = [k for k in pend if s.cartas[k][0] == pid], "oculta"
        for k in ks: s.estilo(k, "ok" if s.modo == "atencion" else "visible")
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
        s.al_terminar(dict(modo=s.modo, nivel=s.nivel, estado=estado, tiempo_s=s.seg, fecha=hoy(), hora=datetime.now().strftime("%H:%M"), **s.m))

class App(W.QMainWindow):
    def __init__(s):
        super().__init__(); s.setWindowTitle("Memorice de Frutas")
        s.datos = cargar(); s.sembrar(); s.conf = s.datos.setdefault("config", {"fuente": 18, "musica": True}); s.user = None; s.modo = None; s.cargando = False
        s.pila = W.QStackedWidget(); cen = W.QWidget(); v = W.QVBoxLayout(cen); s.setCentralWidget(cen)
        cen.setStyleSheet("QWidget{background:#E1F5FE;color:#311B92;}QPushButton{background:#7E57C2;color:white;border-radius:12px;padding:6px 14px;font-weight:bold;}")
        barra = W.QHBoxLayout(); barra.addStretch(1); barra.addWidget(W.QLabel("Letra:"))   # barra fija: visible en todas las pantallas
        s.bMenos, s.bMas, s.bMusica = (W.QPushButton(t) for t in ("A−", "A+", "🔊 Música"))
        for b in (s.bMenos, s.bMas, s.bMusica): b.setMinimumHeight(44); barra.addWidget(b)
        v.addLayout(barra); v.addWidget(s.pila, 1)
        L = lambda n: uic.loadUi(os.path.join(BASE, "ui", n + ".ui"))
        s.login, s.mod, s.niv, s.tut, s.jug, s.panel = (L(n) for n in ("login", "modo", "niveles", "tutorial", "juego", "panel"))
        for p in (s.login, s.mod, s.niv, s.tut, s.jug, s.panel): s.pila.addWidget(p)
        s.juego = Juego(s.jug, s.fin_juego, s.sonido)
        s.login.btnEntrar.clicked.connect(s.entrar); s.login.txtUsuario.returnPressed.connect(s.entrar)
        for m, b in (("memoria", s.mod.btnMemoria), ("asociacion", s.mod.btnAsociacion), ("atencion", s.mod.btnAtencion)):
            b.clicked.connect(lambda _, m=m: s.elegir_modo(m))
        s.bMenos.clicked.connect(lambda: s.cambiar_fuente(-2)); s.bMas.clicked.connect(lambda: s.cambiar_fuente(2))
        s.mod.btnCambiar.clicked.connect(lambda: s.ir(s.login)); s.niv.btnVolverModo.clicked.connect(s.mostrar_modo)
        s.niv.btnComoJugar.clicked.connect(lambda: s.mostrar_tutorial(False))
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
        nom = s.login.txtUsuario.text().strip(); perfil = s.login.cmbPerfil.currentText().lower(); us = s.datos["usuarios"]
        if not nom or len(nom) > 20: s.error_login("Escribe un nombre de 1 a 20 letras"); return
        if nom in us and us[nom]["perfil"] != perfil: s.error_login(f"'{nom}' está registrado como {us[nom]['perfil']}"); return
        if nom not in us: us[nom] = nuevo_usuario(perfil); s.guardar_o_avisar()
        s.user = nom; s.login.lblError.setText(""); s.aplicar_fuente()
        if perfil == "profesional": s.mostrar_panel(); return
        s.mostrar_modo()
        if us[nom]["ultimo_juego"] != hoy() and s.tray.isSystemTrayAvailable():
            s.tray.show(); s.tray.showMessage("¡Hora de tu memorice!", "Tu nivel del día te espera 🍓")

    def mostrar_modo(s):
        u = s.U()
        if not u["ultimo_juego"]: r = "¡Comienza tu primera racha hoy! 🌱"
        elif u["ultimo_juego"] in (hoy(), ayer()): r = f"🔥 Llevas {u['racha']} día(s) seguidos"
        else: r = "¡Qué bueno verte de vuelta! Tu progreso sigue aquí 😊"
        s.mod.lblSaludo.setText(f"Hola, {s.user} 👋"); s.mod.lblRacha.setText(r); s.ir(s.mod)

    def elegir_modo(s, m):
        s.modo = m
        if m not in s.U()["tutorial"]: s.mostrar_tutorial(True)
        else: s.mostrar_niveles()

    def mostrar_tutorial(s, primera):
        ej, txt = TUTO[s.modo]; s.tut.lblTituloTut.setText("Cómo se juega: " + MODOS[s.modo]); s.tut.lblEjemplo.setText(ej); s.tut.lblTexto.setText(txt)
        s.tut.btnEmpezar.setText("¡Entendido, a jugar!" if primera else "Seguir"); s.ir(s.tut)

    def empezar_desde_tutorial(s):
        u = s.U()
        if s.modo not in u["tutorial"]: u["tutorial"].append(s.modo); s.guardar_o_avisar()
        s.mostrar_niveles()

    def mostrar_niveles(s):
        u = s.U(); s.niv.lblModo.setText(MODOS[s.modo]); lay = s.niv.frameNiveles.layout()
        while lay.count(): lay.takeAt(0).widget().deleteLater()
        disp = disponibles(u, s.modo)
        for i in range(1, NIV + 1):
            txt = (("⭐ Nivel del día: " if i == disp else "Nivel ") + str(i)) if i <= disp else f"🔒 Nivel {i} (mañana)"
            b = W.QPushButton(txt); b.setEnabled(i <= disp); b.clicked.connect(lambda _, i=i: s.jugar(i)); lay.addWidget(b)
        s.ir(s.niv)

    def jugar(s, nivel):
        u = s.U(); s.juego.iniciar(nivel, s.modo, u["ayuda"], s.conf["fuente"]); s.ir(s.jug)

    def fin_juego(s, reg):
        u = s.U(); u["sesiones"].append(reg)
        if reg["estado"] == "completada":
            actualizar_racha(u); p = u["progreso"][reg["modo"]]
            if reg["nivel"] == p["max"] + 1: p["max"] = reg["nivel"]; p["fecha"] = hoy()
        s.guardar_o_avisar()
        if reg["estado"] == "completada":
            msg = random.choice(["¡Excelente trabajo! 🌟", "¡Qué buena memoria tienes! 🍓", "¡Sigue así, lo estás haciendo genial! 💪", "¡Un día más cuidando tu mente! 😊"])
            s.aviso("¡Nivel completado!", f"{msg}\n\nTiempo: {reg['tiempo_s']} s · Errores: {reg['errores']}", "ganar.wav")
        else: s.aviso("Sesión guardada", "Tu sesión quedó guardada como interrumpida. ¡Vuelve cuando quieras!", "aviso.wav")
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