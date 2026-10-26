from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

DIAS_PRESTAMO = 7
MULTA_POR_DIA = 0.25  # supuesto, a validar con el bibliotecario


@dataclass
class Usuario:
    id: int
    nombre: str
    tiene_sancion: bool = False
    multa_pendiente: float = 0.0
    prestamos: list = field(default_factory=list)


@dataclass
class Libro:
    id: int
    titulo: str
    disponibles: int


@dataclass
class Prestamo:
    usuario: Usuario
    libro: Libro
    fecha_prestamo: date
    fecha_limite: date
    fecha_devolucion: Optional[date] = None
    estado: str = 'ACTIVO'


class ServicioPrestamos:
    def realizar_prestamo(self, usuario, libro, hoy=None):
        hoy = hoy or date.today()
        if usuario.tiene_sancion or self._tiene_vencidos(usuario, hoy):
            multa = self.multa_pendiente(usuario, hoy)
            raise ValueError(
                f'Usuario bloqueado por sanción pendiente. '
                f'Multa pendiente: {multa:.2f} USD')
        if libro.disponibles <= 0:
            raise ValueError('No hay copias disponibles')
        libro.disponibles -= 1
        prestamo = Prestamo(usuario, libro, hoy,
                            hoy + timedelta(days=DIAS_PRESTAMO))
        usuario.prestamos.append(prestamo)
        return prestamo

    def registrar_devolucion(self, prestamo, hoy=None):
        hoy = hoy or date.today()
        prestamo.fecha_devolucion = hoy
        prestamo.libro.disponibles += 1
        multa = self._multa_por_retraso(prestamo, hoy)
        if multa > 0:
            prestamo.estado = 'CON_RETRASO'
            prestamo.usuario.tiene_sancion = True
            prestamo.usuario.multa_pendiente += multa
            return multa
        prestamo.estado = 'DEVUELTO'
        return 0.0

    def multa_pendiente(self, usuario, hoy):
        """Sanciones ya generadas más la multa de préstamos vencidos sin devolver."""
        total = usuario.multa_pendiente
        for p in usuario.prestamos:
            if p.estado == 'ACTIVO':
                total += self._multa_por_retraso(p, hoy)
        return round(total, 2)

    def _tiene_vencidos(self, usuario, hoy):
        return any(p.estado == 'ACTIVO' and hoy > p.fecha_limite
                   for p in usuario.prestamos)

    def _multa_por_retraso(self, prestamo, hoy):
        dias_retraso = (hoy - prestamo.fecha_limite).days
        return round(max(dias_retraso, 0) * MULTA_POR_DIA, 2)
