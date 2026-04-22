from datetime import datetime, timezone
from typing import Optional

class DatetimeUtils:
    @staticmethod
    def utc_to_local(utc_dt: datetime, local_tz: Optional[timezone] = None) -> datetime:
        """
        Convierte un datetime UTC a hora local del sistema o zona personalizada.
        :param utc_dt: Datetime en UTC (puede ser naive o aware).
        :param local_tz: Opcional: zona horaria personalizada (por defecto: del sistema).
        :return: Datetime con hora local.
        """
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)

        return utc_dt.astimezone(local_tz) if local_tz else utc_dt.astimezone()

    @staticmethod
    def format_local_time(utc_dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
        """
        Convierte datetime UTC a string con hora local formateada.
        :param utc_dt: Datetime en UTC.
        :param fmt: Formato de salida strftime.
        :param local_tz: Zona horaria deseada (opcional).
        :return: String con la hora local.
        """
        local_dt = DatetimeUtils.utc_to_local(utc_dt)
        return local_dt.strftime(fmt)

    @staticmethod
    def now() -> datetime:
        """
        Devuelve datetime timezone-aware en UTC.
        Usar este método para timestamps en tokens y expiraciones.
        """
        return datetime.now(timezone.utc)