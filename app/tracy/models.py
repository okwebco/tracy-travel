"""Modelos de datos de Tracy Travel: Consulta y Reporte.

Se registran sobre la misma Base de SQLAlchemy del proyecto, en tablas
independientes (prefijo tracy_) para no interferir con la app de finanzas.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Consulta(Base):
    """Una consulta acotada de rastreo: vuelo, hospedaje o ambos, con un modo
    de entrega (opción 1: punto único; opción 2: diaria X días)."""
    __tablename__ = "tracy_consultas"

    id = Column(Integer, primary_key=True, index=True)
    whatsapp = Column(String(20), nullable=False)        # 57XXXXXXXXXX
    origen = Column(String(3), nullable=False)           # IATA
    destino = Column(String(3), nullable=False)          # IATA
    macro = Column(String(12), nullable=False)           # vuelo | hospedaje | ambos
    motivo = Column(String(12), nullable=False)          # turismo | negocios | familiar | otros

    fecha_salida = Column(Date, nullable=True)
    fecha_regreso = Column(Date, nullable=True)
    flexible = Column(Boolean, default=False)
    noches = Column(Integer, nullable=True)

    hotel_precio_min = Column(Float, nullable=True)
    hotel_precio_max = Column(Float, nullable=True)
    moneda = Column(String(5), default="COP")

    modo = Column(String(10), nullable=False)            # opcion1 | opcion2
    opcion1_dia = Column(Integer, nullable=True)         # {1,3,5,8,15,30}
    opcion2_dias = Column(Integer, nullable=True)        # 1..8

    estado = Column(String(20), default="pendiente_optin")  # pendiente_optin|activa|finalizada|cancelada
    codigo_optin = Column(String(12), nullable=True, index=True)

    proxima_ejecucion = Column(Date, nullable=True)
    ejecuciones_hechas = Column(Integer, default=0)
    ejecuciones_totales = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reportes = relationship("Reporte", back_populates="consulta", cascade="all, delete-orphan")


class Reporte(Base):
    """Un reporte generado en un checkpoint: Top 3 vuelos / hoteles, total,
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
