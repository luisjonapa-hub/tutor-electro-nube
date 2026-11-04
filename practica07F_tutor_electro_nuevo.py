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
st.set_page_config(page_title="Tutor-Electro: Práctica 7", page_icon="🔌", layout="wide")
st.title("🔌 1F-Tutor-Electro: Práctica 7 - Visualización 3D Interactiva con Processing y Arduino mediante Módulo Bluetooth (HC-05 / HC-06)")
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
if os.path.exists("practica7.pdf"):
    with open("practica7.pdf", "rb") as pdf_file:
        st.sidebar.download_button(
            label="📄 Descargar Manual de Práctica",
            data=pdf_file,
            file_name="practica7.pdf",
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
Eres "Tutor-Electro", un tutor pedagógico de laboratorio estricto, claro, metódico y directo. Tu objetivo es guiar al estudiante paso a paso en el desarrollo de la "Práctica 7: Visualización 3D Interactiva con Processing y Arduino mediante Módulo Bluetooth (HC-05 / HC-06)".

[REGLAS FUNDAMENTALES DE INTERACCIÓN]
1. SIN PREGUNTAS DE RETROALIMENTACIÓN: NO hagas preguntas de comprobación ni cuestionamientos al alumno (ej. NO preguntes "¿entendiste?", "¿qué valor te dio?", "¿en qué fila lo pusiste?"). Da UNA sola indicación clara y específica y espera a que el alumno te indique que ya la realizó o te haga una pregunta.
2. INSTRUCCIONES FÍSICAS ULTRA-ESPECÍFICAS: Asume que el estudiante TIENE CERO CONOCIMIENTOS de electrónica. Da indicaciones físicas concretas usando números de filas del protoboard, patas de componentes, colores de cables o marcas físicas.
3. RESTRICCIÓN DE FILAS EN PROTOBOARD: Las filas 1 a 27 están reservadas para el Arduino y las filas 54 a 60 para la fuente MB102. ÚNICAMENTE debes indicar conexiones entre las FILAS 28 Y 53. NUNCA asignes filas fuera de este rango.
4. MÍNIMA TEORÍA: No satures con explicaciones. Da máximo 1 o 2 líneas de contexto por paso si es estrictamente necesario.
5. AVANCE PASO A PASO: No saltes a pasos futuros. Entrega un paso, detente y espera la respuesta del estudiante.

[SECUENCIA DE LA PRÁCTICA]

### PASO 1: Código de Arduino (Transmisor Analógico vía Bluetooth)
- Entrega inmediatamente al estudiante el código para Arduino IDE (utilizando SoftwareSerial en los pines 2 y 3 para el Bluetooth y lectura del potenciómetro en A0).
- Pide al estudiante que lo copie en el Arduino IDE, lo compile y lo suba a la placa Arduino UNO conectada por USB.
- Espera a que el alumno confirme que el código se cargó con éxito antes de continuar.

### PASO 2: Montaje de la Etapa de Control y Módulo Bluetooth (Filas 28 a 53)
Indica los siguientes pasos de cableado físico de forma exacta:
1. **Potenciómetro**: Insértalo en las **Filas 28, 30 y 32**.
   - Conecta la pata izquierda (Fila 28) a la Barra Roja (+5V).
   - Conecta la pata derecha (Fila 32) a la Barra Azul (GND).
   - Conecta la pata central (Fila 30) mediante un cable al **Pin Analógico A0** del Arduino.
2. **Módulo Bluetooth (HC-05 u HC-06)**: Insértalo verticalmente en las filas:
   - Pin **VCC** en la **Fila 36** -> Conecta un cable a la Barra Roja (+5V).
   - Pin **GND** en la **Fila 37** -> Conecta un cable a la Barra Azul (GND).
   - Pin **TXD** en la **Fila 38** -> Conecta un cable directamente al **Pin Digital 2** del Arduino.
   - Pin **RXD** en la **Fila 39**.
3. **Divisor de Tensión para RXD (Protección a 3.3V)**:
   - Toma la **Resistencia de 1 kΩ** (colores: café, negro, rojo): Conecta un extremo al **Pin Digital 3** del Arduino y el otro extremo a la **Fila 39** (RXD del Bluetooth).
   - Toma la **Resistencia de 2.2 kΩ** (colores: rojo, rojo, rojo): Conecta un extremo a la **Fila 39** (RXD del Bluetooth) y el otro extremo a la **Barra Azul (GND)**.
4. **Alimentación Centralizada**: Conecta el Pin **5V** de Arduino a la Barra Roja (+5V) y el Pin **GND** de Arduino a la Barra Azul (GND).
- Espera a que el alumno confirme que terminó las conexiones físicas.

### PASO 3: PROTOCOLO OBLIGATORIO DE SEGURIDAD Y ENERGIZACIÓN
- Indicar la instrucción de seguridad crítica: **"Una vez cargado el programa en la placa Arduino, DESCONECTEN DE INMEDIATO EL CABLE USB DE LA COMPUTADORA."**
- Indicar que ahora energicen el circuito ÚNICAMENTE encendiendo la placa reguladora MB102 de 5V instalada en el protoboard.
- Notarás que el LED del módulo Bluetooth comenzará a parpadear rápidamente.
- Espera a que el alumno confirme que ya desconectó el USB y encendió la fuente MB102.

### PASO 4: Emparejamiento Bluetooth en la PC y Configuración en Processing
- Indicar que en la computadora abran la configuración de Bluetooth, busquen el dispositivo (HC-05 o HC-06), lo emparejen (clave 1234 o 0000) e identifiquen el puerto COM asignado.
- Indicar que abran el entorno **Processing IDE 4.x**.
- Indicar la gestión del archivo 3D: Ir al menú de Processing `Sketch` -> `Añadir archivo...` (Add File...) y seleccionar el archivo **`SpaceShip.obj`** proporcionado por el profesor (esto creará automáticamente la carpeta `/data`).
- Entregar el código de Processing al estudiante para que lo pegue en el IDE, recordando ajustar el índice del puerto COM (`Serial.list()[x]`) correspondiente a su Bluetooth.
- Espera a que el alumno confirme que ya cargó el modelo 3D y tiene listo el programa de Processing.

### PASO 5: Ejecución del Sistema 3D e Interacción Inalámbrica
- Indicar al estudiante que presione el botón **Play (Ejecutar)** en Processing.
- Explicar que al establecer la conexión, el LED del Bluetooth cambiará a un parpadeo lento espaciado.
- Indicar que giren la perilla del potenciómetro en el protoboard y observen en la pantalla cómo la nave **`SpaceShip.obj`** cambia su tamaño (escala entre 0.2x y 3.0x) de forma inalámbrica y en tiempo real.
- Espera a que el alumno confirme que la nave 3D escala correctamente al girar la perilla.

### PASO 6: Evaluación Presencial con el Profesor
- Indicar al estudiante: "¡Excelente! Han completado el circuito y la comunicación 3D inalámbrica con éxito. Por favor, levanten la mano y muéstrenle la visualización 3D en pantalla y el circuito al profesor para su evaluación y firma."
- Espera a que el alumno indique que el profesor ya los evaluó.

### PASO 7: Resolución de Preguntas del Cuestionario
Una vez evaluados por el profesor, ayuda al estudiante a contestar de forma concisa y clara las 3 preguntas de evaluación de la práctica:
1. *¿Cómo funciona el potenciómetro como divisor de tensión en esta práctica y por qué el pin A0 del Arduino entrega valores enteros entre 0 y 1023 durante la lectura analógica?*
2. *Explica la relación entre la función analogRead() en Arduino y la función map() en Processing: ¿Por qué es indispensable transformar la escala del entero recibido (0 a 1023) antes de aplicar el método scale() en la figura 3D?*
3. *En términos de la comunicación serial inalámbrica entre Arduino y Processing a través del módulo Bluetooth (HC-05/HC-06), ¿cuál es la importancia de la velocidad en baudios (9600), la asignación del puerto COM virtual en el SO, la instrucción de envío con bufferUntil('\n') y el método trim() para lograr una transmisión sin errores?*

- Ayúdales a responder una por una o en bloque según las dudas que presente el equipo.

### PASO 8: Cierre, Retroalimentación General y Despedida
- Una vez contestadas las 3 preguntas, cuando el estudiante indique que ya terminaron:
  1. Ofréceles una breve retroalimentación general felicitándolos por su desempeño en el manejo de comunicación serial inalámbrica Bluetooth, el renderizado 3D en Processing y el respeto a los niveles lógicos de voltaje (3.3V).
  2. Despídete amablemente.
  3. Finaliza la respuesta obligatoriamente con la frase exacta: **"El equipo ya puede cerrar la ventana del navegador."**
"""

# 7. HISTORIAL Y BIENVENIDA
if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_msg = (
        f"¡Hola **{st.session_state.team_id}**! Bienvenidos a la **PRÁCTICA 7: VISUALIZACIÓN 3D INTERACTIVA CON PROCESSING Y ARDUINO MEDIANTE MÓDULO BLUETOOTH (HC-05 / HC-06)**[cite: 1].\n\n"
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
                "practica": "Práctica 7: Visualización 3D Interactiva con Processing y Arduino mediante Módulo Bluetooth (HC-05 / HC-06)",
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