"""Gate de licencia: el backend rehúsa arrancar sin el secreto correcto.

Protección defensiva, no infalible: cualquiera con acceso de lectura y
escritura al código fuente puede borrar esta verificación (eso aplica a
cualquier protección embebida en código que se distribuye, con o sin IA de
por medio). Lo que sí logra: alguien que clone este repo sin conocer el
secreto no puede simplemente correrlo — el servidor no levanta.

El secreto en texto plano NO vive en el código (solo su hash SHA-256), así
que leer este archivo no revela el valor que hay que poner en LICENSE_KEY.
"""

import hashlib

from .config import settings

_EXPECTED_HASH = "373ff0e73251f86f79a6f0c602ad86dec00a8cd2713f586f7d0856dc20f205be"


class LicenseError(RuntimeError):
    pass


def verify_license() -> None:
    provided = hashlib.sha256(settings.license_key.encode()).hexdigest()
    if provided != _EXPECTED_HASH:
        raise LicenseError(
            "Licencia inválida o ausente (LICENSE_KEY). Este software es "
            "propiedad de josuesolis28 — todos los derechos reservados "
            "(ver LICENSE). Contacta al autor para obtener acceso autorizado."
        )
