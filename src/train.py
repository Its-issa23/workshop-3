import json
import pickle
import hashlib
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from .config import ROOT, FEATURES
from .data import prepare

def train():
    data = prepare()
    train_data = data[data.year < 2019]
    test_data = data[data.year == 2019]
    model = Pipeline([('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler()), ('regressor', LinearRegression())])
    model.fit(train_data[FEATURES], train_data.happiness_score)
    prediction = model.predict(test_data[FEATURES])
    metrics = dict(mae=float(mean_absolute_error(test_data.happiness_score, prediction)),
                   rmse=float(root_mean_squared_error(test_data.happiness_score, prediction)),
                   r2=float(r2_score(test_data.happiness_score, prediction)))
    directory = ROOT / 'models'
    directory.mkdir(exist_ok=True)
    payload = pickle.dumps(model)
    (directory / 'model.pkl').write_bytes(payload)
    metadata = dict(features=FEATURES, train_years=[2015, 2016, 2017, 2018], test_years=[2019],
                    train_rows=len(train_data), test_rows=len(test_data), metrics=metrics,
                    sklearn_version=sklearn.__version__, model_sha256=hashlib.sha256(payload).hexdigest())
    (directory / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    report = ROOT / 'reports'
    report.mkdir(exist_ok=True)
    test_data.assign(predicted_score=prediction).to_csv(report / 'test_predictions.csv', index=False)
    print(json.dumps(metadata, indent=2))
    return model, metadata

if __name__ == '__main__':
    train()
