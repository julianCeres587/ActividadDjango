import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from datetime import date, timedelta
from biblioteca.models import Categoria, Autor, Libro, Copia, Estudiante, Prestamo

def poblar():
    print("Limpiando datos anteriores...")
    Prestamo.objects.all().delete()
    Copia.objects.all().delete()
    Libro.objects.all().delete()
    Autor.objects.all().delete()
    Categoria.objects.all().delete()
    Estudiante.objects.all().delete()

    print("Creando categorías...")
    cat_novela = Categoria.objects.create(nombre="Novela")
    cat_ingenieria = Categoria.objects.create(nombre="Ingeniería")
    cat_historia = Categoria.objects.create(nombre="Historia")

    print("Creando autores...")
    autor_gabo = Autor.objects.create(nombre="Gabriel García Márquez")
    autor_uncle_bob = Autor.objects.create(nombre="Robert C. Martin")
    autor_harari = Autor.objects.create(nombre="Yuval Noah Harari")

    print("Creando libros...")
    libro_soledad = Libro.objects.create(
        isbn="9780307474728",
        titulo="Cien años de soledad",
        anio_publicacion=1967,
        categoria=cat_novela,
        idioma="Español"
    )
    libro_soledad.autores.add(autor_gabo)

    libro_clean = Libro.objects.create(
        isbn="9780132350884",
        titulo="Clean Code",
        anio_publicacion=2008,
        categoria=cat_ingenieria,
        idioma="Inglés"
    )
    libro_clean.autores.add(autor_uncle_bob)

    libro_sapiens = Libro.objects.create(
        isbn="9780062316097",
        titulo="Sapiens",
        anio_publicacion=2014,
        categoria=cat_historia,
        idioma="Español"
    )
    libro_sapiens.autores.add(autor_harari)

    libro_arch = Libro.objects.create(
        isbn="9780134494166",
        titulo="Clean Architecture",
        anio_publicacion=2017,
        categoria=cat_ingenieria,
        idioma="Inglés"
    )
    libro_arch.autores.add(autor_uncle_bob)

    print("Creando copias...")
    copia_sol_1 = Copia.objects.create(codigo_inventario="SO-001", libro=libro_soledad, nota="nuevo")
    copia_sol_2 = Copia.objects.create(codigo_inventario="SO-002", libro=libro_soledad, nota="usado")

    copia_clean_1 = Copia.objects.create(codigo_inventario="CC-001", libro=libro_clean, nota="usado")
    copia_clean_2 = Copia.objects.create(codigo_inventario="CC-002", libro=libro_clean, nota="nuevo")

    copia_sapiens_1 = Copia.objects.create(codigo_inventario="SP-001", libro=libro_sapiens, nota="nuevo")

    copia_arch_1 = Copia.objects.create(codigo_inventario="CA-001", libro=libro_arch, nota="usado")

    print("Creando estudiantes...")
    est_carlos = Estudiante.objects.create(codigo=1151001, nombre="Carlos Gómez", correo="carlos.gomez@ufps.edu.co")
    est_maria = Estudiante.objects.create(codigo=1151002, nombre="María Rodríguez", correo="maria.rodriguez@ufps.edu.co")
    est_juan = Estudiante.objects.create(codigo=1151003, nombre="Juan Pérez", correo="juan.perez@ufps.edu.co")
    est_laura = Estudiante.objects.create(codigo=1151004, nombre="Laura Torres", correo="laura.torres@ufps.edu.co")

    print("Creando préstamos...")
    hoy = date.today()

    # 1. Carlos - Cien años de soledad (copia SO-001) - ACTIVO
    p1 = Prestamo.objects.create(
        estudiante=est_carlos,
        copia=copia_sol_1,
        fecha_limite=hoy + timedelta(days=7),
        fecha_entregado=None
    )

    # 2. Carlos - Clean Code (copia CC-001) - DEVUELTO
    p2 = Prestamo.objects.create(
        estudiante=est_carlos,
        copia=copia_clean_1,
        fecha_limite=hoy - timedelta(days=10),
        fecha_entregado=hoy - timedelta(days=12)
    )

    # 3. María - Cien años de soledad (copia SO-002) - DEVUELTO
    p3 = Prestamo.objects.create(
        estudiante=est_maria,
        copia=copia_sol_2,
        fecha_limite=hoy - timedelta(days=5),
        fecha_entregado=hoy - timedelta(days=6)
    )

    # 4. María - Clean Code (copia CC-001) - ACTIVO
    p4 = Prestamo.objects.create(
        estudiante=est_maria,
        copia=copia_clean_1,
        fecha_limite=hoy + timedelta(days=5),
        fecha_entregado=None
    )

    # 5. Juan - Cien años de soledad (copia SO-002) - ACTIVO
    p5 = Prestamo.objects.create(
        estudiante=est_juan,
        copia=copia_sol_2,
        fecha_limite=hoy + timedelta(days=10),
        fecha_entregado=None
    )

    # 6. Juan - Sapiens (copia SP-001) - ACTIVO
    p6 = Prestamo.objects.create(
        estudiante=est_juan,
        copia=copia_sapiens_1,
        fecha_limite=hoy + timedelta(days=3),
        fecha_entregado=None
    )

    print("Base de datos poblada exitosamente:")
    print(f"- Categorías: {Categoria.objects.count()}")
    print(f"- Autores: {Autor.objects.count()}")
    print(f"- Libros: {Libro.objects.count()}")
    print(f"- Copias: {Copia.objects.count()}")
    print(f"- Estudiantes: {Estudiante.objects.count()}")
    print(f"- Préstamos: {Prestamo.objects.count()} (Activos: {Prestamo.objects.filter(fecha_entregado__isnull=True).count()}, Devueltos: {Prestamo.objects.filter(fecha_entregado__isnull=False).count()})")

if __name__ == "__main__":
    poblar()
