from datetime import datetime
import pandas as pd
import streamlit as st

# Configuración de la página para que ocupe todo el ancho
st.set_page_config(
    page_title="Control de Inventario y Equipos", page_icon="💻", layout="wide"
)

st.title("📋 Sistema de Control e Inventario de Equipos")
st.markdown(
    "Gestiona el ingreso, reparación y salida de equipos tal como en tu hoja de registro."
)

# Archivo local para persistencia simple de datos
DATA_FILE = "inventario_equipos.csv"


def cargar_datos():
  try:
    return pd.read_csv(DATA_FILE)
  except FileNotFoundError:
    # Datos iniciales basados en tu imagen de ejemplo
    data = {
        "Cliente": [
            "HEYDI",
            "AUTOIDEAL",
            "AHUFE MATERIALES",
            "HEYDI",
            "EMANUEL",
            "IOSSIFT",
        ],
        "Tipo de equipo": [
            "impresora",
            "impresora",
            "impresora",
            "impresora",
            "laptop",
            "Impresora",
        ],
        "Serie": [
            "06YJB8GDBB0OPVB",
            "X644060753",
            "KPLM09739",
            "074FB8GJAF01CSN",
            "PF1EUMOV",
            "XBBV316499",
        ],
        "Marca": ["samsung", "Epson", "Canon", "samsung", "Lenovo", "Epson"],
        "Modelo": ["M2022", "L3110", "g2110", "M2020", "Ideapad 330", "L5590"],
        "Diagnóstico": [
            "sensor dañado",
            "escaner (completo), banda, placa logica, fuente de poder",
            "Error de contador de Almohadillas",
            "Rodillo de presion dañado",
            "Boton de encendido dañado (Teclado)",
            "Marcaba error 034004 y golpeteaba al momento de encenderla",
        ],
        "Observaciones": [
            "se reparo",
            "se cambiaron piezas",
            "se soluciono",
            "-",
            "-",
            (
                "Se le dio mantenimiento, dandole limpieza, destape de cabezal,"
                " se cambia caja de mantenimiento"
            ),
        ],
        "Fecha ingreso": [
            "25/11/2025",
            "12/02/2026",
            "13/02/2026",
            "17/02/2026",
            "17/02/2026",
            "23/02/2026",
        ],
        "Fecha salida": [
            "",
            "",
            "20/02/2026",
            "",
            "",
            "23/2/2026",
        ],
        "Estado": [
            "Reparado",
            "Reparado",
            "Reparado",
            "Pendiente",
            "Pendiente",
            "Reparado",
        ],
    }
    df_inicial = pd.DataFrame(data)
    df_inicial.to_csv(DATA_FILE, index=False)
    return df_inicial


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
        "Cliente": [c_cliente],
        "Tipo de equipo": [c_tipo],
        "Serie": [c_serie],
        "Marca": [c_marca],
        "Modelo": [c_modelo],
        "Diagnóstico": [c_diagnostico],
        "Observaciones": [c_observaciones],
        "Fecha ingreso": [c_f_ingreso],
        "Fecha salida": [c_f_salida],
        "Estado": [c_estado],
    })
    df = pd.concat([df, nuevo_registro], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.sidebar.success("¡Equipo agregado con éxito!")
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
if filtro_cliente:
  df_filtrado = df_filtrado[
      df_filtrado["Cliente"]
      .str.contains(filtro_cliente, case=False, na=False)
  ]
if filtro_estado != "Todos":
  df_filtrado = df_filtrado[df_filtrado["Estado"] == filtro_estado]
if filtro_serie:
  df_filtrado = df_filtrado[
      df_filtrado["Serie"].str.contains(filtro_serie, case=False, na=False)
  ]


# Función para colorear la tabla según el estado (Verde para Reparado, Amarillo para Pendiente)
def color_estado(val):
  color = "background-color: #2ecc71; color: white;" if val == "Reparado" else "background-color: #f1c40f; color: black;"
  return color


st.subheader("📊 Tabla de Inventario")

# Mostrar la tabla interactiva con colores personalizados
st.dataframe(
    df_filtrado.style.map(color_estado, subset=["Estado"]),
    use_container_width=True,
)

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
            e_cliente,
            e_tipo,
            e_serie,
            e_marca,
            e_modelo,
            e_diagnostico,
            e_observaciones,
            e_f_ingreso,
            e_f_salida,
            e_estado,
        ]
        df.to_csv(DATA_FILE, index=False)
        st.success("¡Registro actualizado correctamente!")
        st.rerun()

      if eliminar:
        df = df.drop(index_a_editar).reset_index(drop=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("¡Registro eliminado correctamente!")
        st.rerun()