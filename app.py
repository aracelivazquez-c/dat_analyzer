"""
KavakDataBot - Aplicación web para consultar información sobre análisis de datos de Kavak

Esta aplicación permite a los usuarios realizar preguntas sobre análisis de datos,
definiciones de KPIs, y construcción de queries utilizando múltiples documentos
como fuente de conocimiento, seleccionando el más relevante para cada pregunta.
"""
import os
import logging
import glob
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, flash
from helpers.openai_helpers import get_openai_response
from helpers.docx_processor import get_document_data, process_multiple_documents, find_most_relevant_document

# Load environment variables from .env file
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Directorio de documentos
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'attached_assets')

# Buscar todos los documentos .docx en el directorio
def get_document_paths():
    """Obtiene las rutas de todos los documentos Word en el directorio attached_assets"""
    doc_paths = glob.glob(os.path.join(DOCS_DIR, '*.docx'))
    logger.debug(f"Documentos encontrados: {len(doc_paths)}")
    for path in doc_paths:
        logger.debug(f"Documento: {os.path.basename(path)}")
    return doc_paths

# Cache para almacenar los datos de los documentos
documents_data_cache = None

def load_documents_data():
    """Carga y almacena en caché los datos de todos los documentos"""
    global documents_data_cache
    if documents_data_cache is None:
        try:
            # Obtener las rutas de los documentos
            doc_paths = get_document_paths()
            
            # Verificar si hay documentos
            if not doc_paths:
                logger.warning("No se encontraron documentos DOCX en el directorio")
                raise FileNotFoundError("No se encontraron documentos para procesar")
            
            # Procesar todos los documentos
            documents_data_cache = process_multiple_documents(doc_paths)
            logger.info(f"Se cargaron y procesaron {len(documents_data_cache)} documentos correctamente")
        except Exception as e:
            logger.error(f"Error al cargar los documentos: {e}")
            raise
    return documents_data_cache

def get_relevant_document_for_question(question):
    """
    Encuentra el documento más relevante para la pregunta del usuario
    
    Args:
        question (str): Pregunta del usuario
        
    Returns:
        dict: Datos del documento más relevante
    """
    try:
        # Cargar datos de documentos
        documents_data = load_documents_data()
        
        # Encontrar el documento más relevante
        doc_id, doc_data = find_most_relevant_document(question, documents_data)
        logger.info(f"Documento seleccionado para la pregunta: {doc_id}")
        
        return doc_data
    except Exception as e:
        logger.error(f"Error al seleccionar el documento relevante: {e}")
        # Si ocurre un error, utilizamos el enfoque anterior de un solo documento
        if os.path.exists(os.path.join(DOCS_DIR, 'documentacion_compras_mx.docx')):
            logger.info("Usando el documento predeterminado como fallback")
            return get_document_data(os.path.join(DOCS_DIR, 'documentacion_compras_mx.docx'))
        else:
            raise

@app.route('/')
def index():
    """Página principal de la aplicación"""
    # Precargar datos de todos los documentos
    try:
        documents_data = load_documents_data()
        logger.info(f"Datos de {len(documents_data)} documentos precargados correctamente")
    except Exception as e:
        logger.error(f"Error al precargar datos de los documentos: {e}")
        flash(f"Error cargando datos de los documentos: {str(e)}", "error")
    return render_template('index.html')

@app.route('/documentos')
def documentos():
    """Página para verificar los documentos cargados"""
    try:
        # Obtener las rutas de los documentos
        doc_paths = get_document_paths()
        logger.debug(f"Documentos encontrados para página de verificación: {len(doc_paths)}")
        
        # Cargar datos de los documentos
        documents_data = load_documents_data()
        logger.debug(f"Documentos cargados en caché: {len(documents_data.keys())}")
        
        doc_info = []
        for doc_id, data in documents_data.items():
            # Obtener información del documento
            raw_content = data.get("raw_content", "")
            content_size = len(raw_content)
            
            # Crear un resumen básico del contenido
            summary = raw_content[:200] + "..." if content_size > 200 else raw_content
            
            # Crear entrada para la lista
            doc_info.append({
                'nombre': f"{doc_id}.docx",  # Añadimos la extensión para claridad
                'tamaño': f"{content_size} caracteres",
                'resumen': summary
            })
            
        # Ordenar documentos alfabéticamente por nombre
        doc_info.sort(key=lambda x: x['nombre'])
        
        return render_template('documentos.html', documentos=doc_info, total=len(doc_info))
    except Exception as e:
        logger.error(f"Error al mostrar documentos: {e}")
        return render_template('documentos.html', documentos=[], error=str(e))

@app.route('/ask', methods=['POST'])
def ask_question():
    """Procesar la pregunta del usuario, obtener datos del documento Word, 
    y generar una respuesta usando OpenAI"""
    try:
        # Obtener la pregunta y el ID de sesión del formulario
        question = request.form.get('question', '')
        session_id = request.form.get('session_id', None)
        reset_chat = request.form.get('reset', 'false').lower() == 'true'
        
        if not question:
            return jsonify({"error": "No se proporcionó ninguna pregunta"}), 400
        
        logger.debug(f"Pregunta recibida: {question}")
        logger.debug(f"ID de sesión: {session_id}")
        logger.debug(f"Reset chat: {reset_chat}")
        
        # Obtener el documento más relevante para la pregunta
        try:
            doc_id, doc_data = find_most_relevant_document(question, load_documents_data())
            logger.debug(f"Documento relevante recuperado correctamente: {doc_id}")
        except Exception as e:
            logger.error(f"Error al recuperar el documento relevante: {e}")
            return jsonify({"error": f"Error al acceder a los documentos: {str(e)}"}), 500
        
        # Verificar si tenemos la clave API de OpenAI
        if not os.environ.get("OPENAI_API_KEY"):
            error_msg = "API Key de OpenAI no configurada. Por favor, configura la variable de entorno OPENAI_API_KEY."
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 500
        
        # Generar respuesta con OpenAI
        try:
            # Si no hay session_id, generar uno nuevo
            if not session_id:
                session_id = f"session_{os.urandom(8).hex()}"
                
            response = get_openai_response(question, doc_data, doc_id=doc_id, session_id=session_id, reset=reset_chat)
            logger.debug("Respuesta de OpenAI generada correctamente")
            
            # Añadir información del documento utilizado a la respuesta
            clean_doc_id = str(doc_id).replace('.docx', '') if doc_id else "Desconocido"
            response_data = {
                "response": response, 
                "session_id": session_id,
                "document_used": clean_doc_id
            }
            
            return jsonify(response_data)
        except Exception as e:
            logger.error(f"Error al generar respuesta con OpenAI: {e}")
            return jsonify({"error": f"No se pudo generar una respuesta: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return jsonify({"error": f"Ocurrió un error inesperado: {str(e)}"}), 500
