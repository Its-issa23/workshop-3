-- KPI 1: sesgo (error firmado) y MAE; filtrado al conjunto de prueba.
SELECT AVG(prediction_error) AS mean_error, AVG(absolute_error) AS mae,
       SQRT(AVG(POWER(prediction_error,2))) AS rmse
FROM vw_predictions WHERE evaluation_split='test';
-- KPI 2: predicciones por país.
SELECT country_name, COUNT(*) AS predictions FROM vw_predictions GROUP BY country_name ORDER BY predictions DESC;
-- KPI 3: comparación real/predicho.
SELECT country_name, observation_year, actual_score, predicted_score FROM vw_predictions;
-- KPI 4: tendencia por emisión (streaming), separada del año histórico.
SELECT date_trunc('minute', event_time) AS event_minute, AVG(actual_score) AS actual,
       AVG(predicted_score) AS predicted, COUNT(*) AS predictions
FROM vw_predictions GROUP BY 1 ORDER BY 1;
SELECT * FROM vw_processing_status;
