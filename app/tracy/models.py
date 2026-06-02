"""Modelos de datos de Tracy Travel: Consulta y Reporte.

Se registran sobre la misma Base de SQLAlchemy del proyecto, en tablas
independientes (prefijo tracy_) para no interferir con la app de finanzas.
"""
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Consulta(Base):
    """Una consulta acotada de rastreo de vuelos.

    Modos de entrega (ADENDA v2):
      - `rapida`     : 1 búsqueda inmediata, una sola vez.
      - `rastreo`    : casillas acumulativas {1,3,5,8,15,30}; informa en cada día
                       marcado (día 1 = inmediato). Termina en el último marcado.
      - `seguimiento`: N rastreos (2..6) cada `seguimiento_frecuencia` días;
                       el #1 es inmediato y luego cada N días.
    """
    __tablename__ = "tracy_consultas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(60), nullable=False)          # nombre de la persona
    apellido = Column(String(60), nullable=False)        # apellido de la persona
    whatsapp = Column(String(20), nullable=False)        # 57XXXXXXXXXX
    origen = Column(String(3), nullable=False)           # IATA
    destino = Column(String(3), nullable=False)          # IATA
    motivo = Column(String(12), nullable=False)          # turismo | negocios | familiar | otros
    # Tipo de viaje: ida | regreso | ida_regreso
    tipo_viaje = Column(String(12), nullable=False, default="ida_regreso")

    fecha_salida = Column(Date, nullable=True)
    fecha_regreso = Column(Date, nullable=True)
    flexible = Column(Boolean, default=False)
    moneda = Column(String(5), default="COP")

    modo = Column(String(12), nullable=False)            # rapida | rastreo | seguimiento
    # Rastreo: CSV de días marcados (acumulativos), p. ej. "1,3,5,8".
    rastreo_dias = Column(String(40), nullable=True)
    # Seguimiento: cantidad de rastreos (2..6) y frecuencia en días.
    seguimiento_cantidad = Column(Integer, nullable=True)
    seguimiento_frecuencia = Column(Integer, nullable=True)

    estado = Column(String(20), default="pendiente_optin")  # pendiente_optin|activa|finalizada|cancelada
    codigo_optin = Column(String(12), nullable=True, index=True)

    proxima_ejecucion = Column(Date, nullable=True)
    ejecuciones_hechas = Column(Integer, default=0)
    ejecuciones_totales = Column(Integer, default=1)
    # Fechas exactas de cada checkpoint (CSV ISO), calculadas al activar.
    # La primera entrada es la entrega inmediata (#1).
    checkpoints = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reportes = relationship("Reporte", back_populates="consulta", cascade="all, delete-orphan")


class Reporte(Base):
    """Un reporte generado en un checkpoint: Top 3 vuelos, precio de referencia,
    frase de recomendación, enlaces. Se sirve en /{numero} y expira a las 48 h."""
    __tablename__ = "tracy_reportes"

    id = Column(Integer, primary_key=True, index=True)
    consulta_id = Column(Integer, ForeignKey("tracy_consultas.id"), nullable=False)
    numero = Column(String(20), index=True, nullable=False)  # = whatsapp (slug de /{numero})
    payload_json = Column(Text, nullable=False)
    enviado = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    consulta = relationship("Consulta", back_populates="reportes")
