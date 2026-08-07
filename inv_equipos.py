from datetime import datetime
import io
from google.oauth2 import service_account
import gspread
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, portrait, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import streamlit as st

# Configuración de la página para que ocupe todo el ancho
st.set_page_config(
    page_title="Ingreso De Equipo A Compumercado ")
st.markdown(
    "Gestiona el ingreso, reparación y salida de equipos conectado a Google Sheets."
)

# Enlace de tu Google Sheet
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Gu9_82stY_tqzEztQqZJUU494IIqjRFXIN1g7XU4B4s/edit?gid=0#gid=0"

def conectar_gsheets():
  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]
  
  if "gcp_service_account" in st.secrets:
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scope)
  else:
    raise Exception("No se encontró la configuración de 'gcp_service_account' en los Secrets de Streamlit.")
  
  gc = gspread.authorize(creds)
  sh = gc.open_by_url(SPREADSHEET_URL)
  return sh

# Usamos caché con ttl=60
@st.cache_data(ttl=60)
def cargar_datos_desde_sheets():
  sh = conectar_gsheets()
  worksheet = sh.worksheet("Mantenimientos")
  data = worksheet.get_all_records()
  return data

def cargar_datos():
  try:
    data = cargar_datos_desde_sheets()
    df = pd.DataFrame(data)
    
    if df.empty:
      return pd.DataFrame(columns=[
          "Cliente", "Tipo de equipo", "Serie", "Marca", "Modelo", 
          "Diagnóstico", "Observaciones", "Fecha ingreso", "Fecha salida", "Estado"
      ])
    df.columns = df.columns.astype(str).str.strip()
    
    # Convertir todas las columnas a texto para evitar conflictos de tipos en las ediciones
    df = df.astype(str)
    # Limpiar posibles "nan" que vengan de celdas vacías en Sheets
    df = df.replace("nan", "")
    
    return df
  except Exception as e:
    st.error(f"❌ Error al conectar con Google Sheets: {e}")
    return pd.DataFrame(columns=[
        "Cliente", "Tipo de equipo", "Serie", "Marca", "Modelo", 
        "Diagnóstico", "Observaciones", "Fecha ingreso", "Fecha salida", "Estado"
    ])

def guardar_datos_en_gsheets(df):
  try:
    sh = conectar_gsheets()
    worksheet = sh.worksheet("Mantenimientos")
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    st.cache_data.clear()
  except Exception as e:
    st.error(f"❌ Error al guardar en Google Sheets: {e}")

# Botón en la barra lateral para sincronizar y forzar la lectura fresca de Google Sheets
if st.sidebar.button("🔄 Sincronizar con Google Sheets"):
  st.cache_data.clear()
  st.rerun()

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
    }).astype(str)
    
    df = pd.concat([df, nuevo_registro], ignore_index=True)
    guardar_datos_en_gsheets(df)
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
  st.info("No hay registros disponibles con los filtros actuales.")
else:
  df_mostrar = df_filtrado.copy()
  df_mostrar.insert(0, "N°", range(1, len(df_mostrar) + 1))
  st.dataframe(df_mostrar, use_container_width=True, hide_index=True)


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


# --- FUNCIÓN PARA GENERAR LA ORDEN DE SERVICIO EN PDF ---
def generar_orden_servicio_pdf(row_data):
  buffer = io.BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=portrait(letter),
      rightMargin=36,
      leftMargin=36,
      topMargin=36,
      bottomMargin=36,
  )
  elements = []
  styles = getSampleStyleSheet()

  style_bold = ParagraphStyle('BoldText', parent=styles['Normal'], fontSize=9, leading=11, fontName='Helvetica-Bold')
  style_normal = ParagraphStyle('NormalText', parent=styles['Normal'], fontSize=9, leading=11, fontName='Helvetica')
  style_center = ParagraphStyle('CenterText', parent=styles['Normal'], fontSize=9, leading=11, fontName='Helvetica', alignment=1)
  style_header = ParagraphStyle('HeaderTxt', parent=styles['Normal'], fontSize=9, leading=11, fontName='Helvetica-Bold', textColor=colors.whitesmoke, alignment=1)

  # Encabezado con datos de Compumercado
  header_data = [
      [
          Paragraph("<b>Calidad y Servicio</b><br/><font size=16 color='#1f3a93'><b>COMPUMERCADO</b></font><br/>VENTA DE EQUIPO DE COMPUTO<br/>Divisoria 506, Col. Fracc. San Angel, CD Altamira, Tamaulipas, CP 89604", style_normal),
          Paragraph("<b>ORDEN DE SERVICIO</b><br/><br/><b>Fecha:</b> " + str(row_data.get("Fecha ingreso", "")), style_normal),
          Paragraph("<b>Teléfonos:</b> (833) 125-2045<br/><b>Oficina:</b> (833) 226-71-86<br/><b>Celular:</b> (833) 407-7804<br/><b>Correos:</b> facturasdjj@gmail.com<br/>compumercadojdiaz@gmail.com", style_normal)
      ]
  ]
  t_head = Table(header_data, colWidths=[200, 140, 200])
  t_head.setStyle(TableStyle([
      ('VALIGN', (0,0), (-1,-1), 'TOP'),
      ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#1f3a93')),
      ('INNERGRID', (0,0), (-1,-1), 0.5, colors.grey),
      ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
      ('TOPPADDING', (0,0), (-1,-1), 6),
      ('BOTTOMPADDING', (0,0), (-1,-1), 6),
      ('LEFTPADDING', (0,0), (-1,-1), 6),
      ('RIGHTPADDING', (0,0), (-1,-1), 6),
  ]))
  elements.append(t_head)
  elements.append(Spacer(1, 10))

  # Bloque PARA / EMPRESA
  cliente_txt = str(row_data.get("Cliente", ""))
  para_empresa_data = [
      [Paragraph("<b>PARA / EMPRESA:</b>", style_bold), Paragraph(cliente_txt, style_normal)]
  ]
  t_para = Table(para_empresa_data, colWidths=[120, 420])
  t_para.setStyle(TableStyle([
      ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
      ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#1f3a93')),
      ('INNERGRID', (0,0), (-1,-1), 0.5, colors.grey),
      ('TOPPADDING', (0,0), (-1,-1), 6),
      ('BOTTOMPADDING', (0,0), (-1,-1), 6),
      ('LEFTPADDING', (0,0), (-1,-1), 6),
      ('RIGHTPADDING', (0,0), (-1,-1), 6),
  ]))
  elements.append(t_para)
  elements.append(Spacer(1, 10))

  # Tabla de Descripción, Cantidad y Total
  desc_texto = (
      f"<b>Tipo de equipo:</b> {row_data.get('Tipo de equipo', '')}<br/>"
      f"<b>Serie:</b> {row_data.get('Serie', '')}<br/>"
      f"<b>Marca:</b> {row_data.get('Marca', '')}<br/>"
      f"<b>Modelo:</b> {row_data.get('Modelo', '')}<br/>"
      f"<b>Diagnóstico:</b> {row_data.get('Diagnóstico', '')}<br/>"
      f"<b>Observaciones:</b> {row_data.get('Observaciones', '')}"
  )

  table_content = [
      [Paragraph("<b>DESCRIPCIÓN DEL PRODUCTO O SERVICIO</b>", style_header), Paragraph("<b>CANTIDAD</b>", style_header), Paragraph("<b>TOTAL</b>", style_header)],
      [Paragraph(desc_texto, style_normal), Paragraph("1", style_center), Paragraph("", style_normal)]
  ]
  t_prod = Table(table_content, colWidths=[340, 100, 100])
  t_prod.setStyle(TableStyle([
      ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1f3a93')),
      ('VALIGN', (0,0), (-1,-1), 'TOP'),
      ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#1f3a93')),
      ('INNERGRID', (0,0), (-1,-1), 0.5, colors.grey),
      ('TOPPADDING', (0,0), (-1,-1), 8),
      ('BOTTOMPADDING', (0,0), (-1,-1), 8),
      ('LEFTPADDING', (0,0), (-1,-1), 6),
      ('RIGHTPADDING', (0,0), (-1,-1), 6),
  ]))
  elements.append(t_prod)
  elements.append(Spacer(1, 15))

  # Firmas
  firma_data = [
      [
          Paragraph("<br/><br/>________________________________________<br/><b>Nombre y Firma de quien Recibe</b>", style_center),
          Paragraph("<br/><br/>________________________________________<br/><b>Nombre y Firma de quien Entrega</b>", style_center)
      ]
  ]
  t_firmas = Table(firma_data, colWidths=[270, 270])
  t_firmas.setStyle(TableStyle([
      ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
      ('TOPPADDING', (0,0), (-1,-1), 20),
  ]))
  elements.append(t_firmas)

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

# Sección para editar o eliminar registros existentes de forma segura
with st.expander("✏️ Editar o Eliminar Registros"):
  if not df.empty:
    opciones_filas = ["-- Selecciona un equipo --"] + [
        f"Fila {i+1} - Cliente: {row['Cliente']} (Serie: {row['Serie']})"
        for i, row in df.iterrows()
    ]
    
    seleccion_usuario = st.selectbox(
        "Selecciona el equipo a modificar", opciones_filas
    )
    
    if seleccion_usuario != "-- Selecciona un equipo --":
      index_a_editar = opciones_filas.index(seleccion_usuario) - 1

      with st.form("form_editar"):
        e_cliente = st.text_input(
            "Cliente", value=str(df.iloc[index_a_editar]["Cliente"])
        )
        e_tipo = st.text_input(
            "Tipo de equipo", value=str(df.iloc[index_a_editar]["Tipo de equipo"])
        )
        e_serie = st.text_input(
            "Serie", value=str(df.iloc[index_a_editar]["Serie"])
        )
        e_marca = st.text_input(
            "Marca", value=str(df.iloc[index_a_editar]["Marca"])
        )
        e_modelo = st.text_input(
            "Modelo", value=str(df.iloc[index_a_editar]["Modelo"])
        )
        e_diagnostico = st.text_area(
            "Diagnóstico", value=str(df.iloc[index_a_editar]["Diagnóstico"])
        )
        e_observaciones = st.text_area(
            "Observaciones", value=str(df.iloc[index_a_editar]["Observaciones"])
        )
        e_f_ingreso = st.text_input(
            "Fecha ingreso", value=str(df.iloc[index_a_editar]["Fecha ingreso"])
        )
        e_f_salida = st.text_input(
            "Fecha salida", value=str(df.iloc[index_a_editar]["Fecha salida"])
        )
        e_estado = st.selectbox(
            "Estado",
            ["Pendiente", "Reparado"],
            index=(
                0
                if str(df.iloc[index_a_editar]["Estado"]) == "Pendiente"
                else 1
            ),
        )

        col_e1, col_e2, col_e3 = st.columns(3)
        actualizar = col_e1.form_submit_button("Actualizar Registro")
        eliminar = col_e2.form_submit_button("Eliminar Registro")
        
        # Botón de Orden de Servicio dentro del formulario (como submit button)
        orden_servicio_btn = col_e3.form_submit_button("📄 Orden de Servicio")

        if actualizar:
          df.loc[df.index[index_a_editar], "Cliente"] = e_cliente.upper()
          df.loc[df.index[index_a_editar], "Tipo de equipo"] = e_tipo.upper()
          df.loc[df.index[index_a_editar], "Serie"] = e_serie.upper()
          df.loc[df.index[index_a_editar], "Marca"] = e_marca.upper()
          df.loc[df.index[index_a_editar], "Modelo"] = e_modelo.upper()
          df.loc[df.index[index_a_editar], "Diagnóstico"] = e_diagnostico.upper()
          df.loc[df.index[index_a_editar], "Observaciones"] = e_observaciones.upper()
          df.loc[df.index[index_a_editar], "Fecha ingreso"] = e_f_ingreso
          df.loc[df.index[index_a_editar], "Fecha salida"] = e_f_salida
          df.loc[df.index[index_a_editar], "Estado"] = e_estado
          
          guardar_datos_en_gsheets(df)
          st.success("¡Registro actualizado correctamente en Google Sheets!")
          st.rerun()

        if eliminar:
          df = df.drop(df.index[index_a_editar]).reset_index(drop=True)
          guardar_datos_en_gsheets(df)
          st.success("¡Registro eliminado correctamente de Google Sheets!")
          st.rerun()

      # Si se hizo clic en Orden de Servicio, generamos el botón de descarga justo abajo
      if 'orden_servicio_btn' in locals() and orden_servicio_btn:
        row_dict = df.iloc[index_a_editar].to_dict()
        pdf_os_data = generar_orden_servicio_pdf(row_dict)
        st.success("¡Orden de servicio generada con éxito!")
        st.download_button(
            label="📥 Descargar PDF de Orden de Servicio",
            data=pdf_os_data,
            file_name=f"orden_servicio_{row_dict.get('Serie', 'equipo')}.pdf",
            mime="application/pdf",
        )
    else:
      st.info("👆 Selecciona un equipo arriba para cargar sus datos y poder editarlos o eliminarlos de forma segura.")