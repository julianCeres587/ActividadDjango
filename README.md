Fase 2

-Elijan una, implémentenla y prueben que falla al intentar prestar dos veces la misma copia. En el README
explicarán por qué la eligieron. La documentación oficial está en docs.djangoproject.com.

RTA: Al tratar de prestar dos veces la misma copia,sale "Please correct the error below.   Esta copia ya tiene un prestamo activo", que es como lo definimos en el models.py, enm prestamo, para su constraint.  
Se escogió aplicar la regla de copia prestada con la restricción en la base de datos con constraints, pues el método clean puede estar sujeto a que si se guarda con el shell con .save(), no se ejecuta a no ser que se llame full_clean por uno mismo, en cambio, con el constraint en la base de datos tiene la ventaja de que siempre se cumple, sin importar si el préstamo se crea desde el admin o el shell, además de que la implementación es más corta, queda en pocas líneas dentro de Meta.




Se agrega el filtro EstadoPrestamoFilter, pues en el admin se puede filtrar co fecha_entregado = No date , pero se trata de un caso de una bibliptecaria sin conocimientos técnicos. 