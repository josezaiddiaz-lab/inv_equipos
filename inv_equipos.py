from datetime import datetime
import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from streamlit_gsheets import GSheetsConnection
import streamlit as st

# Configuración de la página para que ocupe todo el ancho
st.set_page_config(
    page_title="Control de Inventario y Equipos", page_icon="💻", layout="wide"
)

st.title("📋 Sistema de Control e Inventario de Equipos")
st.markdown(
    "Gestiona el ingreso, reparación y salida de equipos conectado a Google Sheets."
)

# ------- Conexión a Google Sheets --------- 
conn = st.connection(
    "gsheets",
    type=GSheetsConnection,
    spreadsheet="https://docs.google.com/spreadsheets/d/1JvQ27EDdRINstMHPCJP40NbLt7vl3qir/edit"
)

def cargar_datos():
  try:
    # Lee directamente desde la pestaña "Mantenimientos" de tu Google Sheet
    df = conn.read(worksheet="Mantenimientos", ttl=0)
    if df is None or df.empty:
      return pd.DataFrame(columns=[
          "Cliente", "Tipo de equipo", "Serie", "Marca", "Modelo", 
          "Diagnóstico", "Observaciones", "Fecha ingreso", "Fecha salida", "Estado"
      ])
    # Limpiar espacios en los nombres de las columnas
    df.columns = df.columns.astype(str).str.strip()
    return df
  except Exception as e:
    st.error(f"❌ Error al conectar con Google Sheets: {e}")
    return pd.DataFrame(columns=[
        "Cliente", "Tipo de equipo", "Serie", "Marca", "Modelo", 
        "Diagnóstico", "Observaciones", "Fecha ingreso", "Fecha salida", "Estado"
    ])

df = cargar_datos()

# Sidebar para agregar nuevos registros
st.sidebar.header("➕ Agregar Nuevo Equipo")
with st.sidebar.form("form_nuevo", clear_on_submit=True):
  c_cliente = st.text_input("Cliente")
  c_tipo = st.text_input("Tipo de equipo")
  c_serie = st.text_input("Serie")
  c_marca = st.text_input("Marca")
  c_modelo = st.text_input("Modelo")
  c_diagnostico = st.text_area("Diagnóstico")
  c_observaciones = st.text_area("Observaciones")
  c_f_ingreso = st.date_input(
      "Fecha ingreso", value=datetime.today()
  ).strftime("%d/%m/%Y")
  c_f_salida = st.text_input("Fecha salida (Opcional, dd/mm/aaaa)")
  c_estado = st.selectbox("Estado", ["Pendiente", "Reparado"])

  submit = st.form_submit_button("Guardar Equipo")

  if submit:
    nuevo_registro = pd.DataFrame({
        "Cliente": [c_cliente.upper()],
        "Tipo de equipo": [c_tipo.upper()],
        "Serie": [c_serie.upper()],
        "Marca": [c_marca.upper()],
        "Modelo": [c_modelo.upper()],
        "Diagnóstico": [c_diagnostico.upper()],
        "Observaciones": [c_observaciones.upper()],
        "Fecha ingreso": [c_f_ingreso],
        "Fecha salida": [c_f_salida],
        "Estado": [c_estado],
    })
    df = pd.concat([df, nuevo_registro], ignore_index=True)
    # Guardar cambios en Google Sheets
    conn.update(worksheet="Mantenimientos", data=df.astype(str))
    st.sidebar.success("¡Equipo agregado con éxito a Google Sheets!")
    st.rerun()

# Filtros rápidos de búsqueda
st.subheader("🔍 Filtros de Búsqueda")
col1, col2, col3 = st.columns(3)
with col1:
  filtro_cliente = st.text_input("Buscar por Cliente")
with col2:
  filtro_estado = st.selectbox("Filtrar por Estado", ["Todos", "Pendiente", "Reparado"])
with col3:
  filtro_serie = st.text_input("Buscar por Serie")

# Aplicar filtros
df_filtrado = df.copy()
if filtro_cliente and not df_filtrado.empty and "Cliente" in df_filtrado.columns:
  df_filtrado = df_filtrado[
      df_filtrado["Cliente"]
      .str.contains(filtro_cliente, case=False, na=False)
  ]
if filtro_estado != "Todos" and not df_filtrado.empty and "Estado" in df_filtrado.columns:
  df_filtrado = df_filtrado[df_filtrado["Estado"] == filtro_estado]
if filtro_serie and not df_filtrado.empty and "Serie" in df_filtrado.columns:
  df_filtrado = df_filtrado[
      df_filtrado["Serie"].str.contains(filtro_serie, case=False, na=False)
  ]

st.subheader("📊 Tabla de Inventario")

if df_filtrado.empty:
  st.info("No hay registros disponibles en Google Sheets.")
else:
  # Creamos una copia para visualización que incluya una columna 'N°' enumerada desde 1
  df_mostrar = df_filtrado.copy()
  df_mostrar.insert(0, "N°", range(1, len(df_mostrar) + 1))

  # Sustituido st.dataframe por st.data_editor para permitir edición directa y borrado sincronizado
  df_editado = st.data_editor(
      df_mostrar,
      use_container_width=True,
      num_rows="dynamic",
      key="tabla_inventario_editor",
  )

  # Sincronización automática de cambios de la tabla interactiva con Google Sheets
  if not df_editado.equals(df_mostrar):
    df_limpio = df_editado.drop(columns=["N°"], errors="ignore")

    if filtro_cliente or filtro_estado != "Todos" or filtro_serie:
      df.update(df_limpio)
      df = df.loc[df.index.intersection(df_limpio.index)]
    else:
      df = df_limpio
      
    # Actualizar en Google Sheets
    conn.update(worksheet="Mantenimientos", data=df.astype(str))
    st.success("¡Cambios guardados correctamente en Google Sheets!")
    st.rerun()


# --- FUNCIÓN PARA GENERAR EL PDF ---
def generar_pdf(dataframe_filtrado, estado_filtro):
  buffer = io.BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=landscape(letter),
      rightMargin=30,
      leftMargin=30,
      topMargin=30,
      bottomMargin=30,
  )
  elements = []

  styles = getSampleStyleSheet()
  title_style = ParagraphStyle(
      'TitleStyle',
      parent=styles['Heading1'],
      fontSize=18,
      alignment=1,
      textColor=colors.HexColor('#1f3a93'),
  )

  elements.append(Paragraph("Reporte de Inventario de Equipos", title_style))
  elements.append(Spacer(1, 10))
  elements.append(
      Paragraph(
          f"<b>Filtro de Estado aplicado:</b> {estado_filtro} | <b>Fecha de"
          f" emisión:</b> {datetime.today().strftime('%d/%m/%Y')}",
          styles['Normal'],
      )
  )
  elements.append(Spacer(1, 15))

  columnas_mostrar = [
      "Cliente",
      "Tipo de equipo",
      "Serie",
      "Marca",
      "Modelo",
      "Diagnóstico",
      "Estado",
  ]
  df_pdf = dataframe_filtrado[columnas_mostrar].copy()

  style_cell = ParagraphStyle(
      'CellText', parent=styles['Normal'], fontSize=9, leading=11
  )
  style_header = ParagraphStyle(
      'HeaderText',
      parent=styles['Normal'],
      fontSize=9,
      leading=11,
      textColor=colors.whitesmoke,
      alignment=1,
  )

  data = [[Paragraph(f'<b>{col}</b>', style_header) for col in df_pdf.columns]]

  for _, row in df_pdf.iterrows():
    data.append([Paragraph(str(val), style_cell) for val in row])

  table = Table(data, colWidths=[100, 80, 90, 70, 70, 200, 70])
  table.setStyle(
      TableStyle([
          ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
          ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
          ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
          ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
          ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
          ('TOPPADDING', (0, 0), (-1, 0), 8),
          (
              'ROWBACKGROUNDS',
              (0, 1),
              (-1, -1),
              [colors.white, colors.HexColor('#f8f9fa')],
          ),
          ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
      ])
  )

  elements.append(table)
  doc.build(elements)
  buffer.seek(0)
  return buffer


if not df_filtrado.empty:
  pdf_data = generar_pdf(df_filtrado, filtro_estado)
  st.download_button(
      label="📥 Descargar Inventario Filtrado en PDF",
      data=pdf_data,
      file_name=f"inventario_estado_{filtro_estado.lower()}.pdf",
      mime="application/pdf",
  )
else:
  st.warning("No hay registros para mostrar con los filtros actuales.")

# Sección para editar o eliminar registros existentes
with st.expander("✏️ Editar o Eliminar Registros"):
  if not df.empty:
    index_a_editar = st.selectbox(
        "Selecciona el número de fila a modificar", df.index
    )

    with st.form("form_editar"):
      e_cliente = st.text_input(
          "Cliente", value=str(df.loc[index_a_editar, "Cliente"])
      )
      e_tipo = st.text_input(
          "Tipo de equipo", value=str(df.loc[index_a_editar, "Tipo de equipo"])
      )
      e_serie = st.text_input(
          "Serie", value=str(df.loc[index_a_editar, "Serie"])
      )
      e_marca = st.text_input(
          "Marca", value=str(df.loc[index_a_editar, "Marca"])
      )
      e_modelo = st.text_input(
          "Modelo", value=str(df.loc[index_a_editar, "Modelo"])
      )
      e_diagnostico = st.text_area(
          "Diagnóstico", value=str(df.loc[index_a_editar, "Diagnóstico"])
      )
      e_observaciones = st.text_area(
          "Observaciones", value=str(df.loc[index_a_editar, "Observaciones"])
      )
      e_f_ingreso = st.text_input(
          "Fecha ingreso", value=str(df.loc[index_a_editar, "Fecha ingreso"])
      )
      e_f_salida = st.text_input(
          "Fecha salida", value=str(df.loc[index_a_editar, "Fecha salida"])
      )
      e_estado = st.selectbox(
          "Estado",
          ["Pendiente", "Reparado"],
          index=(
              0
              if df.loc[index_a_editar, "Estado"] == "Pendiente"
              else 1
          ),
      )

      col_e1, col_e2 = st.columns(2)
      actualizar = col_e1.form_submit_button("Actualizar Registro")
      eliminar = col_e2.form_submit_button("Eliminar Registro")

      if actualizar:
        df.loc[index_a_editar] = [
            e_cliente.upper(),
            e_tipo.upper(),
            e_serie.upper(),
            e_marca.upper(),
            e_modelo.upper(),
            e_diagnostico.upper(),
            e_observaciones.upper(),
            e_f_ingreso,
            e_f_salida,
            e_estado,
        ]
        # Actualizar en Google Sheets
        conn.update(worksheet="Mantenimientos", data=df.astype(str))
        st.success("¡Registro actualizado correctamente en Google Sheets!")
        st.rerun()

      if eliminar:
        df = df.drop(index_a_editar).reset_index(drop=True)
        # Actualizar en Google Sheets
        conn.update(worksheet="Mantenimientos", data=df.astype(str))
        st.success("¡Registro eliminado correctamente de Google Sheets!")
        st.rerun()