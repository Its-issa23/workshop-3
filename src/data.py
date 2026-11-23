import pandas as pd
from .config import ROOT, FEATURES

ALIASES = {
    'country': ['Country', 'Country or region'],
    'happiness_score': ['Happiness Score', 'Happiness.Score', 'Score'],
    'gdp': ['Economy (GDP per Capita)', 'Economy..GDP.per.Capita.', 'GDP per capita'],
    'family': ['Family', 'Social support'],
    'health': ['Health (Life Expectancy)', 'Health..Life.Expectancy.', 'Healthy life expectancy'],
    'freedom': ['Freedom', 'Freedom to make life choices'],
    'generosity': ['Generosity'],
    'corruption': ['Trust (Government Corruption)', 'Trust..Government.Corruption.', 'Perceptions of corruption'],
}

def load_data():
    frames = []
    for year in range(2015, 2020):
        raw = pd.read_csv(ROOT / 'data' / 'raw' / f'{year}.csv')
        rename = {old: new for new, options in ALIASES.items() for old in options if old in raw.columns}
        frame = raw.rename(columns=rename)[list(ALIASES)].copy()
        frame['country'] = frame['country'].astype('string').str.strip().replace({'Taiwan Province of China': 'Taiwan', 'Hong Kong S.A.R., China': 'Hong Kong'})
        frame['year'] = year
        for col in FEATURES + ['happiness_score']:
            frame[col] = pd.to_numeric(frame[col], errors='raise').astype(float)
        frames.append(frame)
    result = pd.concat(frames, ignore_index=True).drop_duplicates()
    if result.duplicated(['country', 'year']).any():
        raise ValueError('Observaciones ambiguas: país/año duplicado')
    return result[['country', 'year', *FEATURES, 'happiness_score']]

def prepare():
    data = load_data()
    target = ROOT / 'data' / 'processed'
    target.mkdir(parents=True, exist_ok=True)
    data.to_csv(target / 'happiness.csv', index=False)
    return data

if __name__ == '__main__':
    print(prepare().shape)
