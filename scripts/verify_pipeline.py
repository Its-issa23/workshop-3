import sys
import json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.config import ROOT
from src.storage import connect

with connect() as conn:
    status=dict(conn.execute('SELECT processing_status,count(*) FROM raw_happiness_events GROUP BY 1').fetchall())
    total=conn.execute('SELECT count(*) FROM fact_predictions').fetchone()[0]
    orphan=conn.execute('''SELECT count(*) FROM fact_predictions f LEFT JOIN raw_happiness_events r USING(raw_event_id)
        WHERE r.raw_event_id IS NULL OR r.processing_status <> 'VALID' ''').fetchone()[0]
    invalid_predictions=conn.execute("SELECT count(*) FROM fact_predictions JOIN raw_happiness_events USING(raw_event_id) WHERE processing_status LIKE 'INVALID%'").fetchone()[0]
    metrics=conn.execute("SELECT avg(absolute_error),sqrt(avg(prediction_error*prediction_error)) FROM fact_predictions WHERE evaluation_split='test'").fetchone()
    assert total>0 and orphan==0 and invalid_predictions==0
    assert status.get('RECEIVED',0)==0
    report=dict(status_counts=status,predictions=total,orphan_predictions=orphan,invalid_predictions=invalid_predictions,test_mae=metrics[0],test_rmse=metrics[1])
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/pipeline_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
