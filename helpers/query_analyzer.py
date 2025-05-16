"""
Módulo para analizar y modificar consultas SQL basado en el historial de conversación.
"""
import re
import logging

# Configurar logging
logger = logging.getLogger(__name__)

def extract_sql_queries(text):
    """
    Extrae consultas SQL de un texto.
    
    Args:
        text (str): Texto que puede contener consultas SQL
        
    Returns:
        list: Lista de consultas SQL encontradas
    """
    # Patrones para identificar consultas SQL
    patterns = [
        # Patrón para consultas dentro de bloques de código ```
        r'```sql\s*(.*?)\s*```',
        r'```\s*(SELECT[\s\S]*?;)\s*```',
        # Patrón para consultas en línea
        r'`(SELECT[\s\S]*?;)`',
        # Patrón para detectar consultas SELECT sin formato especial
        r'(SELECT\s+[\w\*]+\s+FROM\s+[\w\.]+(?:\s+WHERE\s+.*?)?(?:\s+GROUP\s+BY\s+.*?)?(?:\s+HAVING\s+.*?)?(?:\s+ORDER\s+BY\s+.*?)?(?:\s+LIMIT\s+\d+)?;)'
    ]
    
    queries = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]  # En caso de grupos de captura
            queries.append(match.strip())
    
    return queries

def analyze_query(query):
    """
    Analiza una consulta SQL y extrae información relevante.
    
    Args:
        query (str): Consulta SQL a analizar
        
    Returns:
        dict: Información extraída de la consulta
    """
    query_info = {
        'tables': [],
        'columns': [],
        'filters': [],
        'joins': [],
        'aggregations': [],
        'group_by': [],
        'order_by': [],
        'raw_query': query
    }
    
    # Extraer tablas
    from_match = re.search(r'FROM\s+([\w\.\,\s]+)(?:WHERE|GROUP BY|ORDER BY|LIMIT|$)', query, re.IGNORECASE)
    if from_match:
        tables_str = from_match.group(1).strip()
        query_info['tables'] = [t.strip() for t in tables_str.split(',')]
    
    # Extraer columnas
    select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE)
    if select_match:
        columns_str = select_match.group(1).strip()
        if columns_str == '*':
            query_info['columns'] = ['*']
        else:
            cols = []
            for col in columns_str.split(','):
                # Manejar alias y funciones
                col = col.strip()
                if ' AS ' in col.upper():
                    col_parts = col.split(' AS ', 1)
                    col_name = col_parts[0].strip()
                    cols.append(col_name)
                else:
                    cols.append(col)
            query_info['columns'] = cols
    
    # Extraer filtros WHERE
    where_match = re.search(r'WHERE\s+(.*?)(?:GROUP BY|ORDER BY|LIMIT|$)', query, re.IGNORECASE)
    if where_match:
        filters_str = where_match.group(1).strip()
        # Simplificación de filtros - en un sistema real se haría un análisis más profundo
        query_info['filters'] = [f.strip() for f in filters_str.split('AND')]
    
    # Extraer GROUP BY
    group_by_match = re.search(r'GROUP BY\s+(.*?)(?:HAVING|ORDER BY|LIMIT|$)', query, re.IGNORECASE)
    if group_by_match:
        group_by_str = group_by_match.group(1).strip()
        query_info['group_by'] = [g.strip() for g in group_by_str.split(',')]
    
    # Extraer ORDER BY
    order_by_match = re.search(r'ORDER BY\s+(.*?)(?:LIMIT|$)', query, re.IGNORECASE)
    if order_by_match:
        order_by_str = order_by_match.group(1).strip()
        query_info['order_by'] = [o.strip() for o in order_by_str.split(',')]
    
    # Identificar agregaciones
    agg_patterns = [r'COUNT\(\s*\w+\s*\)', r'SUM\(\s*\w+\s*\)', r'AVG\(\s*\w+\s*\)', r'MIN\(\s*\w+\s*\)', r'MAX\(\s*\w+\s*\)']
    for pattern in agg_patterns:
        aggs = re.findall(pattern, query, re.IGNORECASE)
        query_info['aggregations'].extend(aggs)
    
    return query_info

def find_related_queries(query_info1, query_info2):
    """
    Encuentra relaciones entre dos consultas SQL.
    
    Args:
        query_info1 (dict): Información de la primera consulta
        query_info2 (dict): Información de la segunda consulta
        
    Returns:
        dict: Información sobre la relación entre las consultas
    """
    relation = {
        'related': False,
        'common_tables': [],
        'common_columns': [],
        'relationship_type': None,
        'modification_suggestions': []
    }
    
    # Verificar tablas comunes
    relation['common_tables'] = [t for t in query_info1['tables'] if t in query_info2['tables']]
    
    # Verificar columnas comunes
    relation['common_columns'] = [c for c in query_info1['columns'] if c in query_info2['columns']]
    
    # Determinar si las consultas están relacionadas
    if relation['common_tables'] or relation['common_columns']:
        relation['related'] = True
    
    # Determinar el tipo de relación
    if query_info1['tables'] == query_info2['tables'] and query_info1['columns'] != query_info2['columns']:
        relation['relationship_type'] = 'same_table_different_columns'
        relation['modification_suggestions'].append(
            "Se puede modificar la consulta para incluir las columnas de ambas consultas."
        )
    elif set(query_info1['tables']).issubset(set(query_info2['tables'])) or set(query_info2['tables']).issubset(set(query_info1['tables'])):
        relation['relationship_type'] = 'subset_tables'
        relation['modification_suggestions'].append(
            "Se puede hacer un JOIN entre las tablas para obtener resultados relacionados."
        )
    elif relation['common_tables'] and (query_info1['aggregations'] or query_info2['aggregations']):
        relation['relationship_type'] = 'related_aggregations'
        relation['modification_suggestions'].append(
            "Se pueden combinar las agregaciones para obtener un análisis más completo."
        )
    
    return relation

def modify_query(original_query, relation_info, modification_intent):
    """
    Modifica una consulta SQL basada en la relación con otra consulta.
    
    Args:
        original_query (str): Consulta SQL original
        relation_info (dict): Información sobre la relación entre consultas
        modification_intent (str): Intención de modificación (e.g., "incluir ventas")
        
    Returns:
        str: Consulta SQL modificada
    """
    modified_query = original_query
    
    if not relation_info['related']:
        return original_query
    
    # Ejemplo de modificación para añadir JOIN para consultas relacionadas con ventas
    if "venta" in modification_intent.lower() or "ventas" in modification_intent.lower():
        if "join" not in original_query.lower():
            # Simplificación - en un sistema real se haría un análisis más complejo
            if "from registros" in original_query.lower():
                # Añadir JOIN con tabla de ventas
                modified_query = original_query.replace(
                    "FROM registros",
                    "FROM registros JOIN ventas ON registros.id = ventas.registro_id"
                )
                
                # Si hay un WHERE, añadir condición para contar solo ventas completadas
                if "where" in modified_query.lower():
                    modified_query = modified_query.replace(
                        "WHERE",
                        "WHERE ventas.status = 'completada' AND "
                    )
                else:
                    # Si no hay WHERE, añadirlo
                    before_group_by = modified_query.lower().find("group by")
                    if before_group_by > 0:
                        modified_query = modified_query[:before_group_by] + " WHERE ventas.status = 'completada' " + modified_query[before_group_by:]
                    else:
                        modified_query = modified_query + " WHERE ventas.status = 'completada'"
    
    # Modificar SELECT para incluir conteo o suma de ventas
    if "count" in modification_intent.lower() and "count" not in original_query.lower():
        select_end = original_query.lower().find("from")
        if select_end > 0:
            columns = original_query[6:select_end].strip()
            modified_query = "SELECT " + columns + ", COUNT(ventas.id) as total_ventas " + original_query[select_end:]
    
    return modified_query

def generate_query_suggestion(query_history, current_question):
    """
    Genera una sugerencia de modificación de consulta basada en el historial y la pregunta actual.
    
    Args:
        query_history (dict): Historial de consultas por sesión
        current_question (str): Pregunta actual del usuario
        
    Returns:
        dict: Sugerencia de consulta que incluye la consulta original, la modificada y una explicación
    """
    # Si no hay historial, no hay sugerencia
    if not query_history or len(query_history) < 1:
        return None
    
    # Obtener la última consulta del historial
    last_query_info = list(query_history.values())[-1]
    
    # Crear una consulta ficticia basada en la pregunta actual
    # Esto es una simplificación - en un sistema real se haría un análisis más complejo
    current_query = "SELECT * FROM tabla WHERE condicion = 'valor'"
    if "venta" in current_question.lower():
        current_query = "SELECT id, fecha, monto FROM ventas WHERE status = 'completada'"
    
    current_query_info = analyze_query(current_query)
    
    # Encontrar relaciones entre las consultas
    relation = find_related_queries(last_query_info, current_query_info)
    
    # Si hay relación, generar sugerencia de modificación
    if relation['related']:
        modified_query = modify_query(last_query_info['raw_query'], relation, current_question)
        
        if modified_query != last_query_info['raw_query']:
            return {
                'original_query': last_query_info['raw_query'],
                'modified_query': modified_query,
                'explanation': "He modificado la consulta original para responder a tu pregunta sobre ventas."
            }
    
    return None