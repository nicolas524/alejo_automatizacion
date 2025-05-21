import fitz                # PyMuPDF
import re
import unicodedata
import logging
from pathlib import Path
from rapidfuzz import fuzz
import pandas as pd

# ————— Configuración de logging —————
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# -------------- Helpers de normalización --------------

def normalize_filename(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

def normalize_text(text: str) -> str:
    text = text.replace("\u00A0", " ")
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn").lower()

def fuzzy_find_pdf(directory: Path, pattern: str, threshold: int = 70):
    """
    Busca el PDF cuyo nombre fuzzy‐matchee más alto con pattern.
    Devuelve (Path, score) o (None, None).
    """
    candidates = []
    for pdf in directory.glob("*.pdf"):
        score = fuzz.partial_ratio(pattern, normalize_filename(pdf.stem))
        if score >= threshold:
            candidates.append((pdf, score))
    if not candidates:
        return None, None
    return max(candidates, key=lambda x: x[1])

# -------------- Extracciones --------------

def extract_deudor_info(pdf_path: Path) -> dict:
    try:
        with fitz.open(pdf_path) as doc:
            full = "".join(page.get_text() for page in doc)
        norm = normalize_text(full)
        m = re.search(
            r"a\.1\.?\s*informacion\s+sobre\s+el\s+deudor\s*(.*?)(?=[cC]\.)",
            norm, flags=re.S
        )
        section = m.group(1) if m else ""
        patterns = {
            'numero_identificacion': r"numero de identificacion[:\s]*([^\n]+)",
            'primer_apellido':       r"primer apellido[:\s]*([^\n]+)",
            'segundo_apellido':      r"segundo apellido[:\s]*([^\n]+)",
            'primer_nombre':         r"primer nombre[:\s]*([^\n]+)",
            'segundo_nombre':        r"segundo nombre[:\s]*([^\n]+)",
            'pais':                  r"pais[:\s]*([^\n]+)",
            'departamento':          r"departamento[:\s]*([^\n]+)",
            'municipio':             r"municipio[:\s]*([^\n]+)",
            'direccion':             r"direccion[:\s]*([^\n]+)",
            'telefono_celular':      r"telefono\(s\)\s*celular[:\s]*([^\n]+)",
            'email':                 r"direccion electronica\s*\(?email\)?[:\s]*([^\n,]+)",
        }
        data = {}
        for key, pat in patterns.items():
            mm = re.search(pat, section)
            if not mm:
                data[key] = None
                continue
            val = mm.group(1).strip()
            if key == 'direccion':
                val = val.replace('[','').replace(']','').strip()
            if key in ('primer_nombre','segundo_nombre') and \
               re.fullmatch(r'(sexo|femenino|masculino)', val, flags=re.I):
                data[key] = None
            else:
                # email en minúsculas, resto en Title Case
                data[key] = val.lower() if key=='email' else val.title()

        parts = [data.get(f) or "" for f in (
            'primer_apellido','segundo_apellido','primer_nombre','segundo_nombre')]
        data['nombres_completos'] = " ".join(p for p in parts if p)
        return data

    except Exception as e:
        logging.error(f"    Error extract_deudor_info({pdf_path.name}): {e}")
        keys = ['numero_identificacion','primer_apellido','segundo_apellido',
                'primer_nombre','segundo_nombre','pais','departamento',
                'municipio','direccion','telefono_celular','email','nombres_completos']
        return {k: None for k in keys}

def extract_amount_info(pdf_path: Path) -> str:
    try:
        with fitz.open(pdf_path) as doc:
            full = "".join(page.get_text() for page in doc)
        norm = normalize_text(full)
        m = re.search(r"total\s*:\s*\$?\s*([\d\.,]+)", norm, flags=re.I)
        return m.group(1) if m else None

    except Exception as e:
        logging.error(f"    Error extract_amount_info({pdf_path.name}): {e}")
        return None

def extract_fecha_ejecucion(pdf_path: Path) -> str:
    try:
        with fitz.open(pdf_path) as doc:
            full = "".join(page.get_text() for page in doc)
        m = re.search(
            r"fecha\s+y\s+hora\s+de\s+validez\s+de\s+la\s+inscripci[oó]n\s*([^\n]+)",
            full, flags=re.I
        )
        return m.group(1).strip() if m else None

    except Exception as e:
        logging.error(f"    Error extract_fecha_ejecucion({pdf_path.name}): {e}")
        return None

def extract_notification_date(pdf_path: Path) -> str:
    try:
        with fitz.open(pdf_path) as doc:
            full = "".join(page.get_text() for page in doc)
        m = re.search(
            r"Fecha Admisión\s*([0-9]{4}-[0-9]{2}-[0-9]{2}\s+[0-9:]+)",
            full, flags=re.I
        )
        return m.group(1).strip() if m else None

    except Exception as e:
        logging.error(f"    Error extract_notification_date({pdf_path.name}): {e}")
        return None

def extract_vehicle_info(pdf_path: Path) -> dict:
    try:
        with fitz.open(pdf_path) as doc:
            text = "".join(page.get_text() for page in doc).replace("\u00A0", " ")
        lines = text.splitlines()
        labels = {
            'placa':    r'placa\b',
            'servicio': r'tipo de servicio\b',
            'marca':    r'marca\b',
            'linea':    r'l[ií]nea\b',
            'modelo':   r'modelo\b',
            'color':    r'color\b',
        }
        data = {k: None for k in labels}
        for key, pat in labels.items():
            for i, line in enumerate(lines):
                if re.search(pat, line, flags=re.I):
                    for v in lines[i+1:]:
                        v = v.strip()
                        if not v: continue
                        low = v.lower()
                        if re.search(r'\d+/\d+', v) and ':' in v: continue
                        if 'consulta ciudadano' in low or low.startswith('http'): continue
                        if re.match(r'^\d+/\d+$', v): continue
                        data[key] = v
                        break
                    break
        return data

    except Exception as e:
        logging.error(f"    Error extract_vehicle_info({pdf_path.name}): {e}")
        return {k: None for k in ['placa','servicio','marca','linea','modelo','color']}

# -------------- Main: recorre, extrae, arma DataFrame y exporta --------------

def main():
    inputs_dir = Path.cwd() / "inputs"
    target = "formulario de ejecucion"
    threshold = 85
    rows = []

    for sub in sorted(inputs_dir.iterdir(), key=lambda p: p.name):
        if not (sub.is_dir() and sub.name.isdigit()):
            continue

        logging.info(f"💻 Procesando carpeta {sub.name}")
        try:
            # listado único de PDFs por carpeta
            pdfs = list(sub.glob("*.pdf"))

            # 1) formulario
            form_pdf, score = fuzzy_find_pdf(sub, target, threshold)
            if not form_pdf:
                logging.warning(f"  → No se encontró formulario en {sub.name}")
                continue

            # 2) elegir el de prefijo numérico mayor
            candidatos = [
                (p, fuzz.partial_ratio(target, normalize_filename(p.stem)))
                for p in pdfs
            ]
            candidatos = [(p,s) for p,s in candidatos if s>=threshold]
            candidatos.sort(
                key=lambda x: (int(re.match(r'(\d+)', x[0].stem).group(1)), x[1]),
                reverse=True
            )
            form_pdf, score = candidatos[0]

            # 3) extracciones
            deudor      = extract_deudor_info(form_pdf)
            monto       = extract_amount_info(form_pdf)
            fecha_ej    = extract_fecha_ejecucion(form_pdf)

            # 4) acuse electrónico
            acuse_pdf, _ = fuzzy_find_pdf(sub, "acuse electronicos", 70)
            fecha_not    = extract_notification_date(acuse_pdf) if acuse_pdf else None

            # 5) runt
            runt_pdf, _ = fuzzy_find_pdf(sub, "runt", 70)
            veh         = extract_vehicle_info(runt_pdf) if runt_pdf else {}

            # 6) existencia de otros
            def exists(pat):
                pdf,_ = fuzzy_find_pdf(sub, pat, 70)
                return bool(pdf)
            rgm        = exists("formulario de inscripcion inicial")
            poder      = exists("poder")
            carta      = exists("carta unica") or exists("reconocer") or exists("fiserv")
            prenda     = exists("prenda")
            runt_exist = bool(runt_pdf)

            # 7) construye fila
            row = {
                'carpeta':                        sub.name,
                'formulario':                     form_pdf.name,
                'runt_pdf':                       runt_pdf.name   if runt_pdf else None,
                'acuse_pdf':                      acuse_pdf.name  if acuse_pdf else None,
                'fuzzy_score_formulario':         round(score,1),
                'monto_ejecucion':                monto,
                'fecha_ejecucion':                fecha_ej,
                'fecha_notificacion_juridica':    fecha_not,
                'rgm':                            rgm,
                'poder':                          poder,
                'carta_unica':                    carta,
                'runt_exist':                     runt_exist,
                'prenda':                         prenda,
            }
            row.update(deudor)
            row.update(veh)
            rows.append(row)
            logging.info(f"  ✓ Carpeta {sub.name} procesada")

        except Exception as e:
            logging.error(f"  ❌ Error en carpeta {sub.name}: {e}", exc_info=True)

    # 8) DataFrame + Excel/CSV
    df = pd.DataFrame(rows)
    salida_xlsx = Path.cwd() / "outputs/datos_deudores.xlsx"
    salida_csv  = Path.cwd() / "outputs/datos_deudores.csv"
    try:
        df.to_excel(salida_xlsx, index=False)
        logging.info(f"✅ Excel generado en: {salida_xlsx}")
    except ModuleNotFoundError:
        df.to_csv(salida_csv, index=False)
        logging.warning(f"openpyxl no instalado, CSV generado en: {salida_csv}")

if __name__ == "__main__":
    main()