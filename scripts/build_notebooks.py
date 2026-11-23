"""Genera notebooks reproducibles; ejecutar desde la raíz del repositorio."""
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
setup = '''from pathlib import Path
import sys
ROOT = Path.cwd() if (Path.cwd() / 'src').exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from src.config import FEATURES
from src.data import load_data, ALIASES
sns.set_theme(style='whitegrid', palette='viridis')
'''

def save(name, cells):
    notebook = nbf.v4.new_notebook(cells=cells)
    notebook.metadata.kernelspec = dict(display_name='Python 3',language='python',name='python3')
    destination = ROOT / 'notebooks' / name
    destination.parent.mkdir(exist_ok=True)
    nbf.write(notebook,destination)

md=nbf.v4.new_markdown_cell
code=nbf.v4.new_code_cell
save('eda.ipynb',[
md('# Exploración y armonización — World Happiness 2015–2019\nObjetivo: identificar diferencias de esquema y justificar una fuente integrada para entrenamiento y simulación de streaming. Cada fila representa un país en un año.'),
code(setup),
code("raw = {year: pd.read_csv(ROOT / 'data/raw' / f'{year}.csv') for year in range(2015,2020)}\nsummary = pd.DataFrame([{'year':y,'rows':len(d),'columns':len(d.columns),'nulls':int(d.isna().sum().sum()),'duplicates':int(d.duplicated().sum())} for y,d in raw.items()])\ndisplay(summary)\nfor year, frame in raw.items():\n    print(year)\n    display(pd.DataFrame({'dtype':frame.dtypes.astype(str),'missing':frame.isna().sum()}))"),
md('## Esquema unificado\n`country` (texto), `year` (entero), seis características numéricas y `happiness_score` (objetivo numérico). `family` agrupa Family/Social support. Son contribuciones del reporte, no cantidades monetarias ni años de vida medidos directamente. La comparabilidad entre ediciones es una limitación de la fuente.'),
code("display(pd.DataFrame([{'unified':k,'source_names':' | '.join(v)} for k,v in ALIASES.items()]))\ndata = load_data()\ndisplay(data.head())\ndisplay(data.describe(include='all').T)\nprint('Duplicados país/año:',data.duplicated(['country','year']).sum())\ndisplay(data[data.isna().any(axis=1)])"),
md('## Decisiones de calidad\n- Se preservan 782 observaciones y se normalizan espacios y dos variantes explícitas de Taiwan/Hong Kong.\n- El único faltante de corrupción se mantiene en la fuente armonizada. En entrenamiento se imputa con la mediana aprendida exclusivamente en el conjunto de entrenamiento. En streaming, el contrato exige números: se guarda el evento original y se rechaza la predicción de ese registro.\n- No se imputan el país, año ni objetivo.\n- Se excluyen rangos, intervalos, errores estándar y Dystopia Residual: son variables derivadas del objetivo o no están en todos los años. Region tampoco está disponible en todos los archivos.\n- No se eliminan automáticamente los extremos: pueden representar diferencias reales entre países.'),
code("numeric = FEATURES + ['happiness_score']\nq1, q3 = data[numeric].quantile(.25), data[numeric].quantile(.75)\niqr = q3-q1\nflags = (data[numeric] < q1-1.5*iqr) | (data[numeric] > q3+1.5*iqr)\ndisplay(flags.sum().rename('potential_outliers').to_frame())\nfig, ax = plt.subplots(figsize=(11,4))\nsns.boxplot(data=data[FEATURES],ax=ax)\nax.set_title('Extremos potenciales: regla IQR, sin eliminación automática')\nplt.show()"),
code("fig, ax = plt.subplots(figsize=(9,6))\nsns.heatmap(data[numeric].corr(),annot=True,fmt='.2f',cmap='YlGnBu',ax=ax)\nax.set_title('Correlaciones exploratorias entre variables')\nplt.show()\nfig, axes = plt.subplots(1,3,figsize=(13,4))\nfor feature, ax in zip(['gdp','family','health'],axes):\n    sns.scatterplot(data=data,x=feature,y='happiness_score',hue='year',palette='viridis',ax=ax,legend=False)\nplt.tight_layout()\nplt.show()"),
md('Las correlaciones son descriptivas, no causales. Se utilizan las seis características comunes por su disponibilidad en el contrato y relación conceptual con el bienestar; no se seleccionan hiperparámetros usando 2019. Los valores atípicos permanecen porque no se verificó que sean errores.'),
code("from src.data import prepare\nprepared = prepare()\nassert len(prepared)==782\nassert not prepared.duplicated(['country','year']).any()\nprint('Fuente armonizada guardada:',prepared.shape)"),
])
save('model_training.ipynb',[
md('# Regresión y evaluación temporal\nEntrenamos con 2015–2018 (626 filas) y evaluamos con 2019 (156). La división temporal sustituye la sugerencia 70/30 para representar la aplicación a un año posterior. País y año se conservan para trazabilidad, no se usan como predictores.'),
code(setup),
md('## Pipeline reproducible\nImputación por mediana → estandarización → regresión lineal. Todo el preprocesamiento se ajusta en entrenamiento y se serializa con el estimador. El puntaje real solo se usa como objetivo/evaluación. No usamos rango, residual ni intervalos del puntaje.'),
code("from src.train import train\nmodel, metadata = train()\ndisplay(pd.Series(metadata['metrics'],name='test_2019'))\nprint('Filas de entrenamiento:',metadata['train_rows'])\nprint('Filas de prueba:',metadata['test_rows'])"),
code("data=load_data()\ntrain_data=data[data.year<2019]\ntest_data=data[data.year==2019]\nfrom sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score\nbaseline=[train_data.happiness_score.mean()]*len(test_data)\ndisplay(pd.DataFrame([{'model':'Media de entrenamiento','mae':mean_absolute_error(test_data.happiness_score,baseline),'rmse':root_mean_squared_error(test_data.happiness_score,baseline),'r2':r2_score(test_data.happiness_score,baseline)},{'model':'Regresión lineal',**metadata['metrics']}]))"),
code("pred=model.predict(test_data[FEATURES])\nfig, axes=plt.subplots(1,2,figsize=(12,4))\naxes[0].scatter(test_data.happiness_score,pred,alpha=.65,color='#137C8B')\naxes[0].plot([2,8],[2,8],'--',color='#DB8E26')\naxes[0].set(xlabel='Puntaje real',ylabel='Predicción',title='Prueba 2019: real vs. predicho')\naxes[1].hist(pred-test_data.happiness_score,bins=20,color='#137C8B')\naxes[1].set(xlabel='Predicho − real',ylabel='Frecuencia',title='Distribución del error')\nplt.tight_layout()\nplt.show()\ndisplay(pd.Series(model.named_steps['regressor'].coef_,index=FEATURES,name='Coeficiente estandarizado'))"),
md('## Interpretación y límites\nMAE y RMSE se expresan en puntos del puntaje; valores menores son mejores. R² compara con la media del conjunto evaluado y puede ser negativo. Los coeficientes no demuestran causalidad. Son pocos años, las ediciones cambian y los mismos países aparecen en entrenamiento/prueba; el resultado representa otro año de países conocidos, no una garantía para países nuevos. Las métricas del dashboard para todos los años incluyen entrenamiento: filtrar `evaluation_split=test` para evaluar generalización.'),
code("import pickle\nimport numpy as np\nrestored=pickle.loads((ROOT/'models/model.pkl').read_bytes())\nnp.testing.assert_allclose(restored.predict(test_data[FEATURES]),pred)\nassert list(restored.feature_names_in_)==FEATURES\nprint('Serialización y orden de características verificados.')"),
])
print('Notebooks generados')
