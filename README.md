# ETL-canasta-basica-mexico
# Pipeline de datos para el análisis de precios de la canasta básica en México

## Descripción del proyecto

Este repositorio contiene un proyecto personal de Data Science y ETL enfocado en construir un flujo completo de datos para analizar precios de productos de la canasta básica en supermercados mexicanos.

El proyecto no se limita a la extracción de información. Su propósito es demostrar la capacidad de diseñar e implementar un pipeline que cubra todo el ciclo de los datos:  
- obtencion de datos  
- limpieza y normalizacion    
- almacenamiento y modelado   
- automatizacion  
- analisis y visualizacion    
- conclusiones e insights  

El pipeline está diseñado para generar datos comparables y confiables que permitan responder preguntas como:

* *¿Cómo evolucionan los precios de una canasta básica a través del tiempo?*  
* *¿Cuáles son las diferencias entre las principales marcas y tiendas?*  
* *¿Cuáles son los mejores productos con base en su información nutrimental?*  
* *¿Qué otras conclusiones pueden obtenerse al combinar precios, presentaciones, descuentos, marcas, tiendas e información nutrimental?*  

Estas preguntas guían las reglas de extracción, limpieza, normalización, modelado y presentación de los datos.

### Objetivo  
**Construir un pipeline completo que permita:**  
- Obtener periódicamente información pública de productos y precios.  
- Conservar los datos crudos para auditoría y reprocesamiento.  
- Limpiar y normalizar nombres, categorías, marcas, unidades, presentaciones y precios.  
- Identificar productos comparables entre distintas tiendas.  
- Construir desde cero una base de datos relacional en PostgreSQL.  
- Mantener un histórico de precios y descuentos.  
- Crear vistas SQL estables para análisis y visualización.  
- Automatizar la ejecución del flujo cuando la implementación local sea estable.  
- Presentar resultados mediante dashboards orientados a conclusiones claras.

# Fases del proyecto
###  Cronograma y Estado del Proyecto

| Fase | Alcance y Tecnologías | Estado |
| :--- | :--- | :--- |
| **1. Scraping** | Navegación, extracción, parsing, validación básica y exportación de datos crudos por tienda. |  **Completada** |
| **2. Data Cleaning & Automation** | Limpieza, normalización, modelado relacional, PostgreSQL, histórico de precios, vistas SQL y automatización. |  **En desarrollo** — primeros pasos |
| **3. Dashboard** | Visualización, análisis comparativo, evolución de precios, nutrición e interpretación de resultados. |  **Planeada** |

### Implementación futura en la nube

Cuando la versión local sea estable, se evaluará la migración de la base de datos y la automatización a servicios de AWS. La nube no forma parte de la primera implementación funcional y no se utilizará antes de validar correctamente el modelo, las cargas y los resultados.

##  Stack Tecnológico y Herramientas

A continuación se detallan las herramientas principales seleccionadas para cada etapa del pipeline, organizadas por su madurez en la implementación:

###  Obtención de Datos (Scraping)
* **Lenguaje Base:** Python
* **Herramientas de Extracción:**
  - [x] **Playwright:** Navegación e interacción dinámica con los sitios web.
  - [x] **BeautifulSoup:** Parsing y extracción del HTML estructurado.
  - [x] **Pandas:** Estructuración inicial y exportación de los datos crudos.

###  Limpieza, Transformación y Automatización
* **Procesamiento:** Python & Pandas (Limpieza y normalización de textos/precios).
* **Estandarización:** Expresiones regulares (Regex) y diccionarios controlados.
* **Persistencia:** 
  - [ ] **SQLAlchemy:** Configurado como opción inicial para la conexión y carga hacia la base de datos *(decisión definitiva a confirmar durante la implementación)*.

###  Base de Datos (PostgreSQL)
Implementación de un modelo relacional robusto. Se utilizará **SQL puro** para el desarrollo desde cero de:
- [ ] Catálogos maestros y tablas de *staging* (datos temporales).
- [ ] Tablas normalizadas con restricciones de integridad e índices de optimización.
- [ ] Lógica de cargas, operaciones *upsert* e histórico de evolución de precios.
- [ ] Vistas analíticas optimizadas para el consumo de datos.

###  Presentación y Business Intelligence
* [ ] **Power BI:** Herramientas principal prevista para el diseño del dashboard interactivo.
* [ ] **Looker Studio:** Considerado como una posible versión adicional/alternativa.

###  Infraestructura Futura
* [ ] **AWS (Amazon Web Services):** Migración y despliegue en la nube planificado una vez que el pipeline local esté completamente validado y estable.

##  Estado Actual del Proyecto

### Fase 1: Scraping (Finalizada y Funcional)
* **Tiendas implementadas:**
  - **Soriana:** Totalmente funcional y adaptada al flujo automatizado.
  - **Chedraui:** Totalmente funcional y adaptada al flujo automatizado.
* **Resultados y artefactos:**
  - Exportación de archivos CSV independientes por tienda y fecha de ejecución.
  - Generación automática de un resumen acumulativo de control tras cada ejecución.
  - Conservación selectiva del código HTML de origen para facilitar tareas de depuración.
* **Diseño del software:** Arquitectura modular que separa de forma estricta la configuración, la navegación, el *parsing*, la exportación y las funciones auxiliares.
* **Caso Walmart:** La tienda fue evaluada y documentada formalmente. Sin embargo, se desactivó del flujo automático debido a restricciones severas de captcha y sistemas de protección anti-bot. No se integraron mecanismos para evadir estas barreras por considerarse fuera del alcance técnico del proyecto.

### Fase 2: Data Cleaning & Automation (En Desarrollo Inicial)
La fase se encuentra en sus primeros pasos de desarrollo. El diseño general de la arquitectura ya contempla y planifica las siguientes etapas:
* **Ingesta y Staging:** Conservación de los archivos CSV crudos originales y posterior carga inicial hacia una zona de *staging* en la base de datos.
* **Procesamiento de Datos:** Rutinas de limpieza para textos, categorías, marcas, precios y gestión de descuentos aplicados.
* **Estandarización:** Mecanismos para la detección y normalización de unidades de medida junto con sus respectivas presentaciones comerciales.
* **Modelado:** Construcción de identidades estables y unificadas para el catálogo de productos y sus detalles específicos por tienda.
* **Infraestructura SQL:** Creación desde cero de la base de datos PostgreSQL, incluyendo la lógica para el histórico de precios, restricciones de integridad y la automatización posterior de todo el flujo de datos.

### Fase 3: Dashboard (Planeada)
* **Estatus:** El alcance está completamente definido, pero el desarrollo formal aún no ha comenzado.
* **Estrategia de consumo:** La herramienta de visualización consumirá directamente vistas SQL previamente preparadas en la base de datos. Esto se diseñó de esta manera para centralizar la lógica de negocio en el motor de base de datos y evitar reconstruir transformaciones complejas dentro de la herramienta de BI.

### Uso de inteligencia artificial

> Durante el desarrollo se utilizan herramientas de inteligencia artificial como aceleradores para proponer estructuras, generar bloques iniciales de código, explorar alternativas y apoyar la depuración.  
 
> La IA no sustituye la toma de decisiones técnicas. El código, las reglas de transformación, la arquitectura y los resultados son revisados, probados y validados por el autor del proyecto. Su uso se considera un apoyo para aumentar la velocidad de desarrollo, siempre acompañado de criterio profesional y comprensión del código implementado.
