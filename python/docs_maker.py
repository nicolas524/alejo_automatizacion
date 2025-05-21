#!/usr/bin/env python3
# fill_templates.py

from pathlib import Path
import pandas as pd
from docxtpl import DocxTemplate

# 1) Cargo el Excel forzando todo a str
df = pd.read_excel("outputs/datos_deudores.xlsx", dtype=str)

# 2) Defino carpeta de salida bajo "outputs/filled_docs" y la plantilla
OUT_DIR  = Path("outputs") / "filled_docs"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATE = Path("template.docx")

# 3) Inspecciono variables que espera
tpl = DocxTemplate(TEMPLATE)
print("Variables en plantilla:", tpl.get_undeclared_template_variables())

# 4) Renderizado fila por fila
for _, row in df.iterrows():
    tpl = DocxTemplate(TEMPLATE)
    context = {
        # Dinámicos en MAYÚSCULAS
        "carpeta":               row["carpeta"].upper(),
        "CARPETA":               row["carpeta"].upper(),
        "nombres_completos":     row["nombres_completos"].upper(),
        "NOMBRE":                row["nombres_completos"].upper(),
        "numero_identificacion": row["numero_identificacion"].upper(),
        "placa":                 row.get("placa","").upper(),
        "marca":                 row.get("marca","").upper(),
        "linea":                 row.get("linea","").upper(),
        "modelo":                row.get("modelo","").upper(),
        "color":                 row.get("color","").upper(),
        "servicio":              row.get("servicio","").upper(),
        "monto_ejecucion":       row.get("monto_ejecucion","").upper(),
        "direccion":             row.get("direccion","").upper(),
        "municipio":             row.get("municipio","").upper(),
        "fecha_ejecucion":       row.get("fecha_ejecucion","").upper(),
        "fecha_notificacion":    row.get("fecha_notificacion_juridica","").upper(),
        # CORREO en minúsculas
        "email":                 row.get("email","").lower(),
    }

    tpl.render(context)
    safe_name = row["nombres_completos"].replace(" ", "_")
    out_path = OUT_DIR / f"{row['carpeta']}_{safe_name}.docx"
    tpl.save(out_path)
    print(f"📝 Generado: {out_path}")