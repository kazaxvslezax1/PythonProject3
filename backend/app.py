from fastapi import FastAPI
from analysis_service import analyze_market
from strategy import find_best_timeframe

app = FastAPI(title='Trading analysis (paper only)')


@app.get('/')
def home():
    return {'status':'ok','execution':'paper-only'}


@app.post('/analyze')
def analyze(symbol: str='BTCUSDT', timeframe: str='1h'):
    try:
        data=analyze_market(symbol,timeframe)
        return {k:v for k,v in data.items() if k not in ('frame','technical_signal','as_of')}
    except Exception as exc:
        return {'error':type(exc).__name__, 'action':'HOLD', 'status':'DATA_UNAVAILABLE'}


@app.post('/analyze-smart')
def analyze_smart(symbol: str='BTCUSDT'):
    return analyze(symbol,find_best_timeframe(symbol)['best_timeframe'])
