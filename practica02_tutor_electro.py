import streamlit as st
import google.generativeai as genai
import datetime
import json
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
st.caption("Asistente pedagógico secuencial paso a paso")

# 3. Datos del alumno
st.sidebar.header("📋 Registro de Estudiante")
student_id = st.sidebar.text_input("Matrícula / ID:")
student_name = st.sidebar.text_input("Nombre completo:")

# 4. Prompt Maestro Secuencial para Práctica 2
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

# 5. Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 6. Historial de sesión de Chat
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

# 7. Procesamiento de entrada del usuario
if prompt := st.chat_input("Escribe tu respuesta o avance aquí..."):
    if not student_id:
        st.warning("⚠️ Por favor ingresa tu Matrícula / ID en la barra lateral antes de continuar.")
        st.stop()

    # Guardar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Preparar el contexto histórico para la API
    formatted_contents = []
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "model"
        formatted_contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
        )

    # Respuesta de Gemini con el nuevo SDK
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=formatted_contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2  # Temperatura baja para mayor apego a las reglas
            )
        )

        bot_reply = response.text
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        
        with st.chat_message("assistant"):
            st.markdown(bot_reply)

        # Registro en Google Sheets
        try:
            existing_data = conn.read(ttl=0)
            new_log = pd.DataFrame([{
                "timestamp": str(datetime.datetime.now()),
                "practica": "Practica 2 - Relevador",
                "student_id": student_id,
                "student_name": student_name,
                "user_prompt": prompt,
                "bot_response": bot_reply
            }])
            updated_data = pd.concat([existing_data, new_log], ignore_index=True)
            conn.update(data=updated_data)
        except Exception as sheet_err:
            st.error(f"⚠️ Error al guardar en la bitácora: {sheet_err}")

    except Exception as e:
        st.error(f"Error de comunicación con la API: {e}")