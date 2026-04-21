from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, Float, BigInteger


Base = declarative_base()

class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True)
    schema_version = Column(Integer)
    device_id = Column(String)
    sensor = Column(String)
    sensor_value = Column(Float)
    unit = Column(String)
    ts_ms = Column(BigInteger)
    seq = Column(Integer)
    # received_at = Column(DateTime(timezone=True))

    def to_dict(self):
        return {
            "id": self.id,
            "schema_version": self.schema_version,
            "device_id": self.device_id,
            "sensor": self.sensor,
            "sensor_value": self.sensor_value,
            "unit": self.unit,
            "ts_ms": self.ts_ms,
            # "received_at": self.received_at.isoformat() if self.received_at else None
        }

    @staticmethod
    def list_to_dict(items):
        return [item.to_dict() for item in items]


# CREATE TABLE IF NOT EXISTS measurements (
#     id             SERIAL  PRIMARY KEY,
#     schema_version TEXT    NOT NULL,
#     device_id      TEXT    NOT NULL,
#     sensor         TEXT    NOT NULL,
#     sensor_value   REAL    NOT NULL,
#     unit           TEXT    NOT NULL,
#     ts_ms          BIGINT  NOT NULL,
#     seq            INTEGER NOT NULL
# );