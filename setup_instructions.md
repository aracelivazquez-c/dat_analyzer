# Instrucciones de Instalación para KavakDataBot

## Requisitos Previos

- Python 3.11 o superior
- Pip (gestor de paquetes de Python)
- Una clave API de OpenAI

## Paso 1: Preparar el Entorno

### Crear un entorno virtual (recomendado)

```bash
# En sistemas basados en Unix (Linux/Mac)
python -m venv venv
source venv/bin/activate

# En Windows
python -m venv venv
venv\Scripts\activate
```

## Paso 2: Instalar Dependencias

Instala todas las dependencias necesarias con el siguiente comando:

```bash
pip install flask flask-sqlalchemy email-validator gspread gunicorn oauth2client openai psycopg2-binary python-docx python-dotenv trafilatura
```

Asegúrate de usar las versiones específicas:

```
email-validator>=2.2.0
flask>=3.1.0
flask-sqlalchemy>=3.1.1
gspread>=6.2.0
gunicorn>=23.0.0
oauth2client>=4.1.3
openai>=1.73.0
psycopg2-binary>=2.9.10
python-docx>=1.1.2
python-dotenv>=1.1.0
trafilatura>=2.0.0
```

## Paso 3: Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```
OPENAI_API_KEY=tu_clave_api_de_openai
SESSION_SECRET=clave_secreta_para_sesiones

# Opcional para integración con Google Sheets
# GOOGLE_CREDENTIALS_JSON=ruta_al_archivo_de_credenciales.json
```

## Paso 4: Preparar los Documentos

Asegúrate de tener tus documentos Word (`.docx`) en la carpeta `attached_assets`. Estos documentos servirán como fuente de conocimiento para el sistema.

## Paso 5: Ejecutar la Aplicación

```bash
# Método 1: Usando Gunicorn (recomendado para producción)
gunicorn --bind 0.0.0.0:5000 --reuse-port main:app

# Método 2: Usando Flask directamente (para desarrollo)
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0
```

## Resolución de Problemas Comunes

### Error con python-docx

Si tienes problemas con la biblioteca python-docx, intenta:

```bash
pip uninstall python-docx
pip install python-docx --no-cache-dir
```

### Error de OpenAI API

Si ves un error relacionado con la API de OpenAI, verifica que:

1. Tu clave API sea válida y esté correctamente configurada en el archivo `.env`
2. La clave API tenga suficientes créditos disponibles
3. Estés usando una versión compatible de la biblioteca OpenAI

### Problemas con la carga de documentos

Si los documentos no se cargan correctamente:

1. Verifica que estén en formato `.docx` (no `.doc`)
2. Asegúrate de que estén en la carpeta `attached_assets`
3. Reinicia la aplicación después de añadir nuevos documentos

## Notas para el Despliegue

Para un despliegue en producción, considera:

1. Usar un servidor WSGI como Gunicorn con múltiples workers
2. Configurar un proxy inverso como Nginx
3. Implementar HTTPS para conexiones seguras
4. Monitorear el uso de la API de OpenAI para controlar costos