"""
Organiza archivos con el patron:
    PersonaXX_<Ejercicio>_<Angulo>_<numero>.<ext>
en carpetas:
    personaXX/<Ejercicio>/<Angulo>_<numero>.<ext>

Ejemplo:
    Persona01_Chair_Dip_45_grados_0001.png
        -> persona01/Chair_Dip/45_grados_0001.png
    Persona01_Estiramiento_lateral_Frontal_0005.png
        -> persona01/Estiramiento_lateral/Frontal_0005.png

Uso:
    python organizar_fotos.py            # solo muestra que haria (dry-run)
    python organizar_fotos.py --apply    # ejecuta los movimientos de verdad
    python organizar_fotos.py --apply --copy   # copia en vez de mover
"""

import argparse
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

# Angulos conocidos (se detectan sin importar mayusculas/minusculas)
ANGULOS = ["45_grados", "Frontal", "Lateral"]
ANGULO_PATTERN = "|".join(re.escape(a) for a in ANGULOS)

FILENAME_RE = re.compile(
    rf"^Persona(?P<persona>\d+)_(?P<ejercicio>.+)_(?P<angulo>{ANGULO_PATTERN})_(?P<numero>\d+)\.(?P<ext>\w+)$",
    re.IGNORECASE,
)


def normalizar_angulo(angulo: str) -> str:
    for a in ANGULOS:
        if a.lower() == angulo.lower():
            return a
    return angulo


def main():
    parser = argparse.ArgumentParser(description="Organiza fotos por persona/ejercicio/angulo")
    parser.add_argument("--source", default=".", help="Carpeta con los archivos originales (default: carpeta actual)")
    parser.add_argument("--dest", default=".", help="Carpeta donde crear las subcarpetas organizadas (default: carpeta actual)")
    parser.add_argument("--apply", action="store_true", help="Ejecuta los cambios. Sin esto, solo simula (dry-run)")
    parser.add_argument("--copy", action="store_true", help="Copia los archivos en vez de moverlos")
    args = parser.parse_args()

    source = Path(args.source)
    dest = Path(args.dest)

    archivos = sorted(source.iterdir())

    matches = []
    sin_match = []
    for f in archivos:
        if not f.is_file():
            continue
        m = FILENAME_RE.match(f.name)
        if m:
            matches.append((f, m))
        else:
            sin_match.append(f)

    if not matches:
        print("No se encontraron archivos que coincidan con el patron esperado.")
        return

    # Normaliza el nombre del ejercicio: si aparece con distinta capitalizacion
    # (ej. "Estiramiento_lateral" vs "Estiramiento_Lateral"), usa la variante
    # mas frecuente para todos los archivos de ese ejercicio.
    conteo_por_clave = defaultdict(Counter)
    for f, m in matches:
        clave = m.group("ejercicio").lower()
        conteo_por_clave[clave][m.group("ejercicio")] += 1

    nombre_canonico = {
        clave: contador.most_common(1)[0][0] for clave, contador in conteo_por_clave.items()
    }

    plan = []  # (origen, destino)
    for f, m in matches:
        persona = f"persona{m.group('persona')}"
        ejercicio = nombre_canonico[m.group("ejercicio").lower()]
        angulo = normalizar_angulo(m.group("angulo"))
        numero = m.group("numero")
        ext = m.group("ext")

        carpeta_destino = dest / persona / ejercicio
        archivo_destino = carpeta_destino / f"{angulo}_{numero}.{ext}"
        plan.append((f, archivo_destino))

    # Verifica colisiones (dos origenes mapeando al mismo destino)
    destinos = Counter(str(d) for _, d in plan)
    colisiones = {d: c for d, c in destinos.items() if c > 1}
    if colisiones:
        print("ADVERTENCIA: se detectaron colisiones de nombres de destino:")
        for d, c in colisiones.items():
            print(f"  {d}  <-  {c} archivos distintos")
        print("Revisa los nombres antes de continuar. Abortando.")
        return

    accion = "Copiando" if args.copy else "Moviendo"
    modo = "APLICANDO" if args.apply else "DRY-RUN (nada se modifica todavia)"
    print(f"Modo: {modo}")
    print(f"Archivos que coinciden con el patron: {len(matches)}")
    if sin_match:
        print(f"Archivos que NO coinciden con el patron (se ignoran): {len(sin_match)}")
        for f in sin_match[:20]:
            print(f"  - {f.name}")
        if len(sin_match) > 20:
            print(f"  ... y {len(sin_match) - 20} mas")
    print()

    for origen, destino in plan:
        print(f"{accion}: {origen.name}  ->  {destino.relative_to(dest) if dest in destino.parents or dest == destino.parent else destino}")
        if args.apply:
            destino.parent.mkdir(parents=True, exist_ok=True)
            if args.copy:
                shutil.copy2(origen, destino)
            else:
                shutil.move(str(origen), str(destino))

    print()
    print(f"Total procesados: {len(plan)}")
    if not args.apply:
        print("Esto fue una simulacion. Ejecuta con --apply para aplicar los cambios de verdad.")


if __name__ == "__main__":
    main()
