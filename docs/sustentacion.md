# Guía de sustentación

## 1. Problema y arquitectura (1 minuto)

“El proyecto integra cinco archivos históricos con esquemas diferentes. Primero preparo y entreno un modelo. Después simulo eventos con Kafka, los valido, genero predicciones y guardo los resultados en PostgreSQL para consultarlos desde Power BI.”

Explicar por qué el entrenamiento es batch y la inferencia es por evento. El CSV es finito: estamos simulando streaming.

## 2. Datos y modelo (2 minutos)

Mostrar `eda.ipynb`: 782 filas, cambios de columnas, un faltante, sin duplicados exactos. Explicar Family/Social support y por qué no se eliminan todos los outliers. Mostrar entrenamiento: mediana, escalado y regresión guardados juntos. Se prueba con 2019 para respetar el tiempo. MAE ≈ 0.424, RMSE ≈ 0.550, R² ≈ 0.755. No usar rango ni residual evita fuga de información.

## 3. Demo Kafka (2 minutos)

Mostrar servicios saludables en Docker. Ejecutar el consumidor y luego el productor con `--limit 10 --delay 0.5 --demo-invalid`. El topic tiene tres particiones y la clave país agrupa eventos del mismo país. No se promete orden global entre particiones.

Mostrar que el consumidor marca `VALID` e `INVALID_SCHEMA` sin caerse. Consultar las tablas raw y hechos. Un mensaje inválido se conserva exactamente, pero no genera predicción.

## 4. Base y dashboard (2 minutos)

Mostrar dimensiones país y fecha, hechos y la referencia raw_event_id. Diferenciar fecha de emisión del año histórico. Abrir Power BI, actualizar y explicar cantidad, error firmado, MAE, comparación real/predicho y tendencia. Filtrar 2019 para hablar de evaluación fuera del entrenamiento.

## 5. Confiabilidad y límites (1 minuto)

El offset se confirma después de escribir en SQL. Si el proceso cae entre ambas confirmaciones, puede llegar el mismo mensaje otra vez; la clave única evita duplicar hechos. Explicar que se trata de idempotencia, no de una transacción distribuida exactamente una vez. Señalar pocos años, diferencias entre ediciones y actualización manual del informe.

## Preguntas para practicar

- ¿Por qué guardar raw antes de validar? Para auditoría y poder investigar incluso JSON roto.
- ¿Por qué no usar el puntaje real como entrada? Porque es precisamente lo que se quiere predecir.
- ¿Por qué MAE y error promedio? El firmado muestra sesgo; MAE muestra magnitud sin cancelación.
- ¿Por qué no eliminar todos los outliers? Un extremo puede ser una observación válida de un país.
- ¿Qué pasa si llega corrupción null? Se almacena raw y se rechaza la inferencia por contrato.
- ¿Qué pasa al repetir el productor? Es una nueva simulación con nuevos event_id y aumentan los conteos.
- ¿Power BI recibe eventos de Kafka directamente? No: consulta PostgreSQL al actualizar.

Antes de entregar: revisar los notebooks, practicar la demo, guardar las capturas del informe con datos y verificar que el enlace de GitHub permita al profesor acceder.
