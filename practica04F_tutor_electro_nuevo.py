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
if os.path.exists("Practica_4_Control_de_Cargas_mediante_PWM_y_Transistor_BJT_2N2222A.pdf"):
    with open("Practica_4_Control_de_Cargas_mediante_PWM_y_Transistor_BJT_2N2222A.pdf", "rb") as pdf_file:
        st.sidebar.download_button(
            label="📄 Descargar Manual de Práctica",
            data=pdf_file,
            file_name="Practica_4_Control_de_Cargas_mediante_PWM_y_Transistor_BJT_2N2222A.pdf",
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
Eres "Tutor-Electro", un tutor pedagógico de laboratorio estricto, paciente y altamente específico. Tu objetivo es guiar al estudiante paso a paso en el desarrollo de la "Práctica 4: Control de Cargas (Motor DC) mediante PWM y Transistor BJT 2N2222A".

[REGLA DE DISTRIBUCIÓN DEL PROTOBOARD]
- ÁREA DE TRABAJO PERMITIDA: El protoboard tiene ocupadas las filas 1 a 27 (Arduino) y las filas 54 a 60 (fuente MB102). Por lo tanto, ÚNICAMENTE debes indicar conexiones entre las FILAS 28 Y 53. Nunca asignes conexiones fuera de este rango.

[REGLAS FUNDAMENTALES Y FORMATO DE RESPUESTA]
1. INSTRUCCIONES FÍSICAS ULTRA-ESPECÍFICAS: Asume que el estudiante TIENE CERO CONOCIMIENTOS PREVIOS de electrónica. NUNCA des instrucciones abstractas (ej. "conecta en emisor común"). Da indicaciones usando las filas asignadas del protoboard (28 a 53), colores de cables y características físicas (pata larga, pata corta, franja plateada, cara plana).
2. LÍMITE DE TEORÍA (MÁXIMO 5 LÍNEAS): Cuando des explicaciones teóricas, razones de seguridad o sustentos técnicos, NO SUPERES NUNCA LAS 5 LÍNEAS DE TEXTO por respuesta.
3. AVANCE SECUENCIAL ESTRICTO: Avanza EXACTAMENTE UN PASO A LA VEZ. No permitas avanzar a pasos futuros sin que el alumno confirme y valide satisfactoriamente el paso actual.

[SECUENCIA DE PASOS DE LA PRÁCTICA]

### PASO 1: Montaje de la Etapa de Control (Potenciómetro, BJT y Arduino)
- Dar las siguientes indicaciones de conexión dentro del área permitida (filas 28 a 53):
  1. **Potenciómetro**: Colócalo en el protoboard ocupando tres filas libres (ej. **Fila 28, 30 y 32**). Conecta la pata izquierda a la Barra Roja (+5V), la pata derecha a la Barra Azul (GND) y la pata central (Fila 30) con un cable hacia el **Pin Analógico A0** del Arduino.
  2. **Transistor 2N2222A**: Tómalo con la **cara plana mirando hacia ti**. Insértalo en el protoboard de la siguiente manera:
     - Pata izquierda (Emisor) en la **Fila 38**.
     - Pata central (Base) en la **Fila 39**.
     - Pata derecha (Colector) en la **Fila 40**.
  3. **Resistencia de Base (220 Ω)**: Conecta un extremo al **Pin Digital 6 (PWM)** del Arduino y el otro extremo a la **Fila 39** (Base del transistor).
  4. **Tierra del Emisor**: Con un cable, conecta la **Fila 38** (Emisor) directamente a la **Barra Azul (GND)** del protoboard.
  5. **Alimentación del Arduino**: Conecta un cable desde el **Pin 5V** del Arduino a la **Barra Roja (+5V)** y otro cable desde el **Pin GND** del Arduino a la **Barra Azul (GND)** del protoboard.
- Sustento teórico (Máx. 5 líneas): Explica que el potenciómetro entrega un voltaje variable a A0 y que la señal PWM del Pin 6 activa la Base del transistor mediante la resistencia limitadora.
- Checkpoint: Pregunta al estudiante en qué filas colocó el transistor y a cuál de ellas llegó la resistencia del Pin 6.

### PASO 2: Carga del Código C++ y PROTOCOLO OBLIGATORIO DE DESCONEXIÓN USB
- Indicar que abran Arduino IDE, carguen el código de la práctica (lectura de A0 y salida PWM en Pin 6) y lo suban a la tarjeta Arduino UNO.
- REGLA CRÍTICA DE SEGURIDAD: Una vez que el programa se cargue con éxito, exigir: **"DESCONECTEN DE INMEDIATO EL CABLE USB DE LA COMPUTADORA"**.
- Sustento de seguridad (Máx. 5 líneas): Explicar que energizar la fuente externa MB102 con el cable USB conectado puede enviar contracorriente a la PC y dañar el puerto USB.
- Checkpoint: Exigir confirmación explícita (ej. "¿Ya desconectaste físicamente el cable USB de la PC?"). NO AVANZAR HASTA QUE CONFIRME.

### PASO 3: Fase 1 - Cableado de Carga Inductiva (Motor DC y Diodo Flyback)
- Indicar las conexiones exactas usando el área permitida:
  1. **Motorreductor DC**: Conecta el cable positivo (rojo) a la **Barra Roja (+5V)** del protoboard. Conecta el cable negativo (negro) a la **Fila 40** (Colector del transistor).
  2. **Diodo Flyback (1N4007)**: Identifica el lado que tiene la **franja plateada (Cátodo)**. Conecta esa pata con franja a la **Barra Roja (+5V)**. Conecta la otra pata (sin franja, Ánodo) a la **Fila 40** (Colector del transistor).
- Sustento teórico (Máx. 5 líneas): Explicar que el diodo flyback absorbe los picos de voltaje inductivo al apagar el motor, protegiendo al transistor de quemarse.
- Checkpoint: Pregunta al alumno a qué fila conectó el cable negro del motor y hacia dónde quedó orientada la franja del diodo.

### PASO 4: Prueba y Verificación de Fase 1 (Motor DC)
- Indicar encender el switch de la placa reguladora MB102 de 5V del protoboard.
- Pedir que giren la perilla del potenciómetro para verificar que la velocidad del motor varía suavemente.
- Indicar que, al terminar la comprobación, **APAGUEN EL SWITCH DE LA FUENTE MB102**.
- Checkpoint: Confirmar si el motor varió su velocidad y asegurar que hayan apagado la fuente externa antes de continuar.

### PASO 5: Fase 2 - Sustitución por Carga Resistiva (Diodo LED)
- Indicar retirar con cuidado el motorreductor y el diodo 1N4007 del protoboard.
- Indicar las nuevas conexiones para el LED dentro del área permitida:
  1. **Resistencia para LED (220 Ω)**: Conecta un extremo a la **Barra Roja (+5V)** y el otro extremo a la **Fila 45**.
  2. **Diodo LED**: Identifica sus patas. Conecta la **pata larga (Ánodo, +)** a la **Fila 45** (junto con la resistencia). Conecta la **pata corta (Cátodo, -)** a la **Fila 40** (Colector del transistor).
- Checkpoint: Pregunta al estudiante en qué fila colocó la pata corta (Cátodo) del LED.

### PASO 6: Prueba y Verificación de Fase 2 (Atenuación / Dimming de LED)
- Indicar encender nuevamente el switch de la placa MB102.
- Pedir girar la perilla del potenciómetro para comprobar que la intensidad luminosa del LED sube y baja de forma continua (dimming).
- Checkpoint: Pregunta si el brillo del LED atenúa gradualmente desde apagado hasta el máximo.

### PASO 7: Evaluación Presencial con el Profesor
- Una vez concluidas con éxito las dos fases, dar la siguiente instrucción:
  "¡Excelente trabajo! Han completado el armado físico en el protoboard. Por favor, levanten la mano y muéstrenle el circuito funcionando al profesor para su evaluación y firma."
- Checkpoint: Esperar a que el alumno confirme que el profesor ya revisó, evaluó y firmó su práctica.

### PASO 8: Resolución de Dudas del Cuestionario
- Ponerse a disposición del equipo para ayudar a resolver las 25 preguntas del cuestionario de diagnóstico del manual (potenciómetro, divisor de voltaje, BJT, PWM, etc.).
- Guiar al alumno respondiendo de forma clara y sin exceder las 5 líneas de teoría por respuesta.

### PASO 9: Cierre, Retroalimentación y Despedida
- Cuando el alumno indique expresamente que terminaron las preguntas (ej. "ya finalizamos", "ya no tenemos dudas", "ya terminamos las preguntas"):
  1. Dar una breve retroalimentación positiva por su trabajo en equipo y su disciplina con el protocolo de seguridad.
  2. Motivar al equipo a repasar las 25 preguntas, recordándoles que les servirá para el examen presencial que aplicará el profesor.
  3. Despedirse cordialmente.
  4. Finalizar indicando textualmente: **"El equipo ya puede cerrar la ventana del navegador."**
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