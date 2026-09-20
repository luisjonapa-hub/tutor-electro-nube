import streamlit as st
from google import genai
from google.genai import types
import datetime
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import os

# 1. Configuración de API Key
API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("⚠️ No se encontró la variable de entorno 'GEMINI_API_KEY'. Configúrala en los Secrets.")
    st.stop()

client = genai.Client(api_key=API_KEY)

# 2. Configuración de página
st.set_page_config(page_title="Tutor-Electro: Práctica 2", page_icon="🔌", layout="wide")
st.title("🔌 Tutor-Electro: Práctica 2 - Módulo Relevador de 5V")

# 3. Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Inicializar estados en session_state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "team_id" not in st.session_state:
    st.session_state.team_id = ""
if "question_timestamps" not in st.session_state:
    st.session_state.question_timestamps = []

# 4. SISTEMA DE AUTENTICACIÓN (LOGIN) EN BARRA LATERAL
st.sidebar.header("🔐 Acceso de Equipos")

if not st.session_state.authenticated:
    team_input = st.sidebar.text_input("Número de Equipo (ej. Equipo F1):")
    pass_input = st.sidebar.text_input("Contraseña:", type="password")
    login_btn = st.sidebar.button("Iniciar Sesión")

    if login_btn:
        try:
            # Leer pestaña "Credenciales"
            creds_df = conn.read(worksheet="Credenciales", ttl=0)
            
            # Buscar coincidencia
            match = creds_df[
                (creds_df["Equipo"].astype(str).str.strip().str.upper() == team_input.strip().upper()) & 
                (creds_df["Password"].astype(str).str.strip() == pass_input.strip())
            ]
            
            if not match.empty:
                st.session_state.authenticated = True
                st.session_state.team_id = team_input.strip().upper()
                st.sidebar.success(f"✅ ¡Bienvenido {st.session_state.team_id}!")
                st.rerun()
            else:
                st.sidebar.error("❌ Equipo o contraseña incorrectos.")
        except Exception as e:
            st.sidebar.error(f"Error al validar credenciales: {e}")
            
    st.info("👈 Ingresa tu número de equipo y contraseña en la barra lateral para comenzar la práctica.")
    st.stop()

else:
    st.sidebar.success(f"🟢 Sesión activa: **{st.session_state.team_id}**")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.session_state.team_id = ""
        st.session_state.messages = []
        st.session_state.question_timestamps = []
        st.rerun()

# Botón de Descarga del Manual
if os.path.exists("Practica_2_Control_de_Modulo_Relevador_de_5V.pdf"):
    with open("Practica_2_Control_de_Modulo_Relevador_de_5V.pdf", "rb") as pdf_file:
        st.sidebar.download_button(
            label="📄 Descargar Manual PDF",
            data=pdf_file,
            file_name="Practica_2_Relevador.pdf",
            mime="application/pdf"
        )

# 5. CONTROL DE CUOTA / RATE LIMIT (Máximo 2 preguntas cada 5 minutos)
now = datetime.datetime.now()
five_minutes_ago = now - datetime.timedelta(minutes=5)

# Filtrar timestamps anteriores a 5 minutos
st.session_state.question_timestamps = [
    t for t in st.session_state.question_timestamps if t > five_minutes_ago
]

questions_used = len(st.session_state.question_timestamps)
st.sidebar.markdown("---")
st.sidebar.subheader("⏱️ Límite de Consultas")
st.sidebar.write(f"Preguntas realizadas en esta ventana (5 min): **{questions_used} / 2**")

# 6. PROMPT MAESTRO DE LA PRÁCTICA 2
SYSTEM_INSTRUCTION = """
[ROL Y PERFIL]
Eres "Tutor-Electro", un tutor pedagógico de laboratorio estricto y analítico. Tu objetivo es guiar al estudiante de forma SECUENCIAL a través de la "Práctica 2: Control de Módulo Relevador de 5V".

[REGLA DE ORO DE NAVEGACIÓN SECUENCIAL]
- NUNCA proporciones las respuestas de pasos futuros ni permitas al estudiante avanzar al siguiente paso sin haber validado y confirmado satisfactoriamente el paso actual.
- Avanza EXACTAMENTE UN PASO A LA VEZ.

[SECUENCIA DE PASOS Y CHECKPOINTS]
PASO 1: Carga del Código vía USB (Pin 8, delays 1000ms). Pregunta si la carga fue exitosa en el IDE.
PASO 2: PROTOCOLO OBLIGATORIO DE DESCONEXIÓN USB. Exige confirmación explícita de haber desconectado físicamente el USB de la PC antes de continuar.
PASO 3: Montaje de Fuente Regulada en Protoboard (MB102 a 5V con eliminador 12V/9V). Pregunta configuración de jumpers.
PASO 4: Cableado del Circuito desenergizado (VCC, GND, IN a Pin 8, 5V Arduino a 5V Proto, GND Arduino a GND Proto). Pide al alumno describir conexiones.
PASO 5: Energización y Verificación. Pedir verificar si el LED PWR del relevador está encendido constante.
PASO 6: Validación de Conmutación. Verificar si el LED de estado parpadea cada 1s y si se escucha el 'clic' del conmutador interno.
PASO 7: Cuestionario Final (Hacer preguntas teóricas de 1 en 1).

[ESTILO Y TONO]
- Profesional, riguroso con la seguridad eléctrica, paciente y alentador.
"""

# 7. HISTORIAL DE CHAT
if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_msg = (
        f"¡Hola **{st.session_state.team_id}**! Bienvenidos a la **Práctica 2: Control de Módulo Relevador de 5V**.\n\n"
        "Tengan en cuenta que **solo pueden realizar máximo 2 preguntas cada 5 minutos**, "
        "así que formulen sus dudas con precisión y aprovechen el tiempo intermedio para armar las conexiones físicamente.\n\n"
        "--- \n"
        "### 🟢 PASO 1: Carga del Código vía USB\n"
        "1. Conecten su Arduino UNO a la computadora vía USB.\n"
        "2. En Arduino IDE, carguen el código para conmutar el **Pin Digital 8** (HIGH / LOW con delay de 1000ms).\n"
        "3. Seleccionen la placa y puerto activo y suban el sketch.\n\n"
        "**¿Lograron compilar y subir el programa al Arduino sin errores?**"
    )
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 8. ENTRADA DE TEXTO Y EVALUACIÓN DE LÍMITE
if prompt := st.chat_input("Escribe tu consulta o respuesta aquí..."):

    # Verificar si alcanzaron el límite de 2 preguntas en 5 minutos
    if len(st.session_state.question_timestamps) >= 2:
        oldest_question_time = min(st.session_state.question_timestamps)
        next_available_time = oldest_question_time + datetime.timedelta(minutes=5)
        time_left = next_available_time - datetime.datetime.now()
        
        seconds_left = max(1, int(time_left.total_seconds()))
        minutes_display = seconds_left // 60
        seconds_display = seconds_left % 60

        st.warning(
            f"⏳ **Límite de tiempo alcanzado para {st.session_state.team_id}.**\n\n"
            f"Han enviado 2 preguntas en los últimos 5 minutos. "
            f"Aprovechen este tiempo para revisar su circuito en el protoboard. "
            f"Podrán enviar la siguiente pregunta en **{minutes_display}m {seconds_display}s**."
        )
        st.stop()

    # Guardar timestamp de la pregunta autorizada
    st.session_state.question_timestamps.append(datetime.datetime.now())

    # Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Preparar el contexto histórico para la API
    formatted_contents = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part.from_text(text=m["content"])]
        ) for m in st.session_state.messages
    ]

    # Respuesta de Gemini
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=formatted_contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2
            )
        )

        bot_reply = response.text
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        
        with st.chat_message("assistant"):
            st.markdown(bot_reply)

        # Registro en Google Sheets (Pestaña Bitacora)
        try:
            existing_data = conn.read(worksheet="Bitacora", ttl=0)
            new_log = pd.DataFrame([{
                "timestamp": str(datetime.datetime.now()),
                "practica": "Practica 2 - Relevador",
                "student_id": st.session_state.team_id,
                "student_name": st.session_state.team_id,
                "user_prompt": prompt,
                "bot_response": bot_reply
            }])
            updated_data = pd.concat([existing_data, new_log], ignore_index=True)
            conn.update(worksheet="Bitacora", data=updated_data)
        except Exception as sheet_err:
            st.error(f"⚠️ Error al guardar en la bitácora: {sheet_err}")

    except Exception as e:
        st.error(f"Error de comunicación con la API: {e}")