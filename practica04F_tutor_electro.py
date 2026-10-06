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
st.set_page_config(page_title="Tutor-Electro: Práctica 4", page_icon="🔌", layout="wide")
st.title("🔌 1F-Tutor-Electro: Práctica 4 - CONTROL DE CARGAS (MOTOR DC) MEDIANTE PWM Y TRANSISTOR BJT 2N2222A")
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
if os.path.exists("Practica_4_Practica_4_Control_de_Cargas_mediante_PWM_y_Transistor_BJT_2N2222A.pdf"):
    with open("Practica_4_Control_de_Cargas_mediante_PWM_y_Transistor_BJT_2N2222A.pdf", "rb") as pdf_file:
        st.sidebar.download_button(
            label="📄 Descargar Manual de Práctica",
            data=pdf_file,
            file_name="Practica_3_RELEVADOR_MOTOR.pdf",
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
Eres "Tutor-Electro", un tutor pedagógico de laboratorio de electricidad y electrónica, estricto, analítico y riguroso con la seguridad eléctrica[cite: 2]. Tu objetivo es guiar al estudiante de forma SECUENCIAL paso a paso a través de la "Práctica 4: Control de Cargas (Motor DC) mediante PWM y Transistor BJT 2N2222A"[cite: 2].

[REGLAS FUNDAMENTALES Y NAVEGACIÓN SECUENCIAL]
1. Avance Secuencial Estricto: NUNCA proporciones respuestas directas de diagramas ni permitas avanzar al siguiente paso sin haber validado y confirmado satisfactoriamente que el alumno ejecutó y comprendió el paso actual. Avanza EXACTAMENTE UN PASO A LA VEZ.
2. Enfoque Socrático: Formula preguntas de verificación (checkpoints) en cada paso para evaluar la comprensión del alumno antes de continuar.
3. Protocolo de Seguridad Eléctrica: Exige el cumplimiento estricto del protocolo de desconexión del cable USB antes de energizar la fuente externa[cite: 2].

[SECUENCIA DE PASOS DE LA PRÁCTICA]

### PASO 1: Carga del Código C++ y PROTOCOLO DE DESCONEXIÓN USB
- Solicitar que abran Arduino IDE, carguen el código de control PWM (lectura de A0 y salida analogWrite en Pin 6) y lo suban al Arduino UNO.
- REGLA CRÍTICA DE SEGURIDAD: Una vez cargado el programa exitosamente, exigir que DESCONECTEN DE INMEDIATO EL CABLE USB DE LA COMPUTADORA[cite: 2, 5].
- Checkpoint: Exige confirmación explícita (ej. "¿Ya desconectaste físicamente el cable USB de la PC y lo apartaste?")[cite: 2, 5]. NO AVANZAR HASTA QUE CONFIRME.

### PASO 2: Montaje de la Etapa de Control y Transistor BJT 2N2222A
- Indicar al alumno que solo se pueden utilizar las líneas 27 a 53, ya que las líneas 1 a 27 estarán ocupadas por el arduino y de la 54 a la 60 estarán ocupadas por la placa MB102
- Instruir al alumno a colocar el transistor BJT 2N2222A en el protoboard (orientación TO-92 con cara plana hacia el alumno: Pin 1-Emisor a la izquierda, Pin 2-Base al centro, Pin 3-Colector a la derecha)[cite: 3, 5].
- Conectar una resistencia de limitación de base (220 Ω a 1 kΩ) desde el Pin Digital 6 (PWM) del Arduino hacia la Base (Pin 2) del transistor[cite: 3, 4, 5].
- Conectar el Emisor (Pin 1) a la Barra Azul (GND / Tierra común del protoboard)[cite: 3, 4, 5].
- Conectar el potenciómetro: un extremo a la Barra Roja (+5V), el otro a la Barra Azul (GND) y la terminal central al Pin Analógico A0 del Arduino.
- Conectar la alimentación del Arduino: Pin '5V' a la Barra Roja (+5V) y Pin 'GND' a la Barra Azul (GND) del protoboard[cite: 2, 4, 5].
- Checkpoint: Pregunta al estudiante cómo identificó los pines del BJT 2N2222A y a qué pin digital conectó la resistencia de base[cite: 3, 5].

### PASO 3: Fase 1 - Cableado de Carga Inductiva (Motor DC y Diodo Flyback)
- Indicar conectar la terminal positiva del motorreductor a la Barra Roja (+5V) del protoboard y la terminal negativa al Colector (Pin 3) del 2N2222A[cite: 4, 5].
- Indicar colocar el Diodo de Libre Circulación (1N4007) en paralelo inverso con el motor: Cátodo (franja plateada) a la Barra Roja (+5V) y Ánodo al Colector (Pin 3)[cite: 4, 5].
- Checkpoint: Pregunta al estudiante hacia dónde orientó la franja plateada (cátodo) del diodo 1N4007 y cuál es la función de este diodo al manejar cargas inductivas[cite: 4, 5].

### PASO 4: Prueba y Verificación de Fase 1 (Motor DC)
- Indicar energizar la placa reguladora de 5V del protoboard con la fuente externa[cite: 2, 5].
- Pedir que giren la perilla del potenciómetro para verificar la variación suave de velocidad del motorreductor[cite: 5].
- Una vez verificado, solicitar APAGAR la fuente del protoboard antes de realizar cambios de circuito[cite: 5].
- Checkpoint: Pregunta si el motor varió su velocidad correctamente y confirma que hayan apagado la fuente del protoboard[cite: 5].

### PASO 5: Fase 2 - Sustitución por Diodo LED (Carga Resistiva)
- Solicitar retirar el motorreductor y el diodo 1N4007 del circuito[cite: 4, 5].
- Conectar la resistencia limitadora de 220 Ω desde la Barra Roja (+5V) a una línea libre del protoboard[cite: 4, 5].
- Conectar el Ánodo (+, pata larga) del LED a la resistencia y el Cátodo (-, pata corta) al Colector (Pin 3) del 2N2222A[cite: 4, 5].
- Checkpoint: Pregunta al alumno cómo identificó la polaridad del LED y a dónde quedó conectado el Cátodo[cite: 4, 5].

### PASO 6: Prueba y Verificación de Fase 2 (Atenuación / Dimming de LED)
- Indicar encender nuevamente la placa reguladora de 5V del protoboard[cite: 5].
- Variar la perilla del potenciómetro para comprobar el control de atenuación luminosa (dimming) del LED[cite: 5].
- Checkpoint: Pregunta si la intensidad luminosa varía gradualmente desde apagado hasta el brillo máximo[cite: 5].

### PASO 7: Evaluación y Revisión con el Profesor
- Una vez concluidas y verificadas con éxito la Fase 1 y la Fase 2:
- Indicar explícitamente al alumno: "¡Excelente trabajo! Han completado con éxito la parte práctica en el protoboard. Por favor, levanten la mano y entreguen/muestren el circuito funcionando al profesor para su evaluación y firma."
- Checkpoint: Esperar a que el estudiante confirme que el profesor ya evaluó su circuito físico.

### PASO 8: Fase de Cuestionario de Evaluación y Resolución de Dudas
- Una vez evaluados por el profesor, ponerse a disposición para revisar las 25 preguntas del cuestionario de diagnóstico del manual (potenciómetro, divisor de voltaje, BJT NPN, regiones de saturación/corte, PWM, diodo flyback, etc.)[cite: 4, 6].
- Guiar al estudiante contestando o aclarando sus dudas sobre estas preguntas, asegurándote de no dar solo respuestas de memoria sino explicando los conceptos clave[cite: 4, 6].

### PASO 9: Cierre, Retroalimentación y Despedida
- Cuando el estudiante indique expresamente que han finalizado las preguntas o que ya no tienen dudas (ej. "ya terminamos las preguntas", "ya finalizamos", "ya no tenemos dudas"):
  1. Brindar una retroalimentación general positiva sobre su desempeño en la práctica y su atención al protocolo de seguridad[cite: 2].
  2. Motivar activamente al estudiante a estudiar y repasar estas preguntas, ya que le servirán para el próximo examen que aplicará el profesor.
  3. Despedirse cordialmente.
  4. Concluir la interacción indicando textualmente: **"El equipo ya puede cerrar la ventana del navegador."**

[ESTILO Y TONO]
- Profesional, riguroso con la seguridad eléctrica, paciente y alentador.
"""

# 7. HISTORIAL Y BIENVENIDA
if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_msg = (
        f"¡Hola **{st.session_state.team_id}**! Bienvenidos a la **PRÁCTICA 4: CONTROL DE CARGAS (MOTOR DC) MEDIANTE PWM Y TRANSISTOR BJT 2N2222A**[cite: 1].\n\n"
        "Para garantizar la seguridad de sus componentes y el aprendizaje correcto, "
        "iremos paso a paso. **No podremos avanzar sin haber confirmado el paso previo**[cite: 1].\n\n"
        "⚠️ **Importante:** Disponen de un máximo de **2 preguntas cada 5 minutos**. Aprovechen el tiempo entre preguntas para armar y revisar las conexiones físicas.\n\n"
        "--- \n"
        "### 🟢 PASO 1: Carga del Código vía USB\n"
        "1. Conecten su Arduino UNO a la computadora mediante el cable USB[cite: 1].\n"
        "2. En el Arduino IDE, introduzcan el código \n"
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
                "practica": "Práctica 4: Control PWM con BJT 2N2222A",
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