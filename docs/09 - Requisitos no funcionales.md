# **Requisitos no funcionales**

| *Código* | *Requisito no funcional* |
| :---- | :---- |
| RNF-01 | La interfaz deberá adaptarse a computadoras, tabletas y teléfonos móviles. |
| RNF-02 | Las funcionalidades privadas deberán requerir autenticación. |
| RNF-03 | El sistema deberá verificar los permisos en el servidor para impedir operaciones no autorizadas. |
| RNF-04 | Las contraseñas deberán gestionarse mediante los mecanismos seguros de Django, sin almacenarse en texto plano. |
| RNF-05 | Los datos de contacto no autorizados para publicación deberán permanecer inaccesibles desde el directorio público. |
| RNF-06 | Los formularios deberán validar los datos ingresados y comunicar los errores de manera comprensible. |
| RNF-07 | Los datos deberán almacenarse de forma persistente en PostgreSQL. |
| RNF-08 | Los archivos deberán almacenarse en Supabase Storage, aplicando controles de acceso acordes con su carácter público o privado. |
| RNF-09 | La aplicación deberá poder desplegarse en un entorno accesible por Internet. |
| RNF-10 | El código fuente deberá gestionarse mediante Git y alojarse en un repositorio de GitHub. |
| RNF-11 | Las credenciales y configuraciones sensibles deberán gestionarse mediante variables de entorno u otros mecanismos seguros de configuración. |
| RNF-12 | Las funcionalidades principales deberán poder verificarse mediante pruebas funcionales. |
| RNF-13 | El sistema deberá permitir a los usuarios registrados solicitar el restablecimiento de su contraseña mediante el envío de un enlace seguro a su correo electrónico verificado. |
| RNF-14 | La carga de archivos adjuntos (imágenes y documentos) deberá validar el formato (`.jpg`, `.png`, `.pdf`) y limitar el tamaño máximo por archivo a un límite configurable (ej. 5 MB) antes de su procesamiento y posterior almacenamiento en Supabase Storage. |
