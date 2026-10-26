from django.db import models

# Create your models here.
class Categoria(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre


class Autor(models.Model): 
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre


class Libro(models.Model):
    titulo = models.CharField(max_length=100)
    autores = models.ManyToManyField(Autor)
    anio_publicacion = models.IntegerField()
    isbn = models.CharField(max_length=13, primary_key=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    idioma = models.CharField(max_length=50,default="Español")

    def __str__(self):
        return self.titulo


class Copia(models.Model):
    #valor guardado, texto visible
    OPCIONES = [ 
        ('nuevo', 'Nuevo'),
        ('usado', 'Usado'),
        ('daniado', 'Dañado'),
    ]
    codigo_inventario = models.CharField(max_length=50, primary_key=True)
    libro = models.ForeignKey(Libro, on_delete=models.PROTECT) 
    nota = models.CharField(max_length=15, choices=OPCIONES)

    def __str__(self):
        return f"Copia {self.pk} del libro {self.libro.titulo}"

class Estudiante(models.Model):
    codigo = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=70)
    correo = models.EmailField(max_length=100) 

    def __str__(self):
        return f"{self.codigo} - {self.nombre}" 

class Prestamo(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.PROTECT)
    copia = models.ForeignKey(Copia, on_delete=models.PROTECT)
    fecha_prestamo = models.DateField(auto_now_add=True)
    fecha_limite = models.DateField()
    fecha_entregado = models.DateField(null=True, blank=True)

#regla de la logica del negocio, implemantada con constraint 
    class Meta: #clase donde se ponen opciones del modelo que no son campos
        constraints = [  #la lista de restricciones que va a tener
            models.UniqueConstraint( #regla de no repetición
                fields=["copia"], #campo al que se aplica
                condition=models.Q(fecha_entregado__isnull=True), #solo incluye en la comparacion los prestamos que la cunplen
                name="una_copia_por_prestamo_activo", #nombre de la restriccion
                violation_error_message="Esta copia ya tiene un prestamo activo")]
    

    def __str__(self):
        return f"Prestamo de {self.copia},  a {self.estudiante}"
