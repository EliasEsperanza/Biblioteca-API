import pytest
from datetime import date, timedelta
from biblioteca import ServicioPrestamos, Usuario, Libro


def test_prestamo_exitoso_reduce_stock_y_fija_7_dias():
    usuario = Usuario(id=102, nombre='Kevin Rodríguez')
    libro = Libro(id=51, titulo='Clean Code', disponibles=2)
    hoy = date(2026, 3, 2)

    prestamo = ServicioPrestamos().realizar_prestamo(usuario, libro, hoy)

    assert libro.disponibles == 1
    assert prestamo.estado == 'ACTIVO'
    assert prestamo.fecha_limite == hoy + timedelta(days=7)


def test_prestamo_rechazado_si_usuario_tiene_sancion():
    usuario = Usuario(id=101, nombre='Rafael Lino', tiene_sancion=True)
    libro = Libro(id=50, titulo='Ingeniería de Software', disponibles=3)

    with pytest.raises(ValueError, match='Usuario bloqueado por sanción pendiente'):
        ServicioPrestamos().realizar_prestamo(usuario, libro)
    assert libro.disponibles == 3  # el stock no cambia


def test_prestamo_rechazado_muestra_multa_acumulada_de_la_sancion():
    usuario = Usuario(id=107, nombre='Estudiante Sancionado',
                      tiene_sancion=True, multa_pendiente=1.50)
    libro = Libro(id=57, titulo='Code Complete', disponibles=2)

    with pytest.raises(ValueError, match='Multa pendiente: 1.50 USD'):
        ServicioPrestamos().realizar_prestamo(usuario, libro, date(2026, 3, 2))


def test_prestamo_rechazado_si_tiene_prestamo_vencido_sin_devolver():
    usuario = Usuario(id=106, nombre='Estudiante Moroso')
    libro1 = Libro(id=55, titulo='Domain-Driven Design', disponibles=1)
    libro2 = Libro(id=56, titulo='Clean Architecture', disponibles=2)
    servicio = ServicioPrestamos()
    inicio = date(2026, 3, 2)
    servicio.realizar_prestamo(usuario, libro1, inicio)  # vence el 9 de marzo

    # El 13 de marzo lleva 4 días de retraso: 4 x 0.25 = 1.00 USD
    with pytest.raises(ValueError, match='Multa pendiente: 1.00 USD'):
        servicio.realizar_prestamo(usuario, libro2, inicio + timedelta(days=11))
    assert libro2.disponibles == 2


def test_prestamo_permitido_si_otro_prestamo_activo_no_esta_vencido():
    usuario = Usuario(id=108, nombre='Estudiante Puntual')
    libro1 = Libro(id=58, titulo='Refactoring', disponibles=1)
    libro2 = Libro(id=59, titulo='Peopleware', disponibles=1)
    servicio = ServicioPrestamos()
    inicio = date(2026, 3, 2)
    servicio.realizar_prestamo(usuario, libro1, inicio)

    prestamo = servicio.realizar_prestamo(usuario, libro2, inicio + timedelta(days=3))

    assert prestamo.estado == 'ACTIVO'
    assert libro2.disponibles == 0


def test_prestamo_rechazado_si_no_hay_copias():
    usuario = Usuario(id=103, nombre='Meybell Ramírez')
    libro = Libro(id=52, titulo='Refactoring', disponibles=0)

    with pytest.raises(ValueError, match='No hay copias disponibles'):
        ServicioPrestamos().realizar_prestamo(usuario, libro)


def test_devolucion_a_tiempo_no_genera_sancion():
    usuario = Usuario(id=104, nombre='Arturo Esperanza')
    libro = Libro(id=53, titulo='TDD by Example', disponibles=1)
    servicio = ServicioPrestamos()
    inicio = date(2026, 3, 2)
    prestamo = servicio.realizar_prestamo(usuario, libro, inicio)

    multa = servicio.registrar_devolucion(prestamo, inicio + timedelta(days=7))

    assert multa == 0.0
    assert prestamo.estado == 'DEVUELTO'
    assert libro.disponibles == 1
    assert usuario.tiene_sancion is False


def test_devolucion_con_retraso_genera_multa_y_sancion():
    usuario = Usuario(id=105, nombre='Estudiante Demo')
    libro = Libro(id=54, titulo='The Pragmatic Programmer', disponibles=1)
    servicio = ServicioPrestamos()
    inicio = date(2026, 3, 2)
    prestamo = servicio.realizar_prestamo(usuario, libro, inicio)

    multa = servicio.registrar_devolucion(prestamo, inicio + timedelta(days=10))  # 3 días tarde

    assert multa == 0.75
    assert prestamo.estado == 'CON_RETRASO'
    assert usuario.tiene_sancion is True
    assert usuario.multa_pendiente == 0.75
