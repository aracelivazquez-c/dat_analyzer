# KavakDataBot

## Descripción
KavakDataBot es una aplicación web diseñada para consultar información sobre análisis de datos de Kavak. Permite a los usuarios realizar preguntas sobre análisis de datos, definiciones de KPIs, y construcción de queries utilizando múltiples documentos como fuente de conocimiento, seleccionando automáticamente el más relevante para cada pregunta.

## Características

- 🤖 **Asistente inteligente**: Responde preguntas sobre métricas, KPIs y análisis de datos de Kavak
- 📊 **Multi-documento**: Utiliza diferentes documentos como fuentes de conocimiento
- 🔍 **Selección contextual**: Identifica automáticamente el documento más relevante para cada consulta
- 📝 **Contexto de conversación**: Mantiene el historial para responder adecuadamente a preguntas de seguimiento
- 💻 **Interfaz responsiva**: Diseñada con Bootstrap y optimizada para distintos dispositivos
- 🔄 **Funnel de ventas y compras**: Reconoce términos en inglés y español (`sales`/`ventas`, `supply`/`compras`)
- 📋 **Soporte SQL**: Genera y explica consultas SQL para extracción de datos

## Requisitos

- Python 3.11+
- Pip
- OpenAI API Key
- Clave de acceso a Google Sheets (opcional)

## Instalación

1. **Clonar el repositorio o descargar el ZIP**

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**
   
   Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:
   ```
   OPENAI_API_KEY=tu_clave_api_de_openai
   SESSION_SECRET=tu_clave_secreta_para_sesiones

   # Opcional: Para integración con Google Sheets
   # GOOGLE_CREDENTIALS_JSON=ruta_al_archivo_de_credenciales.json
   ```

4. **Agregar documentos**
   
   Coloca los documentos Word (`.docx`) que servirán como fuente de conocimiento en la carpeta `attached_assets`.

## Ejecución

Para ejecutar la aplicación en modo desarrollo:

```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

O simplemente:

```bash
python -m gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

La aplicación estará disponible en `http://localhost:5000`

## Estructura del Proyecto

```
KavakDataBot/
├── attached_assets/         # Documentos fuente en formato .docx
├── helpers/                 # Módulos auxiliares
│   ├── docx_processor.py    # Procesamiento de documentos Word
│   ├── google_sheets.py     # Integración con Google Sheets
│   ├── openai_helpers.py    # Interacción con OpenAI API
│   └── query_analyzer.py    # Análisis de consultas SQL
├── static/                  # Archivos estáticos
│   ├── css/                 # Estilos
│   └── js/                  # JavaScript
├── templates/               # Plantillas HTML
├── .env                     # Variables de entorno (crear manualmente)
├── .env.example             # Ejemplo de variables de entorno
├── app.py                   # Aplicación principal
├── main.py                  # Punto de entrada
└── requirements.txt         # Dependencias
```

## Uso

1. Abre la aplicación en tu navegador.
2. Escribe una pregunta sobre análisis de datos, KPIs o consultas SQL relacionadas con Kavak.
3. El sistema seleccionará automáticamente el documento más relevante para tu consulta.
4. Lee la respuesta generada y haz preguntas de seguimiento si es necesario.

### Ejemplos de preguntas

- "¿Qué tendencias se pueden identificar en los registros del funnel de compras?"
- "¿Cuáles son los principales KPIs utilizados en el reporte del funnel de ventas?"
- "¿Cómo puedo escribir una consulta SQL para encontrar los registros con ofertas por fecha en el funnel de compras?"
- "Explícame qué significa la métrica 'Oportunidades de Venta' en el funnel de ventas y cómo se calcula"

## Tecnologías utilizadas

- **Flask**: Framework web en Python
- **OpenAI API**: Generación de respuestas con GPT-4o
- **Bootstrap**: Interfaz de usuario responsiva
- **SQLAlchemy**: Interacción con base de datos (para futuras expansiones)
- **Trafilatura**: Procesamiento de documentos 
- **Python-docx**: Extracción de contenido de documentos Word

## Personalización

La aplicación puede personalizarse modificando:

- **Tema visual**: Editar los archivos CSS en `static/css/`
- **Comportamiento de IA**: Ajustar los prompts en `helpers/openai_helpers.py`
- **Interfaz**: Modificar las plantillas HTML en `templates/`

## Licencia

Este proyecto es propiedad de Kavak y está destinado para uso interno.

## Soporte

Para soporte, contactar al equipo de desarrollo de Kavak.