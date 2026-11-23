# Memorice de Frutas: cómo crear el instalador de Windows

## Qué hay en esta carpeta
| Archivo | Para qué sirve |
|---|---|
| `main.py`, `ui/`, `recursos/` | Tu juego (con 2 arreglos, ver abajo) |
| `memorice.spec` | Instrucciones para PyInstaller (crea el .exe) |
| `installer.iss` | Instrucciones para Inno Setup (crea el Setup.exe) |
| `icon.ico` | Ícono del juego (hecho con la frutilla) |
| `requirements.txt` | Librerías que necesita (solo PyQt5) |
| `.github/workflows/build.yml` | Receta para que GitHub lo compile solo |
| `build.yml.txt` | Copia del anterior (por si la carpeta oculta `.github` no se sube) |

## Pasos (sin instalar nada en tu PC)
1. Entra a **github.com** y crea una cuenta (gratis).
2. Arriba a la derecha: **+ → New repository**. Ponle un nombre (ej. `memorice`), déjalo en **Public** y toca **Create repository**.
3. En el repositorio nuevo toca **uploading an existing file** y arrastra **todo el contenido** de esta carpeta (descomprímela antes). Toca **Commit changes**.
4. Revisa que exista `.github/workflows/build.yml`. Si no aparece (las carpetas que empiezan con punto a veces no se arrastran):
   - **Add file → Create new file**
   - En el nombre escribe exactamente: `.github/workflows/build.yml` (al escribir las `/` se crean las carpetas)
   - Pega el contenido de `build.yml.txt` y toca **Commit changes**.
5. Entra a la pestaña **Actions**. Verás una ejecución en marcha (círculo amarillo). Tarda unos 4-8 minutos. Si no arrancó sola: toca el workflow → **Run workflow**.
6. Cuando salga el check verde ✅, entra a esa ejecución y abajo, en **Artifacts**, descarga **MemoriceFrutas-Windows**. Dentro hay:
   - `MemoriceFrutas_Setup.exe`: el **instalador** (el que repartes)
   - `MemoriceFrutas_Portable.zip`: versión sin instalar (descomprimir y abrir `MemoriceFrutas.exe`)

### Para tener un link de descarga público
En la página del repo: **Releases → Create a new release → Choose a tag**, escribe `v1.0.0` → **Create new tag** → **Publish release**. GitHub compila de nuevo y adjunta el instalador en esa página; ese es el link que compartes.

## Los 2 arreglos que le hice a tu código
1. **Rutas**: dentro del .exe, `ui/` y `recursos/` están en una carpeta temporal. Ahora `BASE` usa `sys._MEIPASS` cuando corre empaquetado.
2. **Guardado de progreso**: instalado en `Program Files`, Windows no deja escribir ahí. Ahora, ya instalado, `datos.json` se guarda en `%APPDATA%\MemoriceFrutas\datos.json` (cada usuario de Windows tiene el suyo). Si lo corres normal con Python, sigue usando la carpeta `datos/` como antes.
   Nota: el `datos.json` que venía en tu zip no se incluye; el juego crea solo los usuarios Demo y Profesional la primera vez.

Todo lo demás del juego quedó idéntico.

## Si algo sale mal
- **Actions sale con ❌**: entra a la ejecución, abre el paso en rojo y cópiame el error.
- **Windows muestra "Windows protegió su PC" (SmartScreen)**: es normal con programas sin firma digital. Tocar **Más información → Ejecutar de todas formas**. Firmarlo cuesta dinero (certificado de código); para repartir a conocidos o pacientes no suele hacer falta.
- **Algún antivirus lo marca**: pasa a veces con PyInstaller (falso positivo). El instalador es lo más estable.
- **Cambiar versión**: edita `AppVersion` en `installer.iss`.
- **Cambiar el ícono**: reemplaza `icon.ico` (puedes convertir un PNG en convertio.co o similar).
