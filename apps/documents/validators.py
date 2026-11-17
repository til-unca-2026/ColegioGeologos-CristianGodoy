from django.core.exceptions import ValidationError
import os

def validate_document_file(value):
    """
    Valida que el archivo subido sea un PDF o Word (.docx/.doc) y no supere el tamaño máximo permitido.
    RNF-14: formato .pdf, .docx, .doc y límite de tamaño configurable (ej. 10 MB).
    """
    valid_extensions = ['.pdf', '.docx', '.doc']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError('Solo se permiten archivos en formato PDF (.pdf) o Word (.docx, .doc).')

    # Límite de 10 MB (10 * 1024 * 1024 bytes)
    max_size_mb = 10
    try:
        if value.size and value.size > max_size_mb * 1024 * 1024:
            raise ValidationError(f'El tamaño del archivo no puede superar los {max_size_mb} MB.')
    except (NotImplementedError, AttributeError):
        pass


def validate_pdf_file(value):
    """
    Alias retrocompatible para validación de documentos.
    """
    return validate_document_file(value)


