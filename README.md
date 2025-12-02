Nota: Antes de empezar a seguir los pasos, favor de leer todo, ya que vienen varias formas de hacerlo. Proceda con la que desee, si alguna falla, puede seguir con la otra. Para pasar los archivos del repositorio a su
máquina, se recomienda seguir los pasos del .zip por su sencillez. Requisitos previos: tener docker instalado y que el equipo de cómputo tenga soporte de virtualización.   
<br>
<br>
Crea una carpeta en la ruta en donde se desee guardar el proyecto, en este caso, yo elegí "C:\Users\davcm". Lo nombraremos RRHH.
<br>
<br>
<img width="121" height="121" alt="imagen" src="https://github.com/user-attachments/assets/12be30a4-9548-4cca-bbf8-5b85a15be447" />
<br>
<br>
La ruta se puede obtener desde la barra de navegación del explorador de archivos. La copiamos, ya que la vamos a usar.
<br>
<br>
<img width="1027" height="102" alt="imagen" src="https://github.com/user-attachments/assets/eb993b96-d239-415d-a8ee-6d05400bfc3b" />
<br>
<br>
Después, nos iremos a una terminal e ingresaremos el comando "cd [rutaCopiada]", en mi caso es "cd C:\Users\davcm", presionamos enter e ingresamos "cd RRHH", para ingresar a la carpeta del proyecto.
Luego, se ingresa el siguiente comando en la terminal: "git clone https://github.com/davidcllm/basesDeDatosRRHH.git". Una vez que se hayan importado los archivos, se ingresa el comando "docker compose up --build". 
En caso de que el comando de git clone no haya funcionado, favor de descargar el .zip del proyecto, que se encuentra en la página principal de este repositorio, dentro del botón verde "Code".
<br>
<br>
<img width="1146" height="561" alt="imagen" src="https://github.com/user-attachments/assets/db165694-e3c3-409d-aeab-9bf4e63c5736" />
<br>
<br>
Nos vamos a las descargas, donde se encuentra el .zip, se hace click derecho sobre él y se selecciona la opción de "Extraer todo", saldrá una ventana llamada "Extraer carpetas comprimidas (en zip)", y damos click en
"Extraer". Se ingresa en la primera carpeta que sale después de extraer, donde se encontrarán los siguientes archivos:
<br>
<br>
<img width="810" height="230" alt="imagen" src="https://github.com/user-attachments/assets/7aa1a73b-c4fb-41db-81d5-d1b72b0aa1b4" />
<br>
<br>
Copiamos la ruta de la barra de navegación del explorador de archivos, nos vamos a la terminal e ingresamos "cd [rutaCopiada]" en mi caso es "cd C:\Users\davcm\Downloads\basesDeDatosRRHH-main\basesDeDatosRRHH-main".
Al estar en la ruta, ejecutamos "docker compose up --build".
<br>
<br>
<img width="1476" height="362" alt="imagen" src="https://github.com/user-attachments/assets/4c6ce7a0-03e4-43f1-96fb-00f549b284ce" />
<br>
<br>
Si al terminar la generación del contenedor aparece un error como este:
<br>
<br>
<img width="1455" height="173" alt="imagen" src="https://github.com/user-attachments/assets/71bb1d45-25f1-4839-8a11-bc2cdcc9c2de" />
<br>
<br>
Quiere decir que el puerto de la base de datos está ocupado, para solucionarlo abriremos el archivo "docker-compose.yml" con algún editor de código o el bloc de notas, haciendo click derecho sobre el archivo -> 
click en Abrir con -> click en Elegir otra aplicación -> selecciona el bloc de notas.
<br>
<br>
<img width="767" height="217" alt="imagen" src="https://github.com/user-attachments/assets/782c5ba4-1dd0-425f-a0e0-8a832cb5181e" />
<br>
<br>
Al abrir el archivo busca el servcio "db" y en ese servicio busca la sección de ports. Po defecto vendrá el puerto "3307:3307" cambia esa parte por "3308:3308", "3306:3306" o similar, guarda y sal del archivo. 
<br>
<br>
<img width="511" height="385" alt="imagen" src="https://github.com/user-attachments/assets/45dc8259-37a2-4064-882d-a4232f26c5d2" />
<br>
<br>
Otra opción para solucionarlo, es que se puede eliminar el contendor que esté ocupando el puerto en docker desktop:
<br>
<br>
<img width="1573" height="891" alt="imagen" src="https://github.com/user-attachments/assets/73f7daea-81cd-4fb8-abca-c743d9823d71" />
<br>
<br>
Otro posible error, pero poco probable que suceda, es que se tenga un contenedor con el mismo nombre que alguno o varios de los nuestros, si es el caso, favor de eliminar los otros contenedores. Después de cambiar el puerto o eliminar el contenedor que esté ocupando ese puerto, volvemos a ejecutar "docker compose up --build" en la misma ruta del archivo extraído del .zip. 
<br>
<br>
Posteriormente, el contenedor de docker se habrá creado y podremos ingresar a la aplicación por medio del navegador. En la barra de búsqueda ingresamos a "http://localhost:5000/". Para poder ingresar, se creó una cuenta
administradora predeterminada, sus credenciales son: 
<br>
Email: admin@gmail.com
<br>
Contraseña: basesDeDatos123
<br>
<br>
Si se siguieron estos pasos correctamente, la aplicación podrá ser usada. Para detener la ejecución, pulsar Ctrl+C en la terminal si es ejecución en primer plano, o ingresar el comando "docker compose stop" si se está ejecutando en segundo plano. Para ejecutar la aplicación en segundo plano el comando es "docker compose up -d", en primer plano "docker compose up". Para eliminar los contenedores se usa "docker compose down", si se desea eliminar los contenedores, redes y volúmenes de datos se ingresa "docker compose down -v". Todo esto también se puede hacer con el GUI de Docker Desktop, en la sección de "Contenedores". Para detener la aplicación está el ícono del cuadrado, para eliminar el contenedor está el botón rojo. Ambos señalados a continuación:
<br>
<br>
<img width="1186" height="153" alt="imagen" src="https://github.com/user-attachments/assets/e843196d-981b-40b4-81ab-3882b434bc4f" />
<br>
<br>
Para ejecutar la aplicación desde el GUI, se pulsa el botón de "Play" señalado a continuación:
<br>
<br>
<img width="1198" height="158" alt="imagen" src="https://github.com/user-attachments/assets/fb2207e6-cee6-4a4b-876c-1350a7b39f44" />






