"""Proyecto PBIP/PBIR editable con origen PostgreSQL (no CSV)."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'dashboards'
BASE='https://developer.microsoft.com/json-schemas/fabric/item/report/'
def write(path,data):
    path=ROOT/path
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

write(Path('Happiness.pbip'),{'version':'1.0','artifacts':[{'report':{'path':'Happiness.Report'}}],'settings':{'enableAutoRecovery':True}})
write(Path('Happiness.SemanticModel/definition.pbism'),{'version':'1.0','settings':{}})
columns={'prediction_id':'int64','country_name':'string','observation_year':'int64','actual_score':'double','predicted_score':'double','prediction_error':'double','absolute_error':'double','event_time':'dateTime','prediction_timestamp':'dateTime','evaluation_split':'string','latency_ms':'double'}
measures={
    'Predicciones':('COUNTROWS(Predicciones)','0'),
    'MAE':('AVERAGE(Predicciones[absolute_error])','0.000'),
    'Error promedio':('AVERAGE(Predicciones[prediction_error])','0.000'),
    'RMSE':('SQRT(AVERAGEX(Predicciones,POWER(Predicciones[prediction_error],2)))','0.000'),
    'Puntaje real':('AVERAGE(Predicciones[actual_score])','0.00'),
    'Puntaje predicho':('AVERAGE(Predicciones[predicted_score])','0.00'),
    'MAE prueba 2019':('CALCULATE([MAE],Predicciones[evaluation_split]="test")','0.000'),
    'Latencia media ms':('AVERAGE(Predicciones[latency_ms])','0.0'),
}
table={'name':'Predicciones','columns':[{'name':k,'dataType':v,'sourceColumn':k,'summarizeBy':'none'} for k,v in columns.items()],
       'measures':[{'name':k,'expression':v[0],'formatString':v[1]} for k,v in measures.items()],
       'partitions':[{'name':'Predicciones','mode':'import','source':{'type':'m','expression':[
           'let', '    Source = PostgreSQL.Database("localhost:5433", "happiness", [CreateNavigationProperties=false]),',
           '    Data = Source{[Schema="public",Item="vw_predictions"]}[Data]', 'in', '    Data']}}]}
write(Path('Happiness.SemanticModel/model.bim'),{'name':'Happiness','compatibilityLevel':1567,'model':{'culture':'es-CO','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-US','tables':[table],'annotations':[{'name':'PBI_QueryOrder','value':'["Predicciones"]'},{'name':'__PBI_TimeIntelligenceEnabled','value':'0'}]}})
write(Path('Happiness.Report/definition.pbir'),{'$schema':BASE+'definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../Happiness.SemanticModel'}}})
report=Path('Happiness.Report/definition')
write(report/'version.json',{'$schema':BASE+'definition/versionMetadata/1.0.0/schema.json','version':'2.0.0'})
write(report/'report.json',{'$schema':BASE+'definition/report/3.0.0/schema.json','themeCollection':{},'settings':{'useStylableVisualContainerHeader':True}})
write(report/'pages/pages.json',{'$schema':BASE+'definition/pagesMetadata/1.0.0/schema.json','pageOrder':['Overview','Detail'],'activePageName':'Overview'})
def literal(value):
    return {'expr':{'Literal':{'Value':("'"+value.replace("'","''")+"'") if isinstance(value,str) else ('true' if value is True else 'false' if value is False else str(value)+'D')}}}
def color(value):
    return {'solid':{'color':literal(value)}}
def page(name,title):
    write(report/f'pages/{name}/page.json',{'$schema':BASE+'definition/page/2.0.0/schema.json','name':name,'displayName':title,'displayOption':'FitToPage','height':800,'width':1280,'objects':{'background':[{'properties':{'color':color('#F1F5F9'),'transparency':literal(0)}}]}})
def field(name,measure=False):
    kind='Measure' if measure else 'Column'
    return {'field':{kind:{'Expression':{'SourceRef':{'Entity':'Predicciones'}},'Property':name}},'queryRef':f'Predicciones.{name}','nativeQueryRef':name}
def visual(page_name,name,kind,title,pos,roles):
    obj={'$schema':BASE+'definition/visualContainer/2.0.0/schema.json','name':name,'position':dict(zip(['x','y','width','height'],pos),z=0,tabOrder=0),
         'visual':{'visualType':kind,'query':{'queryState':{role:{'projections':[field(n,m) for n,m in items]} for role,items in roles.items()}},
                   'visualContainerObjects':{'title':[{'properties':{'show':literal(True),'text':literal(title),'fontSize':literal(13),'fontColor':color('#17324D')}}],
                                             'background':[{'properties':{'show':literal(True),'color':color('#FFFFFF'),'transparency':literal(0)}}]}}}
    write(report/f'pages/{page_name}/visuals/{name}/visual.json',obj)
page('Overview','01 | Felicidad y predicciones')
page('Detail','02 | Trazabilidad y tendencias')
for i,(measure,title) in enumerate([('Predicciones','PREDICCIONES'),('MAE','ERROR ABSOLUTO MEDIO'),('Error promedio','ERROR PROMEDIO · PREDICHO − REAL'),('MAE prueba 2019','MAE · PRUEBA 2019')]):
    visual('Overview',f'card{i}','card',title,(20+i*315,20,300,130),{'Values':[(measure,True)]})
visual('Overview','year','slicer','Año histórico',(20,170,220,150),{'Values':[('observation_year',False)]})
visual('Overview','split','slicer','Conjunto de evaluación',(20,340,220,150),{'Values':[('evaluation_split',False)]})
visual('Overview','country','slicer','País',(20,510,220,270),{'Values':[('country_name',False)]})
visual('Overview','countries','clusteredBarChart','Predicciones por país',(260,170,490,280),{'Category':[('country_name',False)],'Y':[('Predicciones',True)]})
visual('Overview','comparison','scatterChart','Puntaje real vs. predicho · cada país',(770,170,490,280),{'Category':[('country_name',False)],'X':[('Puntaje real',True)],'Y':[('Puntaje predicho',True)]})
visual('Overview','trend','lineChart','Tendencia por año histórico',(260,470,1000,310),{'Category':[('observation_year',False)],'Y':[('Puntaje real',True),('Puntaje predicho',True)]})
visual('Detail','stream','lineChart','Predicciones por momento de emisión (UTC)',(20,20,1240,320),{'Category':[('event_time',False)],'Y':[('Puntaje real',True),('Puntaje predicho',True)]})
visual('Detail','rows','tableEx','Trazabilidad de las predicciones',(20,360,1240,420),{'Values':[(n,False) for n in ['prediction_id','country_name','observation_year','actual_score','predicted_score','prediction_error','evaluation_split','event_time']]})
print('Proyecto Power BI generado:',ROOT/'Happiness.pbip')
