from datetime import datetime
import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import streamlit as st

# CONFIGURACIÓN DE LA PÁGINA PARA QUE OCUPE TODO EL ANCHO
st.set_page_config(
    page_title="CONTROL DE INVENTARIO Y EQUIPOS", page_icon="💻", layout="wide"
)

st.title("📋 SISTEMA DE CONTROL E INVENTARIO DE EQUIPOS")
st.markdown(
    "GESTIONA EL INGRESO, REPARACIÓN Y SALIDA DE EQUIPOS TAL COMO EN TU HOJA DE REGISTRO."
)

# ARCHIVO LOCAL PARA PERSISTENCIA SIMPLE DE DATOS
DATA_FILE = "inventario_equipos.csv"


def cargar_datos():
  try:
    df_temp = pd.read_csv(DATA_FILE)
    # FORZAR QUE TODO EL DATAFRAME EXISTENTE TAMBIÉN ESTÉ EN MAYÚSCULAS PARA EVITAR MEZCLAS
    for col in df_temp.select_dtypes(include=["object"]).columns:
      df_temp[col] = df_temp[col].astype(str).str.upper()
    return df_temp
  except FileNotFoundError:
    data = {
        "CLIENTE": [
            "HEYDI",
            "AUTOIDEAL",
            "AHUFE MATERIALES",
            "HEYDI",
            "EMANUEL",
            "IOSSIFT",
        ],
        "TIPO DE EQUIPO": [
            "IMPRESORA",
            "IMPRESORA",
            "IMPRESORA",
            "IMPRESORA",
            "LAPTOP",
            "IMPRESORA",
        ],
        "SERIE": [
            "06YJB8GDBB0OPVB",
            "X644060753",
            "KPLM09739",
            "074FB8GJAF01CSN",
            "PF1EUMOV",
            "XBBV316499",
        ],
        "MARCA": ["SAMSUNG", "EPSON", "CANON", "SAMSUNG", "LENOVO", "EPSON"],
        "MODELO": ["M2022", "L3110", "G2110", "M2020", "IDEAPAD 330", "L5590"],
        "DIAGNÓSTICO": [
            "SENSOR DAÑADO",
            "ESCANER (COMPLETO), BANDA, PLACA LOGICA, FUENTE DE PODER",
            "ERROR DE CONTADOR DE ALMOHADILLAS",
            "RODILLO DE PRESION DAÑADO",
            "BOTON DE ENCENDIDO DAÑADO (TECLADO)",
            "MARCABA ERROR 034004 Y GOLPETEABA AL MOMENTO DE ENCENDERLA",
        ],
        "OBSERVACIONES": [
            "SE REPARO",
            "SE CAMBIARON PIEZAS",
            "SE SOLUCIONO",
            "-",
            "-",
            (
                "SE LE DIO MANTENIMIENTO, DÁNDOLE LIMPIEZA, DESTAPE DE CABEZAL,"
                " SE CAMBIA CAJA DE MANTENIMIENTO"
            ),
        ],
        "FECHA INGRESO": [
            "25/11/2025",
            "12/02/2026",
            "13/02/2026",
            "17/02/2026",
            "17/02/2026",
            "23/02/2026",
        ],
        "FECHA SALIDA": [
            "",
            "",
            "20/02/2026",
            "",
            "",
            "23/2/2026",
        ],
        "ESTADO": [
            "REPARADO",
            "REPARADO",
            "REPARADO",
            "PENDIENTE",
            "PENDIENTE",
            "REPARADO",
        ],
    }
    df_inicial = pd.DataFrame(data)
    df_inicial.to_csv(DATA_FILE, index=False)
    return df_inicial


df = cargar_datos()

# SIDEBAR PARA AGREGAR NUEVOS REGISTROS
st.sidebar.header("➕ AGREGAR NUEVO EQUIPO")
with st.sidebar.form("form_nuevo", clear_on_submit=True):
  c_cliente = st.text_input("CLIENTE")
  c_tipo = st.text_input("TIPO DE EQUIPO")
  c_serie = st.text_input("SERIE")
  c_marca = st.text_input("MARCA")
  c_modelo = st.text_input("MODELO")
  c_diagnostico = st.text_area("DIAGNÓSTICO")
  c_observaciones = st.text_area("OBSERVACIONES")
  c_f_ingreso = st.date_input(
      "FECHA INGRESO", value=datetime.today()
  ).strftime("%d/%m/%Y")
  c_f_salida = st.text_input("FECHA SALIDA (OPCIONAL, DD/MM/AAAA)")
  c_estado = st.selectbox("ESTADO", ["PENDIENTE", "REPARADO"])

  submit = st.form_submit_button("GUARDAR EQUIPO")

  if submit:
    nuevo_registro = pd.DataFrame({
        "CLIENTE": [c_cliente.upper()],
        "TIPO DE EQUIPO": [c_tipo.upper()],
        "SERIE": [c_serie.upper()],
        "MARCA": [c_marca.upper()],
        "MODELO": [c_modelo.upper()],
        "DIAGNÓSTICO": [c_diagnostico.upper()],
        "OBSERVACIONES": [c_observaciones.upper()],
        "FECHA INGRESO": [c_f_ingreso],
        "FECHA SALIDA": [c_f_salida.upper()],
        "ESTADO": [c_estado.upper()],
    })
    df = pd.concat([df, nuevo_registro], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.sidebar.success("¡EQUIPO AGREGADO CON ÉXITO!")
    st.rerun()

# FILTROS RÁPIDOS DE BÚSQUEDA
st.subheader("🔍 FILTROS DE BÚSQUEDA")
col1, col2, col3 = st.columns(3)
with col1:
  filtro_cliente = st.text_input("BUSCAR POR CLIENTE")
with col2:
  filtro_estado = st.selectbox("FILTRAR POR ESTADO", ["TODOS", "PENDIENTE", "REPARADO"])
with col3:
  filtro_serie = st.text_input("BUSCAR POR SERIE")

# APLICAR FILTROS
df_filtrado = df.copy()
if filtro_cliente:
  df_filtrado = df_filtrado[
      df_filtrado["CLIENTE"]
      .str.contains(filtro_cliente.upper(), case=False, na=False)
  ]
if filtro_estado != "TODOS":
  df_filtrado = df_filtrado[df_filtrado["ESTADO"] == filtro_estado]
if filtro_serie:
  df_filtrado = df_filtrado[
      df_filtrado["SERIE"].str.contains(filtro_serie.upper(), case=False, na=False)
  ]


# FUNCIÓN PARA COLOREAR LA TABLA SEGÚN EL ESTADO
def color_estado(val):
  color = "background-color: #2ecc71; color: white;" if val == "REPARADO" else "background-color: #f1c40f; color: black;"
  return color


st.subheader("📊 TABLA DE INVENTARIO")

st.dataframe(
    df_filtrado.style.map(color_estado, subset=["ESTADO"]),
    use_container_width=True,
)


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

  elements.append(Paragraph("REPORTE DE INVENTARIO DE EQUIPOS", title_style))
  elements.append(Spacer(1, 10))
  elements.append(
      Paragraph(
          f"<b>FILTRO DE ESTADO APLICADO:</b> {estado_filtro} | <b>FECHA DE"
          f" EMISIÓN:</b> {datetime.today().strftime('%d/%m/%Y')}",
          styles['Normal'],
      )
  )
  elements.append(Spacer(1, 15))

  columnas_mostrar = [
      "CLIENTE",
      "TIPO DE EQUIPO",
      "SERIE",
      "MARCA",
      "MODELO",
      "DIAGNÓSTICO",
      "ESTADO",
  ]
  df_pdf = dataframe_filtrado[columnas_mostrar].copy()

  style_cell = ParagraphStyle(
      'CellText', parent=styles['Normal'], fontSize=9, leading=11
  )
  data = [[Paragraph(f'<b>{col}</b>', style_cell) for col in df_pdf.columns]]

  for _, row in df_pdf.iterrows():
    data.append([
        Paragraph(str(val), style_cell) for val in row
    ])

  table = Table(data, colWidths=[100, 80, 90, 70, 70, 200, 70])
  table.setStyle(
      TableStyle([
          ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
          ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
          ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
          ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
          ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
          ('TOPPADDING', (0, 0), (-1, 0), 8),
          ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
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
      label="📥 DESCARGAR INVENTARIO FILTRADO EN PDF",
      data=pdf_data,
      file_name=f"inventario_estado_{filtro_estado.lower()}.pdf",
      mime="application/pdf",
  )
else:
  st.warning("NO HAY REGISTROS PARA MOSTRAR CON LOS FILTROS ACTUALES.")

# SECCIÓN PARA EDITAR O ELIMINAR REGISTROS EXISTENTES
with st.expander("✏️ EDITAR O ELIMINAR REGISTROS"):
  if not df.empty:
    index_a_editar = st.selectbox(
        "SELECCIONA EL NÚMERO DE FILA A MODIFICAR", df.index
    )

    with st.form("form_editar"):
      e_cliente = st.text_input(
          "CLIENTE", value=str(df.loc[index_a_editar, "CLIENTE"])
      )
      e_tipo = st.text_input(
          "TIPO DE EQUIPO", value=str(df.loc[index_a_editar, "TIPO DE EQUIPO"])
      )
      e_serie = st.text_input(
          "SERIE", value=str(df.loc[index_a_editar, "SERIE"])
      )
      e_marca = st.text_input(
          "MARCA", value=str(df.loc[index_a_editar, "MARCA"])
      )
      e_modelo = st.text_input(
          "MODELO", value=str(df.loc[index_a_editar, "MODELO"])
      )
      e_diagnostico = st.text_area(
          "DIAGNÓSTICO", value=str(df.loc[index_a_editar, "DIAGNÓSTICO"])
      )
      e_observaciones = st.text_area(
          "OBSERVACIONES", value=str(df.loc[index_a_editar, "OBSERVACIONES"])
      )
      e_f_ingreso = st.text_input(
          "FECHA INGRESO", value=str(df.loc[index_a_editar, "FECHA INGRESO"])
      )
      e_f_salida = st.text_input(
          "FECHA SALIDA", value=str(df.loc[index_a_editar, "FECHA SALIDA"])
      )
      e_estado = st.selectbox(
          "ESTADO",
          ["PENDIENTE", "REPARADO"],
          index=(
              0
              if df.loc[index_a_editar, "ESTADO"] == "PENDIENTE"
              else 1
          ),
      )

      col_e1, col_e2 = st.columns(2)
      actualizar = col_e1.form_submit_button("ACTUALIZAR REGISTRO")
      eliminar = col_e2.form_submit_button("ELIMINAR REGISTRO")

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
            e_f_salida.upper(),
            e_estado.upper(),
        ]
        df.to_csv(DATA_FILE, index=False)
        st.success("¡REGISTRO ACTUALIZADO CORRECTAMENTE!")
        st.rerun()

      if eliminar:
        df = df.drop(index_a_editar).reset_index(drop=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("¡REGISTRO ELIMINADO CORRECTAMENTE!")
        st.rerun()