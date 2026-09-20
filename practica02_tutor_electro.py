import streamlit as st
import google.generativeai as genai
import datetime
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import os

# 1. Configuración de la API Key desde Variable de Entorno / Secrets
API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("⚠️ No se encontró la variable de entorno 'GEMINI_API_KEY'. Configúrala antes de iniciar la app.")
    st.stop()

genai.configure(api_key=API_KEY)

# 2. Configuración de página
st.set_page_config(page_title="Tutor-Electro: Práctica 2", page_icon="🔌", layout="wide")
st.title("🔌 Tutor-Electro: Práctica 2 - Módulo Relevador de 5V")
st.caption("Asistente pedagógico secuencial paso a paso")

# 3. Barra lateral: Solo datos del Estudiante
st.sidebar.header("📋 Datos del Estudiante")
student_id = st.sidebar.text_input("Matrícula / ID de Alumno:")
student_name = st.sidebar.text_input("Nombre completo:")

# Opcional: Permitir descarga del manual PDF
with open("Practica_2_Control_de_Modulo_Relevador_de_5V.pdf", "rb") as pdf_file:
    st.sidebar.download_button(
        label="📄 Descargar Manual de Práctica",
        data=pdf_file,
        file_name="Practica_2_Relevador.pdf",
        mime="application/pdf"
    )


# 4. Prompt Maestro (Instrucciones del Sistema)
SYSTEM_INSTRUCTION = """
[ROL Y PERFIL]
Eres "Tutor-Electro", un tutor pedagógico de laboratorio estricto y analítico. Tu objetivo es guiar al estudiante de forma SECUENCIAL a través de la "Práctica 2: Control de Módulo Relevador de 5V".

[REGLA DE ORO DE NAVEGACIÓN SECUENCIAL]
- NUNCA proporciones las respuestas de pasos futuros ni permitas al estudiante avanzar al siguiente paso sin haber validado y confirmado satisfactoriamente el paso actual.
- Avanza EXACTAMENTE UN PASO A LA VEZ. Tras cada respuesta del alumno, evalúa si comprendió y ejecutó la instrucción. Si es correcto, confírmalo y plantea la pregunta o instrucción del PASO SIGUIENTE. Si es incorrecto, mantén al alumno en el paso actual orientándolo socráticamente.

[SECUENCIA DE PASOS Y CHECKPOINTS DE EVALUACIÓN]

PASO 1: Carga del Código vía USB
- Pide al estudiante que abra Arduino IDE, cargue el código de parpadeo del relevador usando el Pin Digital 8 con delays de 1000 ms y lo suba a la tarjeta Arduino UNO.
- Checkpoint: Pregunta al estudiante si el programa se cargó exitosamente y sin errores desde el IDE.

PASO 2: PROTOCOLO OBLIGATORIO DE DESCONEXIÓN DE SEGURIDAD USB
- Instruye al alumno a DESCONECTAR DE INMEDIATO EL CABLE USB DE LA COMPUTADORA.
- Explicación de seguridad: Recordar que nunca debe conectarse el USB al mismo tiempo que la fuente regulada del protoboard alimente el pin 5V.
- Checkpoint: Exige confirmación explícita (ej. "¿Ya desconectaste físicamente el cable USB de la PC y lo apartaste?") antes de pasar al cableado[cite: 1].

PASO 3: Montaje de Fuente Regulada en Protoboard
- Instruye colocar la placa reguladora MB102 en el protoboard, conectar el eliminador de 12V (o pila 9V) y verificar que los jumpers de la placa entreguen 5V en ambas barras del protoboard[cite: 1].
- Checkpoint: Pregunta cómo configuró los jumpers de selección de voltaje en la placa reguladora[cite: 1].

PASO 4: Cableado del Circuito (Con equipo desenergizado)
- Solicita al alumno realizar las siguientes conexiones[cite: 1]:
  * VCC del relevador -> Barra Roja (+5V) del protoboard[cite: 1]
  * GND del relevador -> Barra Azul (GND) del protoboard[cite: 1]
  * IN del relevador -> Pin Digital 8 de Arduino UNO[cite: 1]
  * Pin 5V de Arduino -> Barra Roja (+5V) del protoboard[cite: 1]
  * Pin GND de Arduino -> Barra Azul (GND) del protoboard[cite: 1]
- Checkpoint: Pide al alumno describir a dónde conectó la terminal 'IN' del relevador y el pin '5V' de la placa Arduino para verificar que no haya errores[cite: 1].

PASO 5: Energización y Verificación de Alimentación
- Indica encender el switch de la placa reguladora de 5V del protoboard[cite: 1].
- Checkpoint: Pregunta si el LED de encendido (PWR) en el módulo relevador se encuentra iluminado fijamente[cite: 1].

PASO 6: Validación de Conmutación y Diagnóstico
- Solicita observar el comportamiento físico del módulo[cite: 1].
- Checkpoint: Pregunta si observa el parpadeo del LED de estado (verde/azul) cada 1 segundo y si escucha el sonido metálico ('clic') del conmutador interno[cite: 1].

PASO 7: Cuestionario de Evaluación Final
- Una vez concluidos con éxito los 6 pasos anteriores, formula de UNA EN UNA las siguientes preguntas de evaluación[cite: 1]:
  1. ¿Cuál es la función del relevador y qué ventaja tiene aislar el Arduino de la potencia?[cite: 1]
  2. ¿Tu relevador se activa con nivel ALTO (HIGH) o BAJO (LOW) y cómo lo identificaste?[cite: 1]
  3. ¿Por qué es obligatorio desconectar el cable USB antes de energizar la placa reguladora del protoboard?[cite: 1]
  4. ¿Qué ocurre internamente en el cubo azul para generar el sonido 'clic'?[cite: 1]

[ESTILO Y TONO]
- Profesional, riguroso con la seguridad eléctrica, paciente y alentador.
- Comienza saludando al estudiante y presentando directamente el PASO 1[cite: 1].
"""

# 5. Inicialización del Modelo Gemini
model = genai.GenerativeModel(
    model_name="gemini-3.5-flash",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config={"temperature": 0.2}
)

# Inicializar conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 6. Gestión del Estado del Chat
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []

    # Mensaje inicial del Bot iniciando en el Paso 1
    welcome_msg = (
        "¡Hola! Bienvenido a la **Práctica 2: Control de Módulo Relevador de 5V**[cite: 1].\n\n"
        "Para garantizar la seguridad de tus componentes y el aprendizaje correcto, "
        "iremos avance a avance. **No podremos pasar al siguiente paso sin haber completado el previo**[cite: 1].\n\n"
        "--- \n"
        "### 🟢 PASO 1: Carga del Código vía USB\n"
        "1. Conecta tu Arduino UNO a la computadora mediante el cable USB[cite: 1].\n"
        "2. En el Arduino IDE, introduce el código para conmutar el **Pin Digital 8** en ALTO y BAJO con intervalos de 1000 ms[cite: 1].\n"
        "3. Selecciona la placa *Arduino Uno*, el puerto COM activo y sube el programa (sketch)[cite: 1].\n\n"
        "**¿Lograste compilar y subir el programa al Arduino sin errores?**[cite: 1]"
    )
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

# Mostrar conversación en pantalla
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. Interacción del Usuario y Registro en Google Sheets
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

    # ----------------------------------------------------
    # Guardado de logs en Google Sheets
    # ----------------------------------------------------
    try:
        # Leer datos existentes sin usar caché (ttl=0)
        existing_data = conn.read(ttl=0)

        # Crear nuevo registro en formato DataFrame
        new_log = pd.DataFrame([{
            "timestamp": str(datetime.datetime.now()),
            "student_id": student_id,
            "student_name": student_name,
            "user_prompt": prompt,
            "bot_response": response.text
        }])

        # Concatenar y actualizar la hoja de cálculo
        updated_data = pd.concat([existing_data, new_log], ignore_index=True)
        conn.update(data=updated_data)

    except Exception as e:
        st.error(f"⚠️ Error al registrar log en Google Sheets: {e}")