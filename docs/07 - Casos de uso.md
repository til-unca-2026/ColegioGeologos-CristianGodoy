# **Casos de uso**

| *Código* | *Caso de uso* | *Actor* | *Descripción* |
| :---- | :---- | :---- | :---- |
| CU-01 | Consultar información institucional | Público | Consultar información general, autoridades y datos de contacto del Colegio. |
| CU-02 | Consultar directorio de matriculados | Público | Ver el listado de profesionales, buscar por nombre, apellido o matrícula y filtrar por especialidad. |
| CU-03 | Consultar perfil de un matriculado | Público | Consultar los datos profesionales y el estado de matrícula de un profesional, junto con los datos de contacto autorizados para su publicación. |
| CU-04 | Consultar noticias y eventos | Público | Consultar noticias, novedades y eventos publicados por el Colegio. |
| CU-05 | Iniciar sesión | Matriculado, Colaborador y Administrador | Acceder al sistema mediante nombre de usuario y contraseña. |
| CU-06 | Consultar datos propios | Matriculado | Visualizar sus datos personales y profesionales desde el panel privado. |
| CU-07 | Modificar datos de contacto | Matriculado | Modificar su correo electrónico y teléfono, sin alterar los datos profesionales administrados por el Colegio. |
| CU-08 | Configurar visibilidad de contacto | Matriculado | Decidir de forma independiente si su correo electrónico y su teléfono aparecen en el directorio público. |
| CU-09 | Gestionar contenidos institucionales | Colaborador | Crear y editar noticias, novedades y eventos. |
| CU-10 | Publicar contenidos | Colaborador | Publicar directamente los contenidos gestionados, sin requerir aprobación previa del Administrador. |
| CU-11 | Gestionar matriculados | Administrador | Registrar y modificar datos profesionales, asignar especialidades y actualizar el estado de matrícula. |
| CU-12 | Gestionar cuentas de usuario | Administrador | Crear, modificar, activar o desactivar cuentas y asociar las cuentas correspondientes a los matriculados. |
| CU-13 | Gestionar roles y permisos | Administrador | Administrar los permisos de acceso según los roles definidos. |
| CU-14 | Gestionar contenidos y documentos institucionales | Administrador | Administrar noticias, novedades, eventos y documentos institucionales incluidos en el alcance. |
| CU-15 | Cerrar sesión | Matriculado, Colaborador y Administrador | Finalizar la sesión de usuario. |
| CU-16 | Recuperar contraseña | Matriculado, Colaborador, Administrador | Permitir que un usuario con cuenta registrada solicite el envío de un correo para restablecer sus credenciales de acceso. |

**Relación con los requisitos**

Los casos de uso se vinculan con los requisitos funcionales definidos anteriormente:

* **CU-01 a CU-04:** información institucional y directorio público.  
* **CU-05 y CU-15:** autenticación y cierre de sesión.  
* **CU-06 a CU-08:** funciones del panel del matriculado.  
* **CU-09 y CU-10:** gestión y publicación de contenidos por el Colaborador.  
* **CU-11 a CU-14:** funciones administrativas.

**Diagrama**
<img width="1094" height="1500" alt="Casos de uso" src="https://github.com/user-attachments/assets/413e6f78-8b05-4ecd-9254-5162163b045b" />
