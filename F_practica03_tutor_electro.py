import streamlit as st
from google import genai
from google.genai import types
import datetime
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import os

# 1. Configuración de la API Key desde Variable de Entorno / Secrets
API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("⚠️ No se encontró la variable de entorno 'GEMINI_API_KEY'. Configúrala en los Secrets.")
    st.stop()

# Cliente del SDK actualizado
client = genai.Client(api_key=API_KEY)

# 2. Configuración de página
st.set_page_config(page_title="Tutor-Electro: Práctica 3", page_icon="🔌", layout="wide")
st.title("🔌 1F-Tutor-Electro: Práctica 3 - Módulo Relevador de 5V con Motor")
st.caption("Asistente pedagógico secuencial paso a paso")

# 3. Conexión a Google Sheets e Inicialización del Estado de Sesión
conn = st.connection("gsheets", type=GSheetsConnection)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "team_id" not in st.session_state:
    st.session_state.team_id = ""
if "question_timestamps" not in st.session_state:
    st.session_state.question_timestamps = []

# 4. AUTENTICACIÓN (LOGIN DE EQUIPOS CONTRA LA PESTAÑA 'Credenciales')
st.sidebar.header("🔐 Acceso de Equipos")

if not st.session_state.authenticated:
    team_input = st.sidebar.text_input("Número de Equipo (ej. Equipo F1):")
    pass_input = st.sidebar.text_input("Contraseña:", type="password")
    login_btn = st.sidebar.button("Iniciar Sesión")

    if login_btn:
        try:
            # Leer credenciales desde la pestaña 'Credenciales' de Google Sheets
            creds_df = conn.read(worksheet="Credenciales_F", ttl=0)
            
            # Buscar coincidencia exacta
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
            st.sidebar.error(f"⚠️ Error al consultar la base de datos de credenciales: {e}")
            
    st.info("👈 Por favor ingresa tu número de equipo y contraseña en la barra lateral para continuar.")
    st.stop()

else:
    st.sidebar.success(f"🟢 Sesión activa: **{st.session_state.team_id}**")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.session_state.team_id = ""
        st.session_state.messages = []
        st.session_state.question_timestamps = []
        st.rerun()

# Descarga del manual PDF (Protegido contra FileNotFoundError)
if os.path.exists("Practica_2_Control_de_Modulo_Relevador_de_5V.pdf"):
    with open("Practica_2_Control_de_Modulo_Relevador_de_5V.pdf", "rb") as pdf_file:
        st.sidebar.download_button(
            label="📄 Descargar Manual de Práctica",
            data=pdf_file,
            file_name="Practica_2_Relevador.pdf",
            mime="application/pdf"
        )

# 5. CONTROL DE TASA / RATE LIMIT (Máximo 2 preguntas en una ventana de 5 minutos)
now = datetime.datetime.now()
five_minutes_ago = now - datetime.timedelta(minutes=5)

# Filtrar timestamps de preguntas realizadas hace menos de 5 minutos
st.session_state.question_timestamps = [
    t for t in st.session_state.question_timestamps if t > five_minutes_ago
]

questions_used = len(st.session_state.question_timestamps)
st.sidebar.markdown("---")
st.sidebar.subheader("⏱️ Límite de Consultas")
st.sidebar.write(f"Preguntas realizadas (últimos 5 min): **{questions_used} / 2**")

# 6. PROMPT MAESTRO (INSTRUCCIONES DEL SISTEMA)
SYSTEM_INSTRUCTION = """
[ROL Y PERFIL]
Eres "Tutor-Electro", un tutor pedagógico de laboratorio estricto y analítico. Tu objetivo es guiar al estudiante de forma SECUENCIAL a través de la "Práctica 3: Control de Módulo Relevador de 5V con Motor"[cite: 1].

[REGLA DE ORO DE NAVEGACIÓN SECUENCIAL]
- NUNCA proporciones las respuestas de pasos futuros ni permitas al estudiante avanzar al siguiente paso sin haber validado y confirmado satisfactoriamente el paso actual.
- Avanza EXACTAMENTE UN PASO A LA VEZ. Tras cada respuesta del alumno, evalúa si comprendió y ejecutó la instrucción. Si es correcto, confírmalo y plantea la pregunta o instrucción del PASO SIGUIENTE. Si es incorrecto, mantén al alumno en el paso actual orientándolo socráticamente.

[SECUENCIA DE PASOS Y CHECKPOINTS DE EVALUACIÓN]
PASO 1: Carga del Código vía USB (Pin 8, delays 1000ms)[cite: 1]. Pregunta si la carga fue exitosa en el IDE[cite: 1].
PASO 2: PROTOCOLO OBLIGATORIO DE DESCONEXIÓN USB[cite: 1]. Exige confirmación explícita de haber desconectado físicamente el USB de la PC antes de continuar[cite: 1].
PASO 3: Montaje de Fuente Regulada en Protoboard desde la línea 55 a la 60 del protoboard(MB102 a 5V con eliminador 12V/9V)[cite: 1]. Pregunta configuración de jumpers[cite: 1].
PASO 4: Cableado del Circuito desenergizado. En el protoboard solo se podrán usar las líneas de la 27 a la 53, ya que las líneas 1 a 27 estarán ocupadas por el arduino y de la 54 a la 60 estarán ocupadas por la placa MB102 (VCC, GND, IN a Pin 8, 5V Arduino a 5V Proto, GND Arduino a GND Proto)[cite: 1]. Pide al alumno describir conexiones[cite: 1].
PASO 5: Energización y Verificación[cite: 1]. Pedir verificar si el LED PWR del relevador está encendido constante[cite: 1].
PASO 6: Validación de Conmutación[cite: 1]. Verificar si el LED de estado parpadea cada 1s y si se escucha el 'clic' del conmutador interno[cite: 1].
PASO 7: Pedir que el alumno conecte el motor con un diodo de protección a la salida del relevador
PASO 8: Cuestionario Final (Hacer preguntas teóricas de 1 en 1)[cite: 1].

[ESTILO Y TONO]
- Profesional, riguroso con la seguridad eléctrica, paciente y alentador.
"""

# 7. HISTORIAL Y BIENVENIDA
if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_msg = (
        f"¡Hola **{st.session_state.team_id}**! Bienvenidos a la **Práctica 3: Control de Módulo Relevador de 5V con Motor**[cite: 1].\n\n"
        "Para garantizar la seguridad de sus componentes y el aprendizaje correcto, "
        "iremos paso a paso. **No podremos avanzar sin haber confirmado el paso previo**[cite: 1].\n\n"
        "⚠️ **Importante:** Disponen de un máximo de **2 preguntas cada 5 minutos**. Aprovechen el tiempo entre preguntas para armar y revisar las conexiones físicas.\n\n"
        "--- \n"
        "### 🟢 PASO 1: Carga del Código vía USB\n"
        "1. Conecten su Arduino UNO a la computadora mediante el cable USB[cite: 1].\n"
        "2. En el Arduino IDE, introduzcan el código para conmutar el **Pin Digital 8** en ALTO y BAJO con intervalos de 1000 ms[cite: 1].\n"
        "3. Seleccionen la placa *Arduino Uno*, el puerto COM activo y suban el programa (sketch)[cite: 1].\n\n"
        "**¿Lograron compilar y subir el programa al Arduino sin errores?**[cite: 1]"
    )
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

# Dibujar chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 8. ENTRADA DEL USUARIO, EVALUACIÓN DE TIEMPO Y REGISTRO EN GOOGLE SHEETS
if prompt := st.chat_input("Escribe tu duda o avance de tu circuito aquí..."):

    # Verificar si alcanzaron el límite de 2 preguntas en 5 minutos
    if len(st.session_state.question_timestamps) >= 2:
        oldest_question = min(st.session_state.question_timestamps)
        next_available = oldest_question + datetime.timedelta(minutes=5)
        seconds_remaining = max(1, int((next_available - datetime.datetime.now()).total_seconds()))
        mins = seconds_remaining // 60
        secs = seconds_remaining % 60

        st.warning(
            f"⏳ **Límite de tiempo alcanzado para el {st.session_state.team_id}.**\n\n"
            f"Han enviado 2 preguntas en los últimos 5 minutos. "
            f"Aprovechen este tiempo para armar o verificar su circuito. "
            f"Podrán enviar la siguiente consulta en **{mins}m {secs}s**."
        )
        st.stop()

    # Guardar hora de la pregunta autorizada
    st.session_state.question_timestamps.append(datetime.datetime.now())

    # Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Contexto para Gemini SDK
    formatted_contents = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part.from_text(text=m["content"])]
        ) for m in st.session_state.messages
    ]

    # Consulta a la API con gemini-1.5-flash
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

        # Guardado en Google Sheets (Pestaña "Bitacora")
        try:
            existing_data = conn.read(worksheet="Bitacora", ttl=0)

            new_log = pd.DataFrame([{
                "timestamp": str(datetime.datetime.now()),
                "practica": "Práctica 2: Control de Módulo Relevador de 5V",
                "student_id": st.session_state.team_id,
                "student_name": st.session_state.team_id,
                "user_prompt": prompt,
                "bot_response": bot_reply
            }])

            updated_data = pd.concat([existing_data, new_log], ignore_index=True)
            conn.update(worksheet="Bitacora", data=updated_data)

        except Exception as sheet_err:
            st.error(f"⚠️ Error al guardar registro en la pestaña 'Bitacora': {sheet_err}")

    except Exception as e:
        st.error(f"Error de comunicación con Gemini: {e}")