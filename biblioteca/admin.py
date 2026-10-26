from django.contrib import admin
from datetime import date
from .models import Categoria, Autor, Libro, Copia, Estudiante, Prestamo
# Register your models here.

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id','nombre')
    search_fields = ('nombre',)
    
@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ('id','nombre')
    search_fields = ('nombre',)

class  CopiaInline(admin.TabularInline):
    model = Copia
    extra = 1  

@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin): 
    list_display = ('titulo', 'isbn', 'categoria', 'anio_publicacion')
    search_fields = ('titulo', 'isbn', 'autores__nombre')
    list_filter = ('categoria', 'anio_publicacion', 'idioma')
    inlines = [CopiaInline]  # Mostrar copias relacionadas en la vista de libro

@admin.register(Copia)
class CopiaAdmin(admin.ModelAdmin):
    list_display = ('codigo_inventario', 'libro', 'nota')
    search_fields = ('codigo_inventario', 'libro__titulo')
    list_filter = ('nota',)

@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'correo')
    search_fields = ('codigo', 'nombre', 'correo')

class EstadoPrestamoFiltro(admin.SimpleListFilter):
        title = 'estado'            # título que se ve arriba del filtro
        parameter_name = 'estado'   # nombre que usa en la URL
        #title y parameter_name los exige SimpleListFilter
    
        def lookups(self, request, model_admin):  #degfine opciones que aparecen en el filtro
        # (valor interno, texto que ve la bibliotecaria)
             return [
                    ('sin_entregar', 'Sin entregar'),
                    ('entregado', 'Entregado'),
                ]

        def queryset(self, request, queryset):
            if self.value() == 'sin_entregar':
                return queryset.filter(fecha_entregado__isnull=True)
            if self.value() == 'entregado':
                return queryset.filter(fecha_entregado__isnull=False)
            return queryset   # si no eligió nada, muestra todos

@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin): 
    list_display = ('estudiante', 'copia', 'fecha_prestamo', 'fecha_limite', 'fecha_entregado')
    search_fields = ('estudiante__nombre', 'estudiante__codigo', 'copia__codigo_inventario', 'copia__libro__titulo')
    list_filter = ('fecha_prestamo', 'fecha_limite', EstadoPrestamoFiltro)
    readonly_fields = ('fecha_prestamo',) 
    actions= ('marcar_devueltos',)

    def marcar_devueltos(self, request, queryset):  #queryset trae los prestamos cuya checkbox esta marcada, esta en actions
        for prestamo in queryset.filter(fecha_entregado__isnull=True):
            prestamo.fecha_entregado = date.today()
            prestamo.save()