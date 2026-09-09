import posixpath
import uuid

import cloudinary.api
import cloudinary.uploader
import cloudinary.utils
from cloudinary.exceptions import NotFound
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class CloudinaryRawStorage(Storage):
    """
    Almacenamiento de archivos media en Cloudinary.

    Se usa resource_type='raw' porque Aula Virtual almacena
    documentos y archivos generales, no solamente imágenes.
    """

    def _open(self, name, mode="rb"):
        raise NotImplementedError(
            "CloudinaryRawStorage no permite abrir archivos "
            "remotos como archivos locales."
        )

    def _save(self, name, content):
        clean_name = self._clean_name(name)
        unique_name = self._unique_name(clean_name)

        content.seek(0)

        result = cloudinary.uploader.upload(
            content,
            resource_type="raw",
            public_id=unique_name,
            overwrite=False,
        )

        return result["public_id"]

    def delete(self, name):
        if not name:
            return

        cloudinary.uploader.destroy(
            name,
            resource_type="raw",
            invalidate=True,
        )

    def exists(self, name):
        if not name:
            return False

        try:
            cloudinary.api.resource(
                name,
                resource_type="raw",
            )
            return True
        except NotFound:
            return False

    def url(self, name):
        if not name:
            return ""

        url, _ = cloudinary.utils.cloudinary_url(
            name,
            resource_type="raw",
            secure=True,
        )
        return url

    def size(self, name):
        resource = cloudinary.api.resource(
            name,
            resource_type="raw",
        )
        return resource.get("bytes", 0)

    def _clean_name(self, name):
        name = str(name).replace("\\", "/")
        name = posixpath.normpath(name).lstrip("/")
        return name

    def _unique_name(self, name):
        directory, filename = posixpath.split(name)

        if "." in filename:
            stem, extension = filename.rsplit(".", 1)
            filename = (
                f"{stem}_{uuid.uuid4().hex}.{extension}"
            )
        else:
            filename = (
                f"{filename}_{uuid.uuid4().hex}"
            )

        if directory:
            return posixpath.join(
                directory,
                filename,
            )

        return filename
