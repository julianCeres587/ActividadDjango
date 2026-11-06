Fase 2

-Elijan una, implémentenla y prueben que falla al intentar prestar dos veces la misma copia. En el README
explicarán por qué la eligieron. La documentación oficial está en docs.djangoproject.com.

RTA: Al tratar de prestar dos veces la misma copia,sale "Please correct the error below.   Esta copia ya tiene un prestamo activo", que es como lo definimos en el models.py, enm prestamo, para su constraint.  
Se escogió aplicar la regla de copia prestada con la restricción en la base de datos con constraints, pues el método clean puede estar sujeto a que si se guarda con el shell con .save(), no se ejecuta a no ser que se llame full_clean por uno mismo, en cambio, con el constraint en la base de datos tiene la ventaja de que siempre se cumple, sin importar si el préstamo se crea desde el admin o el shell, además de que la implementación es más corta, queda en pocas líneas dentro de Meta.


Fase 4

Se agrega el filtro EstadoPrestamoFilter, pues en el admin se puede filtrar con fecha_entregado = No date, pero se trata de un caso de una bibliotecaria sin conocimientos técnicos. 


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
 