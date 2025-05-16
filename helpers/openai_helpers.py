"""
Módulo para interactuar con la API de OpenAI
"""
import os
import logging
import json
import re
from openai import OpenAI, APIError
from helpers.query_analyzer import extract_sql_queries, analyze_query, generate_query_suggestion

# Configurar logging
logger = logging.getLogger(__name__)

# Inicializar cliente de OpenAI solo si la API Key está disponible
client = None
if os.environ.get("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    logger.info("Cliente de OpenAI inicializado correctamente")
else:
    logger.warning(
        "OPENAI_API_KEY no está configurada. El cliente de OpenAI no se ha inicializado."
    )


def format_document_data(doc_data):
    """
    Formatea los datos del documento en un string legible para el prompt
    
    Args:
        doc_data (dict): Los datos estructurados del documento Word
        
    Returns:
        str: Datos formateados como string
    """
    formatted_data = []

    # Añadir título del documento
    formatted_data.append(f"# {doc_data['title']}\n")

    # Añadir secciones con sus contenidos
    formatted_data.append("## Secciones del Documento:")
    for section_title, section_content in doc_data['sections'].items():
        formatted_data.append(f"\n### {section_title}")
        formatted_data.append(section_content)

    # Añadir tablas
    if doc_data['tables']:
        formatted_data.append("\n## Tablas del Documento:")

        for table in doc_data['tables']:
            formatted_data.append(f"\n### Tabla {table['table_id'] + 1}")

            # Añadir encabezados
            if table['headers']:
                headers = " | ".join(table['headers'])
                formatted_data.append(f"Encabezados: {headers}")

            # Añadir filas
            formatted_data.append("Datos:")
            for row in table['rows']:
                row_text = " | ".join(row)
                formatted_data.append(f"- {row_text}")

    return "\n".join(formatted_data)


# Almacenamiento de conversaciones y queries
chat_history = {}
query_history = {}


def get_openai_response(question,
                        doc_data,
                        doc_id=None,
                        session_id=None,
                        reset=False):
    """
    Genera una respuesta a una pregunta de análisis de datos usando OpenAI API
    manteniendo el contexto de la conversación y analizando queries SQL
    
    Args:
        question (str): La pregunta del usuario sobre análisis/KPIs/queries
        doc_data (dict): Datos del documento Word a referenciar
        doc_id (str, optional): Identificador del documento utilizado para responder
        session_id (str, optional): Identificador de la sesión para mantener el historial
        reset (bool): Si es True, reinicia la conversación
    
    Returns:
        str: La respuesta generada por IA
    """
    global chat_history, query_history

    try:
        # Verificar si tenemos la clave API
        if not os.environ.get("OPENAI_API_KEY"):
            logger.error(
                "OPENAI_API_KEY no está configurada en las variables de entorno"
            )
            return "Error: API de OpenAI no configurada. Por favor, configura la variable de entorno OPENAI_API_KEY."

        # Formatear los datos del documento para el prompt
        formatted_data = format_document_data(doc_data)

        # Obtener el nombre del documento si se proporciona el ID
        document_name = doc_data.get('title', 'Documento de Kavak')
        if '.docx' in document_name:
            document_name = document_name.replace('.docx', '')

        # Construir el prompt para OpenAI
        system_prompt = f"""
        Eres un asistente experto en análisis de datos para Kavak, la plataforma líder de compra-venta de autos usados en Latinoamérica.
        Tu función es ayudar a los empleados de Kavak a entender la documentación sobre métricas, reportes y análisis de datos.
        
        Para responder a esta pregunta, estás utilizando la documentación: "{document_name}"
        
        NOTA IMPORTANTE:
        - Considera "sales" como sinónimo de "ventas"
        - Considera "supply" como sinónimo de "compras"
        - Cuando un usuario mencione "sales" o "ventas", se refiere al mismo funnel
        - Cuando un usuario mencione "supply" o "compras", se refiere al mismo funnel
        
        Usa la documentación proporcionada para contestar preguntas sobre:
        1. Definiciones de KPIs y métricas
        2. Cómo interpretar reportes y gráficos
        3. Consultas para obtener diferentes tipos de datos
        4. Análisis y tendencias en los datos
        
        Debes:
        - Si necesitas preguntar mas contexto sobre la preguna, preguntar al usuario por mas detalle basandote en un par de cuestionamientos sobre su solicitud. Por ejemplo, si no te queda claro si la pregunta es del funnel de ventas o de compras, preguntar al usuario.
        - Mantener un tono profesional y claro
        - Proporcionar explicaciones detalladas
        - Referenciar específicamente secciones o tablas de la documentación
        - Aportar ejemplos de SQL cuando sea apropiado
        - Responder siempre en español
        - Mantener el contexto de la conversación, recordando preguntas y respuestas anteriores
        - Cuando se te pida modificar queries, proporciona la consulta SQL modificada y explica los cambios
        - Indicar al final de tu respuesta qué documento se utilizó como fuente: [Fuente: {document_name}]
        
        Si una pregunta está fuera del alcance de la documentación, indica cortésmente que esa información no está disponible en la documentación actual.
        """

        # Crear el mensaje para el usuario con la documentación
        context_message = f"""
        Estás utilizando la siguiente documentación como base de conocimiento:
        
        # DOCUMENTACIÓN: {document_name}
        {formatted_data}
        """

        # Inicializar o reiniciar el historial de chat si es necesario
        if session_id is None:
            session_id = "default"

        if session_id not in chat_history or reset:
            chat_history[session_id] = [{
                "role": "system",
                "content": system_prompt
            }, {
                "role": "system",
                "content": context_message
            }]
            query_history[session_id] = {}

        # Verificar si hay una sugerencia de modificación de query basada en el historial
        query_suggestion = None
        if session_id in query_history and query_history[session_id]:
            query_suggestion = generate_query_suggestion(
                query_history[session_id], question)

        # Si hay una sugerencia, añadirla al contexto
        enhanced_question = question
        if query_suggestion:
            suggestion_context = f"""
            Basado en tus consultas anteriores, te sugiero modificar la consulta SQL:
            
            Consulta original:
            ```sql
            {query_suggestion['original_query']}
            ```
            
            Consulta modificada:
            ```sql
            {query_suggestion['modified_query']}
            ```
            
            {query_suggestion['explanation']}
            
            Tu pregunta original: {question}
            """
            enhanced_question = suggestion_context

        # Añadir la pregunta actual al historial
        chat_history[session_id].append({
            "role": "user",
            "content": enhanced_question
        })

        # Limitar el historial para no exceder los límites de token
        if len(chat_history[session_id]) > 10:
            # Mantener el sistema y el contexto, y las últimas 6 interacciones
            chat_history[session_id] = chat_history[
                session_id][:2] + chat_history[session_id][-6:]

        # Llamar a la API de OpenAI
        # Nota: el modelo más nuevo de OpenAI es "gpt-4o", que fue lanzado el 13 de mayo de 2024.
        # No cambiar esto a menos que el usuario lo solicite explícitamente
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=chat_history[session_id],
            temperature=0.7,
            max_tokens=1000)

        # Extraer la respuesta
        answer = response.choices[0].message.content

        # Añadir la respuesta al historial
        chat_history[session_id].append({
            "role": "assistant",
            "content": answer
        })

        # Extraer y almacenar queries SQL de la respuesta
        extracted_queries = extract_sql_queries(answer)
        for i, query in enumerate(extracted_queries):
            query_info = analyze_query(query)
            query_key = f"query_{len(query_history.get(session_id, {})) + i + 1}"
            if session_id not in query_history:
                query_history[session_id] = {}
            query_history[session_id][query_key] = query_info
            logger.debug(f"Query SQL extraída y analizada: {query_key}")

        logger.debug(f"Respuesta generada con éxito: {len(answer)} caracteres")
        return answer

    except APIError as e:
        error_message = f"Error en la API de OpenAI: {str(e)}"
        logger.error(error_message)
        return f"Lo siento, ocurrió un error al comunicarse con OpenAI: {str(e)}"

    except Exception as e:
        error_message = f"Error inesperado al generar la respuesta: {str(e)}"
        logger.error(error_message)
        return f"Lo siento, ocurrió un error inesperado: {str(e)}"
