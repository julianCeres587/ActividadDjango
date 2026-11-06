## Fase 2: Del Enunciado a los Modelos y Regla de Negocio

### 1. Entidades y Modelado
Se diseñaron 6 modelos para representar la biblioteca universitaria, resolviendo las relaciones requeridas:
* **`Categoria`:** Clasificación temática de los libros (`Novela`, `Ingeniería`, `Historia`, etc.).
* **`Autor`:** Creadores de las obras.
* **`Libro`:** Obra intelectual en abstracto (título, ISBN, año, idioma y categoría). Posee una relación `ManyToManyField` con `Autor` (un libro puede tener varios autores y un autor varios libros).
* **`Copia`:** Ejemplar físico tangible en estantería (`ForeignKey` a `Libro`), con código de inventario único y condición (`nuevo`, `usado`, `dañado`).
* **`Estudiante`:** Usuario de la biblioteca (código estudiantil como PK, nombre y correo).
* **`Prestamo`:** Transacción que asocia a un estudiante con una copia física concreta, fecha de préstamo, fecha límite y fecha de entrega real.

---

### 2. Implementación de la Regla: "Una copia no puede estar prestada a dos personas al mismo tiempo"

Para garantizar que una copia física no se preste simultáneamente a dos usuarios, se evaluaron dos alternativas que ofrece Django:

| Enfoque | Ventajas | Limitaciones |
| :--- | :--- | :--- |
| **Validación con `clean()`** | Permite mensajes de error personalizados y validaciones en formularios/admin. | **Vulnerable fuera del admin:** Si se guarda desde el shell mediante `.save()`, no se ejecuta a menos que se invoque manualmente `full_clean()`. |
| **Restricción en BD con `UniqueConstraint` (Elegida)** | **Integridad absoluta:** La restricción vive en el motor de base de datos. Se cumple sin excepción desde el admin, el shell, APIs o scripts externos. | Requiere definir la restricción condicional en `class Meta`. |

#### Decisión adoptada y código implementado
Se implementó mediante un **`UniqueConstraint` condicional** dentro de `class Meta` en el modelo `Prestamo`:

```python
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=["copia"],
            condition=models.Q(fecha_entregado__isnull=True),
            name="una_copia_por_prestamo_activo",
            violation_error_message="Esta copia ya tiene un préstamo activo"
        )
    ]
```

> **Justificación:**  
> Se eligió la restricción a nivel de base de datos (`constraints`) porque garantiza que la regla de negocio nunca se viole, sin depender del punto de entrada de los datos (sea panel de administración, shell de Python o futuros servicios). Además, la implementación es declarativa, limpia y se integra directamente con las migraciones de Django.

#### Evidencia de funcionamiento
Al intentar registrar un segundo préstamo para una copia física cuya fecha de entrega aún está vacía (`fecha_entregado is NULL`), Django y la base de datos bloquean la operación mostrando:
```text
Please correct the error below.
* Esta copia ya tiene un préstamo activo
```

---

## Fase 4: Personalización del Panel de Administración

El panel de administración fue configurado para satisfacer tanto los requerimientos técnicos de la actividad como las necesidades prácticas de una bibliotecaria sin conocimientos técnicos.

### 1. Resumen de personalizaciones por modelo

| Modelo | `list_display` (Columnas) | `search_fields` (Búsqueda) | `list_filter` (Filtros laterales) | Características especiales |
| :--- | :--- | :--- | :--- | :--- |
| **`Categoria`** | `id`, `nombre` | `nombre` | — | Búsqueda rápida por nombre. |
| **`Autor`** | `id`, `nombre` | `nombre` | — | Búsqueda rápida por autor. |
| **`Libro`** | `titulo`, `isbn`, `categoria`, `anio_publicacion` | `titulo`, `isbn`, `autores__nombre` | `categoria`, `anio_publicacion`, `idioma` | **`inlines = [CopiaInline]`** (gestión de copias físicas desde la página del libro). |
| **`Copia`** | `codigo_inventario`, `libro`, `nota` | `codigo_inventario`, `libro__titulo` | `nota` | Búsqueda cruzada por código o título del libro. |
| **`Estudiante`** | `codigo`, `nombre`, `correo` | `codigo`, `nombre`, `correo` | — | Búsqueda rápida por código o nombre del alumno. |
| **`Prestamo`** | `estudiante`, `copia`, `fecha_prestamo`, `fecha_limite`, `fecha_entregado` | `estudiante__nombre`, `estudiante__codigo`, `copia__codigo_inventario`, `copia__libro__titulo` | `fecha_prestamo`, `fecha_limite`, `EstadoPrestamoFiltro` | **`readonly_fields = ('fecha_prestamo',)`** y acción masiva **`marcar_devueltos`**. |

---

### 2. Solución al Mini Reto: La Bibliotecaria

Para que la bibliotecaria trabaje con agilidad y sin confusiones, se implementaron cuatro mejoras clave:

1. **Búsqueda inmediata de estudiantes:**  
   En `PrestamoAdmin` y `EstudianteAdmin`, la caja de búsqueda permite encontrar alumnos tipeando su nombre o su código estudiantil (`search_fields = ('estudiante__nombre', 'estudiante__codigo')`).
2. **Diferenciación inequívoca de copias físicas:**  
   Se definió un método `__str__` descriptivo en `Copia` (`"Copia SO-001 del libro Cien años de soledad"`) e inline tabular dentro de `Libro`, evitando que se confundan copias físicas de libros distintos al momento de prestarlas.
3. **Filtro intuitivo de estado (`EstadoPrestamoFiltro`):**  
   Por defecto, filtrar en Django por `fecha_entregado = None` muestra etiquetas poco claras como *"No date"*. Se creó un `SimpleListFilter` personalizado que expone dos opciones legibles:
   * **`Sin entregar:`** filtra préstamos con `fecha_entregado__isnull=True`.
   * **`Entregado:`** filtra préstamos con `fecha_entregado__isnull=False`.
4. **Acción masiva para devolver libros (`marcar_devueltos`):**  
   Permite seleccionar una o varias filas de préstamos pendientes en la lista y, con un solo clic en la barra de acciones, asignar automáticamente la fecha actual (`date.today()`) a `fecha_entregado`.

--- 


## Fase 5: Consultas con el ORM

Para esta fase se cargaron datos de prueba representativos usando el script `poblar_datos.py` (categorías, autores, libros, copias físicas, estudiantes y préstamos con estados devueltos y sin devolver).

A continuación se registran los 10 retos ejecutados en el shell interactivo de Django (`python manage.py shell`), contrastando la predicción previa con lo que devolvió el ORM y la explicación correspondiente:

### Reto 1: Crear un autor, un libro y dos copias físicas desde el shell
- **Código:**
  ```python
  from biblioteca.models import Categoria, Autor, Libro, Copia
  cat = Categoria.objects.get(nombre="Novela")
  autor = Autor.objects.create(nombre="Isaac Asimov")
  libro = Libro.objects.create(
      isbn="9780553293357",
      titulo="Fundación",
      anio_publicacion=1951,
      categoria=cat,
      idioma="Español"
  )
  libro.autores.add(autor)
  copia1 = Copia.objects.create(codigo_inventario="FD-001", libro=libro, nota="nuevo")
  copia2 = Copia.objects.create(codigo_inventario="FD-002", libro=libro, nota="usado")
  ```
- **Lo que predijimos:** Se creará la instancia del autor 'Isaac Asimov', el libro 'Fundación' asociado a dicho autor mediante la relación ManyToMany, y dos copias físicas ('FD-001' y 'FD-002') asociadas a ese libro.
- **Lo que devolvió:**
  - Autor: `<Autor: Isaac Asimov>`
  - Libro: `<Libro: Fundación>`
  - Copias: `<Copia: Copia FD-001 del libro Fundación>`, `<Copia: Copia FD-002 del libro Fundación>`

---

### Reto 2: Obtener todos los libros de un autor buscando al autor por su nombre
- **Código:**
  ```python
  from biblioteca.models import Libro
  libros = Libro.objects.filter(autores__nombre="Robert C. Martin")
  print(list(libros))
  ```
- **Lo que predijimos:** Devolverá un QuerySet con los dos libros escritos por Robert C. Martin: 'Clean Code' y 'Clean Architecture'.
- **Lo que devolvió:**
  `[<Libro: Clean Code>, <Libro: Clean Architecture>]`

---

### Reto 3: Obtener libros cuyo título contiene cierta palabra sin importar mayúsculas
- **Código:**
  ```python
  from biblioteca.models import Libro
  libros = Libro.objects.filter(titulo__icontains="clean")
  print(list(libros))
  ```
- **Lo que predijimos:** El lookup `__icontains` filtrará insensibilizando mayúsculas/minúsculas. Al buscar `"clean"`, traerá 'Clean Code' y 'Clean Architecture'.
- **Lo que devolvió:**
  `[<Libro: Clean Code>, <Libro: Clean Architecture>]`

---

### Reto 4: Obtener las copias físicas disponibles (las que no tienen ningún préstamo activo)
- **Código:**
  ```python
  from biblioteca.models import Copia, Prestamo
  # Excluimos las copias presentes en préstamos activos (fecha_entregado is NULL):
  prestamos_activos = Prestamo.objects.filter(fecha_entregado__isnull=True)
  copias_disponibles = Copia.objects.exclude(prestamo__in=prestamos_activos)
  print(list(copias_disponibles))
  ```
- **Lo que predijimos:** Inicialmente podríamos pensar en `Copia.objects.exclude(prestamo__fecha_entregado__isnull=True)`, pero al evaluar `LEFT OUTER JOIN` en SQL, una copia sin préstamos tiene `prestamo.fecha_entregado IS NULL` y es erróneamente excluida. Excluyendo directamente las copias que están en préstamos activos (`exclude(prestamo__in=prestamos_activos)`), predijimos que obtendríamos las copias no prestadas o ya devueltas: CC-002, CA-001, FD-001, FD-002.
- **Lo que devolvió:**
  `[<Copia: Copia CC-002 del libro Clean Code>, <Copia: Copia CA-001 del libro Clean Architecture>, <Copia: Copia FD-001 del libro Fundación>, <Copia: Copia FD-002 del libro Fundación>]`

---

### Reto 5: Obtener los estudiantes con al menos un préstamo activo, sin repetir
- **Código:**
  ```python
  from biblioteca.models import Estudiante, Prestamo
  prestamos_activos = Prestamo.objects.filter(fecha_entregado__isnull=True)
  estudiantes_activos = Estudiante.objects.filter(prestamo__in=prestamos_activos).distinct()
  print(list(estudiantes_activos))
  ```
- **Lo que predijimos:** Obtendremos los estudiantes que tienen préstamos sin devolver (Carlos Gómez, María Rodríguez, Juan Pérez). Gracias a `.distinct()`, Juan Pérez (quien tiene dos préstamos activos) solo aparecerá una vez. Laura Torres no aparecerá porque nunca ha pedido préstamos.
- **Lo que devolvió:**
  `[<Estudiante: 1151001 - Carlos Gómez>, <Estudiante: 1151002 - María Rodríguez>, <Estudiante: 1151003 - Juan Pérez>]`

---

### Reto 6: Calcular cuántos préstamos ha hecho cada estudiante, contando los ya devueltos
- **Código:**
  ```python
  from django.db.models import Count
  from biblioteca.models import Estudiante
  estudiantes_conteo = Estudiante.objects.annotate(total_prestamos=Count("prestamo"))
  for e in estudiantes_conteo:
      print(f"{e.nombre} ({e.codigo}): {e.total_prestamos} préstamo(s)")
  ```
- **Lo que predijimos:** Se agregará a cada estudiante el conteo total histórico de sus préstamos usando `annotate(Count('prestamo'))`. Carlos: 2, María: 2, Juan: 2, Laura: 0.
- **Lo que devolvió:**
  - Carlos Gómez (1151001): 2 préstamo(s)
  - María Rodríguez (1151002): 2 préstamo(s)
  - Juan Pérez (1151003): 2 préstamo(s)
  - Laura Torres (1151004): 0 préstamo(s)

---

### Reto 7: Encontrar el libro más prestado de la biblioteca
- **Código:**
  ```python
  from django.db.models import Count
  from biblioteca.models import Libro
  libro_top = Libro.objects.annotate(total_prestamos=Count("copia__prestamo")).order_by("-total_prestamos").first()
  print(f"{libro_top.titulo} con {libro_top.total_prestamos} préstamos")
  ```
- **Lo que predijimos:** Atravesando la relación inversa `copia__prestamo`, contará los préstamos de todas las copias de cada libro. 'Cien años de soledad' acumuló 3 préstamos, por lo que será el primero.
- **Lo que devolvió:**
  `Cien años de soledad con 3 préstamos`

---

### Reto 8: Obtener los estudiantes que nunca han pedido un préstamo
- **Código:**
  ```python
  from biblioteca.models import Estudiante
  sin_prestamo = Estudiante.objects.filter(prestamo__isnull=True)
  print(list(sin_prestamo))
  ```
- **Lo que predijimos:** Filtrando por la relación inversa nula (`prestamo__isnull=True`), devolverá a Laura Torres, quien no tiene registros de préstamo.
- **Lo que devolvió:**
  `[<Estudiante: 1151004 - Laura Torres>]`

---

### Reto 9: Marcar un préstamo como devuelto con la fecha de hoy y comprobar que quedó guardado
- **Código:**
  ```python
  from datetime import date
  from biblioteca.models import Prestamo
  prestamo = Prestamo.objects.filter(fecha_entregado__isnull=True).first()
  print("Antes:", prestamo.id, prestamo.fecha_entregado)
  prestamo.fecha_entregado = date.today()
  prestamo.save()
  prestamo.refresh_from_db()
  print("Después:", prestamo.id, prestamo.fecha_entregado)
  ```
- **Lo que predijimos:** Inicialmente `fecha_entregado` es `None`. Tras asignarle `date.today()` y hacer `save()`, al recargar el registro de la base de datos con `refresh_from_db()`, el valor almacenado será la fecha de hoy.
- **Lo que devolvió:**
  `Antes: 1 None`
  `Después: 1 2026-11-06` (fecha confirmada y persistida en BD).

---

### Reto 10: Borrar un autor y observar qué pasa con sus libros (explicación de la relación y on_delete)
- **Código:**
  ```python
  from biblioteca.models import Autor, Libro
  autor_asimov = Autor.objects.get(nombre="Isaac Asimov")
  libro_fundacion = Libro.objects.get(isbn="9780553293357")
  print("Autores antes de borrar:", list(libro_fundacion.autores.all()))
  autor_asimov.delete()
  print("¿Existe el libro 'Fundación'?:", Libro.objects.filter(isbn="9780553293357").exists())
  libro_fundacion.refresh_from_db()
  print("Autores después de borrar:", list(libro_fundacion.autores.all()))
  ```
- **Lo que predijimos:** Al borrar el autor 'Isaac Asimov', el libro 'Fundación' no se borrará, sino que permanecerá en la base de datos con su lista de autores vacía.
- **Lo que devolvió:**
  - Autores antes de borrar: `[<Autor: Isaac Asimov>]`
  - ¿Existe el libro 'Fundación'?: `True`
  - Autores después de borrar: `[]`
- **Explicación técnica:** La relación entre `Libro` y `Autor` está definida como `ManyToManyField(Autor)`. En las bases de datos relacionales y en Django, esto crea una tabla intermedia oculta (`biblioteca_libro_autores`). Al borrar una instancia de `Autor`, Django elimina en cascada las filas en la tabla intermedia que asocian a ese autor con los libros correspondientes. No se borra la entidad `Libro` porque el libro tiene vida independiente. En Django, a diferencia de `ForeignKey`, los campos `ManyToManyField` no requieren ni aceptan el parámetro `on_delete` directamente en el campo porque la integridad referencial opera sobre la tabla intermedia de unión.


## Fase 6: Reto final: Consultas repetidas (Problema N+1)

El problema de las consultas N+1 ocurre cuando se itera sobre una lista de registros y, por cada uno, se accede a un modelo relacionado que no fue precargado, obligando al ORM a disparar una consulta SQL adicional por cada elemento del bucle.

Para medir con precisión la cantidad de consultas SQL ejecutadas se utilizó `CaptureQueriesContext(connection)` desde el shell de Django.

---

### Caso 1: Recorrer préstamos accediendo al estudiante y al libro de la copia

#### 1. Código sin optimizar
```python
from django.db import connection
from django.test.utils import CaptureQueriesContext
from biblioteca.models import Prestamo

with CaptureQueriesContext(connection) as ctx:
    for p in Prestamo.objects.all():
        print(p.estudiante.nombre, p.copia.libro.titulo)

print(len(ctx), "consultas")
```
- **Predicción antes de medir:**
  - Tenemos 6 préstamos ($N = 6$).
  - 1 consulta inicial para obtener todos los préstamos: `SELECT * FROM biblioteca_prestamo`.
  - Por cada iteración:
    - 1 consulta para resolver la ForeignKey `p.estudiante`.
    - 1 consulta para resolver la ForeignKey `p.copia`.
    - 1 consulta para resolver la ForeignKey `p.copia.libro`.
  - Predicción total: $1 + (6 \times 3) = 19$ consultas.
- **Medición real:** **19 consultas**.

#### 2. Corrección con `select_related`
Dado que `estudiante`, `copia` y `copia.libro` son relaciones `ForeignKey` (hacia un solo objeto), se pueden precargar mediante un solo `SQL JOIN`:
```python
with CaptureQueriesContext(connection) as ctx:
    for p in Prestamo.objects.select_related("estudiante", "copia__libro").all():
        print(p.estudiante.nombre, p.copia.libro.titulo)

print(len(ctx), "consultas")
```
- **Medición después de optimizar:** **1 consulta** (Django resolvió todas las tablas en un único `JOIN`).

---

### Caso 2: Mostrar cada libro con la lista de sus autores

#### 1. Código sin optimizar
```python
from django.db import connection
from django.test.utils import CaptureQueriesContext
from biblioteca.models import Libro

with CaptureQueriesContext(connection) as ctx:
    for libro in Libro.objects.all():
        autores = ", ".join([a.nombre for a in libro.autores.all()])
        print(f"{libro.titulo}: {autores}")

print(len(ctx), "consultas")
```
- **Predicción antes de medir:**
  - Tenemos 5 libros en la base de datos ($N = 5$).
  - 1 consulta inicial para traer todos los libros.
  - 1 consulta individual por cada libro para consultar la relación `libro.autores.all()` mediante la tabla intermedia.
  - Predicción total: $1 + 5 = 6$ consultas.
- **Medición real:** **6 consultas**.

#### 2. Corrección con `prefetch_related`
Como la relación entre `Libro` y `Autor` es de muchos a muchos (`ManyToManyField`), se debe utilizar `prefetch_related`:
```python
with CaptureQueriesContext(connection) as ctx:
    for libro in Libro.objects.prefetch_related("autores").all():
        autores = ", ".join([a.nombre for a in libro.autores.all()])
        print(f"{libro.titulo}: {autores}")

print(len(ctx), "consultas")
```
- **Medición después de optimizar:** **2 consultas** (1 consulta para todos los libros y 1 consulta separada con `WHERE libro_id IN (...)` para todos sus autores; Django hace el ensamble en memoria en Python).

---

### Respuesta a la pregunta: ¿Por qué `select_related` no sirve para el caso de los libros y sus autores?

`select_related` funciona ejecutando un `JOIN` relacional dentro de la misma sentencia SQL. Esto es eficiente para relaciones hacia un único objeto (`ForeignKey` o `OneToOneField`), pues cada registro de la tabla principal se asocia con a lo sumo una fila de la tabla relacionada y el número de filas del resultado no se multiplica.

Por el contrario, en una relación muchos a muchos (`ManyToManyField`) como la de `Libro` y `Autor`:
1. Un `JOIN` generaría un producto cartesiano multiplicando las filas: si un libro tiene 4 autores, se generarían 4 filas duplicando los datos del libro en el conjunto devuelto por la base de datos.
2. Si intentamos forzar `select_related('autores')`, Django lanza una excepción inmediata:  
   `django.core.exceptions.FieldError: Invalid field name(s) given in select_related: 'autores'. Choices are: categoria`
3. Por diseño, Django reserva para las relaciones "a muchos" el método `prefetch_related`, que realiza exactamente 2 consultas limpias sin duplicidad ni sobrecarga en el motor SQL y asocia los objetos directamente en memoria.

---

### Tabla comparativa de optimización

| Consulta | Número de consultas antes | Número después | Técnica utilizada |
| :--- | :---: | :---: | :--- |
| **Préstamo con estudiante y libro** (`p.estudiante.nombre`, `p.copia.libro.titulo`) | 19 consultas | **1 consulta** | `select_related("estudiante", "copia__libro")` |
| **Libro con lista de autores** (`[a.nombre for a in libro.autores.all()]`) | 6 consultas | **2 consultas** | `prefetch_related("autores")` |

 