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
st.set_page_config(page_title="Tutor-Electro: Práctica 9 - Control electrónico para videojuegos", page_icon="🔌", layout="wide")
st.title("🔌 1F-Tutor-Electro: Práctica 9 - Control electrónico para videojuegos")
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
    team_input = st.sidebar.text_input("Número de Equipo (ej. Equipo H1):")
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
if os.path.exists("practica9.pdf"):
    with open("practica9.pdf", "rb") as pdf_file:
        st.sidebar.download_button(
            label="📄 Descargar Manual de Práctica",
            data=pdf_file,
            file_name="practica9.pdf",
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
Eres "Tutor-Electro", un tutor pedagógico de laboratorio estricto, metódico, directo y paciente. Tu objetivo es guiar al estudiante paso a paso en el desarrollo de la "Práctica 9: Simulador de Vuelo e Interacción Inercial con MPU-6050 (I2C), Joystick y Processing vía Bluetooth (HC-05 / HC-06)".

[REGLAS FUNDAMENTALES Y FORMATO DE INTERACCIÓN]
1. PROHIBIDO HACER PREGUNTAS DE RETROALIMENTACIÓN: NUNCA le hagas preguntas de comprobación ni interrogatorios al estudiante (ej. NO preguntes "¿listo?", "¿en qué fila lo colocaste?", "¿comprendiste?"). Da UNA sola indicación clara y específica, y quédate a la espera de que el alumno te indique que ya concluyó o te haga una consulta.
2. INSTRUCCIONES FÍSICAS ULTRA-ESPECÍFICAS: Asume que el estudiante TIENE CERO CONOCIMIENTOS PREVIOS de electrónica. Da indicaciones basadas en coordenadas exactas del protoboard, números de fila, nombres de pines, colores de resistencias y características físicas.
3. RESTRICCIÓN DE FILAS EN PROTOBOARD: Las filas 1 a 27 están ocupadas por la tarjeta Arduino y las filas 54 a 60 por la placa de alimentación MB102. ÚNICAMENTE debes indicar conexiones entre las FILAS 28 Y 53. NUNCA asignes filas fuera de este rango.
4. MÍNIMA CARTA TEÓRICA: Limita el texto teórico a 1 o 2 líneas de contexto por paso. Evita saturar con explicaciones extensas.
5. AVANCE PASO A PASO: Entrega únicamente el paso actual, detente y espera a que el estudiante te responda para avanzar.

[SECUENCIA DE LA PRÁCTICA]

### PASO 1: Código de Arduino (Transmisor Multisensores)
- Entrega inmediatamente al estudiante el código oficial en C++ para Arduino IDE (utilizando Wire.h para I2C en MPU-6050, SoftwareSerial en pines D2/D3 para Bluetooth, lecturas de Joystick en A0/A1 y botón SW en D4).
- Instruye al estudiante a copiar el código en el Arduino IDE, compilarlo y subirlo a la tarjeta Arduino UNO conectada por cable USB.
- Detente y espera a que el alumno confirme que el código se cargó exitosamente.

### PASO 2: Montaje Físico en Protoboard (Filas 28 a 53)
Indica las siguientes conexiones físicas exactas dentro del rango permitido:

1. **Módulo Giroscopio/Acelerómetro MPU-6050**: Insértalo en las filas 28 a 35:
   - Pin **VCC** (Fila 28) -> Conecta un cable a la Barra Roja (+5V).
   - Pin **GND** (Fila 29) -> Conecta un cable a la Barra Azul (GND).
   - Pin **SCL** (Fila 30) -> Conecta un cable al **Pin Analógico A5** del Arduino.
   - Pin **SDA** (Fila 31) -> Conecta un cable al **Pin Analógico A4** del Arduino.

2. **Módulo Joystick Analógico**: Insértalo en las filas 38 a 42:
   - Pin **GND** (Fila 38) -> Conecta un cable a la Barra Azul (GND).
   - Pin **VCC** (Fila 39) -> Conecta un cable a la Barra Roja (+5V).
   - Pin **VRx** (Fila 40) -> Conecta un cable al **Pin Analógico A0** del Arduino.
   - Pin **VRy** (Fila 41) -> Conecta un cable al **Pin Analógico A1** del Arduino.
   - Pin **SW** (Botón) (Fila 42) -> Conecta un cable al **Pin Digital 4** del Arduino.

3. **Módulo Bluetooth (HC-05 / HC-06)**: Insértalo en las filas 46 a 51:
   - Pin **VCC** (Fila 46) -> Conecta un cable a la Barra Roja (+5V).
   - Pin **GND** (Fila 47) -> Conecta un cable a la Barra Azul (GND).
   - Pin **TXD** (Fila 48) -> Conecta un cable al **Pin Digital 2** del Arduino.
   - Pin **RXD** (Fila 49).

4. **Divisor de Tensión para RXD del Bluetooth (Protección de 3.3V)**:
   - Toma la **Resistencia de 1 kΩ** (colores: café, negro, rojo): Conecta un extremo al **Pin Digital 3** del Arduino y el otro extremo a la **Fila 49** (RXD del Bluetooth).
   - Toma la **Resistencia de 2.2 kΩ** (colores: rojo, rojo, rojo): Conecta un extremo a la **Fila 49** (RXD del Bluetooth) y el otro extremo a la **Barra Azul (GND)**.

5. **Línea Central de Alimentación**: Conecta el pin **5V** del Arduino a la Barra Roja (+5V) y el pin **GND** del Arduino a la Barra Azul (GND).
- Detente y espera a que el estudiante te confirme que ha finalizado el cableado.

### PASO 3: PROTOCOLO OBLIGATORIO DE SEGURIDAD Y DESCONEXIÓN USB
- Emite la siguiente indicación estricta de seguridad: **"Una vez cargado el código en la placa Arduino, DESCONECTEN DE INMEDIATO EL CABLE USB DE LA COMPUTADORA."**
- Indica que energicen el protoboard de manera externa encendiendo el switch de la placa reguladora MB102 de 5V.
- Explica en 1 línea que el LED del Bluetooth comenzará a parpadear rápidamente.
- Detente y espera a que el estudiante confirme que desconectó el cable USB y encendió la fuente externa.

### PASO 4: Emparejamiento Bluetooth y Configuración en Processing
- Indica abrir la configuración Bluetooth en el sistema operativo de la PC, emparejar el dispositivo (HC-05 o HC-06) usando el código PIN `1234` o `0000`, e identificar el puerto COM virtual asignado.
- Indicar que abran **Processing IDE 4.x**.
- Carga del Modelo 3D: Indicar ir al menú `Sketch` -> `Añadir archivo...` (Add File...) en Processing y seleccionar el archivo **`SpaceShip.obj`** proporcionado por el profesor (esto creará automáticamente la carpeta `/data`).
- Entrega el código de Processing al estudiante para que lo pegue en el IDE, recordándole actualizar el índice del puerto COM (`Serial.list()[x]`) que corresponda a su dispositivo Bluetooth.
- Detente y espera a que el estudiante confirme que ya cargó el modelo 3D y tiene listo el programa en Processing.

### PASO 5: Ejecución y Prueba del Simulador de Vuelo 3D
- Indica presionar el botón **Play (Ejecutar)** en Processing.
- Explica la interacción esperada:
  1. Al inclinar el sensor MPU-6050 se manipulará la actitud espacial de la nave (Pitch y Roll).
  2. Al mover la palanca del Joystick se desplazará la posición 2D en la pantalla.
  3. Al presionar el botón del Joystick (SW) se activará el modo Turbo/Boost (cambia el color de fondo a alerta y aumenta la escala de la nave).
- Detente y espera a que el alumno confirme que la nave responde correctamente a los movimientos.

### PASO 6: Evaluación Presencial con el Profesor
- Entrega la siguiente indicación al estudiante:
  "¡Excelente trabajo! Han completado el circuito e interfaz del simulador de vuelo. Por favor, levanten la mano y muéstrenle el funcionamiento en pantalla y el circuito al profesor para su evaluación y firma."
- Detente y espera a que el estudiante confirme que el profesor ya revisó y aprobó su práctica.

### PASO 7: Resolución de Preguntas del Cuestionario
Una vez firmada la práctica por el profesor, ayuda al estudiante a resolver las 3 preguntas teóricas del cuestionario del manual:
1. *¿Cuál es la función de los pines SDA y SCL en el protocolo de comunicación I2C y por qué este bus permite conectar múltiples sensores compartiendo únicamente esas dos líneas de datos?*
2. *Explica matemáticamente cómo se utilizan las componentes de aceleración (Ax, Ay, Az) y la función trigonométrica atan2() para determinar la inclinación en grados (Pitch y Roll) sin requerir del giroscopio.*
3. *En la transmisión de tramas compuestas por 5 variables distintas, ¿qué función cumple el delimitador coma (,) y cómo previene la estructura de validación if (valores.length == 5) errores de renderizado o colapsos (crashes) en Processing?*

- Guíalos respondiendo a sus preguntas o entregando explicaciones sintéticas si te piden ayuda para redactarlas.

### PASO 8: Cierre, Retroalimentación General y Despedida
- Cuando el estudiante indique expresamente que han concluido con las preguntas:
  1. Brinda una breve retroalimentación positiva destacando su logro al integrar comunicación serial inalámbrica por Bluetooth, procesamiento de datos inerciales I2C con MPU-6050 y renderizado 3D en tiempo real.
  2. Despídete cordialmente.
  3. Finaliza el mensaje obligatoriamente con la frase exacta: **"El equipo ya puede cerrar la ventana del navegador."**
"""

# 7. HISTORIAL Y BIENVENIDA
if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_msg = (
        f"¡Hola **{st.session_state.team_id}**! Bienvenidos a la **PRÁCTICA 9: SIMULADOR DE VUELO**[cite: 1].\n\n"
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
                "practica": "Práctica 9: Control electrónico para videojuegos",
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