# Evidencia de validación local

- Entrenamiento completado: 626 filas, prueba temporal de 156 filas.
- MAE 2019: 0.42420889094311465; RMSE: 0.5496792180531228; R²: 0.7545699894821631.
- Ambos notebooks ejecutados sin celdas con errores: EDA 6 celdas de código; entrenamiento 5.
- Pytest: 17 pruebas aprobadas, incluyendo tres pruebas con PostgreSQL real en esquemas aislados.
- Topic `happiness-events` verificado con 3 particiones y factor de replicación 1.
- Productor real: 784 mensajes confirmados por Kafka en la primera simulación.
- Consumidor real: 781 registros válidos, 3 inválidos, 781 predicciones, cero predicciones huérfanas.
- Modelo Power BI PBIP/PBIR abierto correctamente en Power BI Desktop. La primera actualización requiere ingresar las credenciales locales. La validación visual con datos y las capturas quedan pendientes hasta completar esa conexión.

La evidencia cuantitativa de SQL está en `pipeline_verification.json`. Los conteos aumentarán si se repite la simulación: cada ejecución crea nuevos identificadores.
