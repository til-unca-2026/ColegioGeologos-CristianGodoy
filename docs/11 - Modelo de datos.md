# **Modelo de datos**

## ***Definición de las entidades***

**1\. USUARIO**

Representa las cuentas que pueden iniciar sesión en la aplicación.

| *Campo* | *Propósito* |
| :---- | :---- |
| id | Identificador único. |
| nombre\_usuario | Nombre de inicio de sesión, único. |
| nombre, apellido | Datos personales. |
| email, telefono | Datos de contacto. |
| activo | Indica si la cuenta está habilitada. |
| position | Si el usuario integra la comisión directiva. |
| profile\_picture | Foto de perfil del usuario (almacenada en Supabase Storage). |

La contraseña no se almacena como texto ni se incorpora como un campo manual al diagrama: Django gestiona su almacenamiento seguro mediante su sistema de autenticación. Los roles se administran mediante grupos y permisos de Django.

**2\. MATRICULADO**

Representa el perfil profesional de una persona matriculada en el Colegio.

| *Campo* | *Propósito* |
| :---- | :---- |
| id | Identificador interno. |
| numero\_matricula | Número de matrícula, único. |
| titulo | Título profesional. |
| universidad | Universidad de formación. |
| estado | activo, suspendido o dado de baja. |
| email\_publico | Autoriza o impide mostrar el correo en el directorio. |
| telefono\_publico | Autoriza o impide mostrar el teléfono en el directorio. |
| usuario\_id | Cuenta asociada, única y obligatoria. |
| especialidad\_id | Especialidad profesional. |

La cuenta contiene los datos personales y de contacto; el perfil contiene los datos profesionales y las preferencias de visibilidad pública.

**3\. ESPECIALIDAD**

Catálogo de especialidades que el Colegio podrá administrar.

| *Campo* | *Propósito* |
| :---- | :---- |
| id | Identificador único. |
| nombre | Nombre de la especialidad, único. |
| descripcion | Descripción opcional. |

Cada matriculado tendrá exactamente una especialidad en esta versión del modelo. Una especialidad podrá estar asociada a muchos matriculados.

**4\. CONTENIDO**

Almacena noticias, novedades y eventos institucionales.

| *Campo* | *Propósito* |
| :---- | :---- |
| id | Identificador único. |
| tipo | Noticia, novedad o evento. |
| titulo, cuerpo | Contenido publicado. |
| estado\_publicacion | Borrador o publicado. |
| fecha\_evento | Fecha del evento, cuando corresponda. |
| fecha\_publicacion | Fecha de publicación, cuando corresponda. |
| imagen\_storage\_path | Referencia opcional a una imagen. |
| autor\_id | Usuario que crea el contenido. |

El mismo modelo permite que Colaborador y Administrador gestionen contenidos sin duplicar tablas.

**5\. DOCUMENTO**

Representa documentos institucionales y su ubicación de almacenamiento.

| *Campo* | *Propósito* |
| :---- | :---- |
| id | Identificador único. |
| titulo, descripcion | Identificación del documento. |
| categoria | Clasificación documental. |
| archivo\_storage\_path | Referencia al archivo en Supabase Storage. |
| publico | Indica si el documento está destinado al acceso público. |
| subido\_por\_id | Usuario que carga el documento. |

El archivo PDF o la imagen no se guardan directamente en esta tabla: se conserva la referencia al archivo almacenado.

**Diagrama**
<img width="2080" height="1792" alt="Entidad-Relacion" src="https://github.com/user-attachments/assets/918f240b-7856-4bb2-b82c-a0b6eb9fa14c" />
