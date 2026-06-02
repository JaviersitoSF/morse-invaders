# Plan de implementacion para Morse Invaders

Este plan esta escrito para avanzar en sesiones cortas, con feedback rapido y cambios faciles de revertir. La meta no es "aprender pygame completo"; la meta es mejorar el juego un pedazo a la vez, probando cada pedazo en menos de 10 minutos.

## Regla principal de trabajo

Trabaja en bloques de 25 a 45 minutos.

En cada bloque:

1. Elige una sola tarea pequena.
2. Lee solo el codigo necesario.
3. Cambia pocas lineas.
4. Ejecuta el juego.
5. Prueba manualmente una cosa especifica.
6. Anota que funciono y que falta.

Si una tarea crece demasiado, no la termines a la fuerza. Dividela.

## Preparacion inicial

Antes de tocar funcionalidades nuevas, deja el ambiente comodo.

Temas para investigar:

- Como ejecutar un script Python desde terminal.
- Que es un virtualenv y por que se usa `venv/bin/python`.
- Flujo basico de pygame: `init`, ventana, eventos, `update`, `draw`, `clock.tick`.
- Como leer errores de Python: archivo, linea, tipo de error.

Pasos:

1. Ejecuta el juego:

   ```bash
   /home/javier/morse_invaders/venv/bin/python main.py
   ```

2. Juega 2 minutos sin cambiar codigo.
3. Abre estos archivos y reconoce su responsabilidad:
   - `main.py`: ventana, loop principal, input, dibujo, audio y reglas generales.
   - `Invader.py`: datos y comportamiento de cada invasor.
   - `morse.py`: conversion de texto a codigo Morse.
   - `levels.py`: dificultad, palabras, velocidad y puntos.

Feedback rapido:

- Si el juego abre, la preparacion esta lista.
- Si no abre, arregla solo el error de arranque antes de seguir.

Definicion de listo:

- Puedes abrir el juego desde terminal.
- Puedes cerrar con `Esc`.
- Sabes en que archivo buscar niveles, invasores y codigo Morse.

## Fase 1: Crear un ciclo seguro de cambios

Objetivo: poder cambiar algo pequeno y verificarlo inmediatamente.

Temas para investigar:

- Que significa una constante en Python.
- Como pygame usa colores RGB: `(rojo, verde, azul)`.
- Como `pygame.font.Font` crea tamanos de texto.

Tareas pequenas:

1. Cambia temporalmente el color `BG` en `main.py`.
2. Ejecuta el juego.
3. Confirma visualmente que el fondo cambio.
4. Devuelve el color original o elige uno definitivo.
5. Cambia el texto inicial de `self.message`.
6. Ejecuta otra vez y confirma que aparece en el HUD.

Feedback rapido:

- Cada cambio debe ser visible al abrir el juego.
- Si no ves el cambio en 2 minutos, revisa si editaste el archivo correcto.

Definicion de listo:

- Puedes hacer un cambio visual pequeno.
- Puedes ejecutar y confirmar el resultado sin leer todo el programa.

## Fase 2: Entender el loop del juego

Objetivo: saber donde poner cambios sin romper el flujo principal.

Temas para investigar:

- Diferencia entre input, update y draw.
- Que es `dt` y para que sirve el tiempo en videojuegos.
- Que hace `pygame.event.get()`.
- Que hace `pygame.display.flip()`.

Mapa del loop actual:

- `Game.run()` mantiene el juego vivo.
- `handle_events()` lee teclado, mouse y cerrar ventana.
- `update(dt)` mueve invasores, reproduce Morse, crea nuevos invasores y revisa vidas.
- `draw()` limpia pantalla, dibuja HUD, invasores y game over.

Tareas pequenas:

1. Agrega temporalmente un mensaje en pantalla cuando se presiona `Tab`.
2. Prueba que `Tab` cambia el objetivo.
3. Agrega temporalmente un cambio de mensaje cuando haces click en un invasor.
4. Prueba con un solo click.

Feedback rapido:

- No uses `print` como unica prueba si el resultado puede verse en pantalla.
- El HUD es tu tablero de feedback inmediato.

Definicion de listo:

- Puedes decir si un cambio pertenece a input, update o draw.
- Puedes encontrar rapidamente donde se maneja una tecla.

## Fase 3: Mejorar la experiencia de aprendizaje Morse

Objetivo: hacer que el juego ayude mas al jugador a aprender, no solo a sobrevivir.

Temas para investigar:

- Tabla Morse: letras faciles y letras parecidas.
- Aprendizaje espaciado: repetir lo que el jugador falla.
- Diferencia entre reconocimiento auditivo y reconocimiento visual.

Ideas de tareas pequenas:

1. Mostrar la letra correcta durante 1 segundo cuando un invasor llega al suelo.
2. Guardar la ultima respuesta fallida en `self.message`.
3. Agregar un modo de practica lenta en `levels.py`.
4. Repetir mas seguido las letras que el jugador falla.
5. Mostrar una pista opcional despues de varios errores.

Orden recomendado:

1. Empieza con mensajes en HUD.
2. Luego ajusta niveles.
3. Despues agrega memoria de errores.

Feedback rapido:

- Para cada mejora, juega solo 1 minuto y pregunta: "me ayudo a aprender o solo agrego ruido?"
- Si una pista hace el juego demasiado facil, dejala solo para errores repetidos.

Definicion de listo:

- El jugador recibe feedback claro cuando falla.
- Los primeros niveles se sienten como entrenamiento, no como castigo.

## Fase 4: Separar logica pura de pygame

Objetivo: poder probar partes del juego sin abrir una ventana.

Temas para investigar:

- Que es una funcion pura.
- Que es `unittest` o `pytest`.
- Por que `morse.py` es mas facil de probar que `main.py`.
- Dataclasses en Python.

Tareas pequenas:

1. Agrega pruebas para `morse.encode`.
2. Agrega pruebas para `Invader.can_accept`.
3. Agrega pruebas para `Invader.accept`.
4. Agrega pruebas para `get_level`.

Ejemplos de cosas probables:

- `encode("SOS")` debe devolver `"... --- ..."`.
- Un invasor con texto `"CAT"` debe aceptar `"C"` al inicio.
- El nivel final debe repetirse si se pide un indice muy alto.

Feedback rapido:

- Las pruebas deben correr en segundos.
- Corre las pruebas despues de cada cambio de logica.

Definicion de listo:

- Hay pruebas para Morse, invasores y niveles.
- Puedes cambiar reglas pequenas con menos miedo.

## Fase 5: Hacer el movimiento independiente del FPS

Objetivo: que la velocidad del juego sea consistente aunque cambie el rendimiento.

Temas para investigar:

- Que es FPS.
- Que significa delta time.
- Por que `move()` deberia usar tiempo y no solo sumar una cantidad fija por frame.

Situacion actual:

- `update(dt)` recibe `dt`.
- `Invader.move()` no usa `dt`.
- La velocidad depende de cuantas veces por segundo se llama `move()`.

Tareas pequenas:

1. Cambia `Invader.move()` para recibir `dt`.
2. Convierte `dt` de milisegundos a segundos.
3. Decide que `speed` signifique pixeles por segundo.
4. Ajusta los valores de `speed` en `levels.py`.
5. Prueba si el juego se siente parecido al anterior.

Feedback rapido:

- Antes de cambiar, mira cuanto tarda un invasor en llegar al suelo.
- Despues de cambiar, compara la sensacion.
- No ajustes todos los niveles a la vez si el primero ya se siente mal.

Definicion de listo:

- `dt` afecta el movimiento.
- El primer nivel sigue siendo jugable.
- Cambiar `FPS` no cambia dramaticamente la velocidad.

## Fase 6: Mejorar audio Morse

Objetivo: que el sonido ayude al reconocimiento y sea agradable.

Temas para investigar:

- Timing Morse: punto, raya, espacio entre simbolos, letras y palabras.
- Como funciona `pygame.mixer`.
- Que es frecuencia de audio en Hz.
- Diferencia entre volumen, frecuencia y duracion.

Tareas pequenas:

1. Agrega constantes para frecuencia y volumen.
2. Prueba 3 frecuencias: 600, 720, 850.
3. Prueba 2 velocidades de unidad: 140 ms y 180 ms.
4. Agrega una tecla para repetir el Morse del invasor activo.
5. Si no hay invasor activo, repetir el invasor mas bajo.

Feedback rapido:

- Haz cambios de audio de uno en uno.
- Juega con audifonos y sin audifonos.
- Si el audio cansa en 2 minutos, bajale volumen o frecuencia.

Definicion de listo:

- El jugador puede repetir una senal.
- El audio se entiende sin ser molesto.

## Fase 7: Mejorar seleccion de objetivo

Objetivo: reducir frustracion cuando hay varios invasores en pantalla.

Temas para investigar:

- Hitboxes en pygame.
- Orden de dibujo y seleccion.
- UX basica: feedback visual de seleccion.

Tareas pequenas:

1. Hacer mas visible el invasor activo.
2. Agregar un borde o fondo tenue al activo.
3. Al escribir una letra, priorizar el invasor activo si coincide.
4. Si varios coinciden, elegir el mas bajo.
5. Mostrar un mensaje cuando ninguna senal coincide.

Feedback rapido:

- Crea varios invasores y usa `Tab`.
- Haz click en uno y escribe.
- Pregunta: "entiendo cual estoy atacando?"

Definicion de listo:

- El objetivo activo se reconoce de inmediato.
- Escribir se siente predecible.

## Fase 8: Pulir niveles y dificultad

Objetivo: que el juego tenga una curva clara de aprendizaje.

Temas para investigar:

- Curvas de dificultad en juegos pequenos.
- Como ordenar letras Morse de faciles a dificiles.
- Balance: velocidad, cantidad de enemigos, longitud de palabras.

Tareas pequenas:

1. Ajustar nivel 1 solo con letras muy comunes.
2. Agregar numeros en un nivel posterior.
3. Separar palabras cortas y largas.
4. Reducir velocidad cuando las palabras sean mas largas.
5. Agregar nombres descriptivos a niveles si ayuda al HUD.

Feedback rapido:

- Juega cada nivel por separado si agregas una forma temporal de empezar en ese nivel.
- Cambia solo una variable por prueba: velocidad, spawn o palabras.

Definicion de listo:

- El nivel 1 ensena.
- Los niveles medios retan.
- El nivel final no se siente injusto.

## Fase 9: Agregar menus simples

Objetivo: dar control al jugador sin construir una interfaz complicada.

Temas para investigar:

- Estados de juego: menu, jugando, pausa, game over.
- Como dibujar botones simples con pygame.
- Como manejar clicks por rectangulos.

Tareas pequenas:

1. Agregar pantalla inicial con `Enter` para jugar.
2. Agregar pausa con `P`.
3. Mostrar controles en la pantalla inicial.
4. Agregar opcion de practica lenta.

Feedback rapido:

- Cada pantalla nueva debe tener una forma obvia de salir.
- Prueba teclado antes de dibujar botones.

Definicion de listo:

- El jugador puede empezar, pausar, reiniciar y salir sin confusion.

## Fase 10: Guardar progreso local

Objetivo: recordar mejores puntajes o estadisticas sin servidor.

Temas para investigar:

- Archivos JSON en Python.
- Manejo seguro de archivos que no existen.
- Que datos vale la pena guardar.

Tareas pequenas:

1. Guardar mejor puntaje.
2. Mostrar mejor puntaje en HUD o game over.
3. Guardar conteo de errores por letra.
4. Usar errores para recomendar practica.

Feedback rapido:

- Cierra y abre el juego para confirmar que el dato persiste.
- Borra temporalmente el archivo de guardado y confirma que no crashea.

Definicion de listo:

- El mejor puntaje persiste.
- Si el archivo falta o esta vacio, el juego arranca igual.

## Checklist antes de cada cambio

- Que archivo voy a tocar?
- Que comportamiento espero ver?
- Como lo pruebo en menos de 5 minutos?
- Que hago si rompe el juego?

## Checklist despues de cada cambio

- El juego abre?
- `Esc` cierra?
- La funcion nueva se ve o se siente?
- El cambio fue pequeno?
- Hay algo que anotar para despues?

## Prioridad recomendada

1. Feedback visual y mensajes claros.
2. Pruebas para `morse.py`, `Invader.py` y `levels.py`.
3. Movimiento con `dt`.
4. Repetir audio del objetivo activo.
5. Balance de niveles.
6. Menu inicial y pausa.
7. Guardar mejor puntaje.

## Regla anti-atasco

Si pasas mas de 15 minutos sin ver progreso:

1. Vuelve al ultimo cambio pequeno que funcionaba.
2. Escribe en una nota que estabas intentando.
3. Reduce la tarea a la mitad.
4. Prueba con un cambio visible, aunque sea temporal.

El objetivo es mantener el juego siempre ejecutable. Un juego que abre y da feedback vale mas que una gran mejora a medio construir.
