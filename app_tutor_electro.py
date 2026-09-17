import streamlit as st
import google.generativeai as genai
import datetime
import json
import os

# 1. Configuración de la API Key desde Variable de Entorno
# Busca en el entorno o en los secretos locales de Streamlit (.streamlit/secrets.toml)
API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("⚠️ No se encontró la variable de entorno 'GEMINI_API_KEY'. Configúrala antes de iniciar la app.")
    st.stop()

genai.configure(api_key=API_KEY)

# 2. Configuración básica de la página
st.set_page_config(page_title="Tutor-Electro", page_icon="⚡", layout="wide")
st.title("⚡ Tutor-Electro: Asistente para Laboratorio de Arduino")
st.caption("Sistema de apoyo pedagógico para armado de circuitos en Protoboard")

# 3. Barra lateral: Solo datos del Estudiante
st.sidebar.header("📋 Datos del Estudiante")
student_id = st.sidebar.text_input("Matrícula / ID de Alumno:")
student_name = st.sidebar.text_input("Nombre completo:")

# 4. Prompt Maestro (Instrucciones del Sistema)
SYSTEM_INSTRUCTION = """
[ROL Y PERFIL]
Eres "Tutor-Electro", un asistente pedagógico de nivel universitario especializado en Electrónica Básica y microcontroladores Arduino. Tu objetivo es guiar a los estudiantes de ingeniería para que aprendan a conectar circuitos físicos en un protoboard de forma analítica, estructurada y segura.

[PRINCIPIOS PEDAGÓGICOS - MÉTODO SOCRÁTICO]
1. No entregues el circuito completo ni la solución directa de entrada.
2. Guía al estudiante paso a paso mediante preguntas orientadoras para que comprenda la matriz de nodos (filas, columnas y buses de alimentación) del protoboard.
3. Ante la duda del alumno, explica el "porqué" físico de las conexiones (mallas, nodos, caída de tensión) antes del "cómo".
4. Tras cada paso de conexionado, realiza una pregunta corta de comprobación (ej. "¿En qué fila estás cerrando la malla del circuito?").

[REGLAS DE CONEXIÓN EN PROTOBOARD]
* Sé extremadamente preciso con la nomenclatura física del protoboard (ej. "Columna 15, pista A" o "Riel positivo +").
* Distingue claramente entre pines de Arduino (D13, A0, 5V, GND) y pistas del protoboard.

[PROTOCOLO DE SEGURIDAD ELÉCTRICA - IMPRESCINDIBLE]
* NUNCA le pidas o permitas al usuario conectar el cable USB del Arduino a la computadora sin antes ejecutar el "Check-list de Seguridad" (ausencia de cortocircuito, polaridad de componentes y resistencias adecuadas).

[DEPURACIÓN Y DIAGNÓSTICO DE ERRORES (DEBUGGING)]
* Si el estudiante reporta fallas, aplica un flujo de diagnóstico guiado.

[ESTILO Y TONO]
* Tono profesional, paciente y motivador. Usa negritas para resaltar pines, valores y componentes clave.
"""

# 5. Inicialización del Modelo Gemini
model = genai.GenerativeModel(
    model_name="gemini-pro-latest",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config={"temperature": 0.3}
)

# 6. Gestión del Estado del Chat
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. Interacción del Usuario y Registro de Datos
if prompt := st.chat_input("Escribe tu duda o avance de tu circuito aquí..."):
    if not student_id:
        st.warning("⚠️ Por favor ingresa tu Matrícula / ID en la barra lateral antes de chatear.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = st.session_state.chat_session.send_message(prompt)
    
    st.session_state.messages.append({"role": "assistant", "content": response.text})
    with st.chat_message("assistant"):
        st.markdown(response.text)

    # Guardado de logs en servidor
    os.makedirs("research_logs", exist_ok=True)
    file_path = f"research_logs/log_{student_id}.json"
    
    log_entry = {
        "timestamp": str(datetime.datetime.now()),
        "student_id": student_id,
        "student_name": student_name,
        "user_prompt": prompt,
        "bot_response": response.text
    }
    
    existing_logs = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                existing_logs = json.load(f)
            except json.JSONDecodeError:
                existing_logs = []
                
    existing_logs.append(log_entry)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(existing_logs, f, ensure_ascii=False, indent=2)