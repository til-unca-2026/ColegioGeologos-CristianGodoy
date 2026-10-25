# **Arquitectura**

## ***Componentes de la arquitectura***

* **Patrón arquitectónico:** aplicación web cliente-servidor, con Django como backend y capa central de lógica de negocio.  
* **Backend:** Python con Django.

  * Procesa las solicitudes, valida formularios, gestiona la autenticación, aplica permisos por rol y conecta la interfaz con la base de datos y el almacenamiento de archivos. También proporciona Django Admin para la gestión administrativa.

* **Frontend:** HTML, CSS, JavaScript y Tailwind CSS.

  * Sitio institucional, directorio público, panel del matriculado y paneles de gestión. `npm run build:css` compila Tailwind con su CLI; `build.sh` ejecuta ese paso antes de `collectstatic`, que prepara el CSS resultante para WhiteNoise.

* **Autenticación y autorización:** sistema de autenticación y permisos de Django. No se utilizará Supabase Auth en esta propuesta.  
* **Base de datos:** PostgreSQL administrado por Supabase, accedido desde Django mediante su ORM.

  * Almacena usuarios asociados a sus perfiles, matrículas, especialidades, estados, contenidos y referencias a documentos. Django se encarga del acceso a los datos mediante su ORM.

* **Almacenamiento de archivos:** Supabase Storage, con políticas de acceso acordes a la naturaleza pública o privada de cada archivo.

  * Guarda PDF e imágenes. La base de datos conserva sus referencias, mientras que Django controla el acceso según corresponda. Los archivos privados deben almacenarse en espacios privados y no exponerse mediante enlaces públicos permanentes.

* **Despliegue:** Render para alojar la aplicación Django.  
* **Control de versiones:** Git y GitHub.

  * Mantiene el historial del código fuente y permite conectar el repositorio con Render para facilitar los despliegues.

* **Configuración y seguridad:** credenciales y claves almacenadas mediante variables de entorno o mecanismos seguros de configuración. La aplicación se publicará mediante HTTPS.

La arquitectura propuesta centraliza las reglas de negocio y el control de permisos en Django. PostgreSQL se utilizará para los datos estructurados y Supabase Storage para los archivos. Los servicios gratuitos podrán utilizarse inicialmente para la demostración académica, sujeto a sus límites y condiciones vigentes.

**Diagrama**
<img width="968" height="1196" alt="Arquitectura" src="https://github.com/user-attachments/assets/1d6c1ad6-483f-4a57-80ed-7f73127d57bd" />
