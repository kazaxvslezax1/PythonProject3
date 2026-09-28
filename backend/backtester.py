"""Shared-strategy replay. Signals at close; entries next open; no network in simulate."""
import numpy as np
import pandas as pd
from data import get_candles
from market_data import INTERVALS, utc, validate_candles
from strategy_engine import generate_signal, indicator_values
from signal_models import TradePlan
from execution import PaperPosition


def statistics(trades,equity,initial):
    pnl=[t['pnl'] for t in trades]
    wins=[v for v in pnl if v>0]
    losses=[v for v in pnl if v<0]
    gross_loss=-sum(losses)
    values=np.array(equity,dtype=float)
    peaks=np.maximum.accumulate(values)
    dd=(peaks-values)/peaks*100
    return {'total_trades':len(trades),'winning_trades':len(wins),
            'losing_trades':len(pnl)-len(wins),'win_rate':100*len(wins)/len(pnl) if pnl else 0.,
            'total_profit':(values[-1]/initial-1)*100,'avg_profit':np.mean(pnl)/initial*100 if pnl else 0.,
            'max_drawdown':float(dd.max()),
            'profit_factor':sum(wins)/gross_loss if gross_loss else None,
            'net_pnl':float(values[-1]-initial),'initial_capital':initial,'final_capital':float(values[-1])}


def simulate(df,signals,initial=10000.,fee=.001,slippage=.0005,allocation=.1,start_index=60):
    if initial<=0 or not 0<allocation<=1 or not 0<=fee<.1 or not 0<=slippage<.1:
        raise ValueError('Invalid execution settings')
    cash=initial
    position=None
    pending=signals.get(start_index-1)
    trades=[]
    equity=[initial]
    fills=[]
    entry_time=None
    for i in range(start_index,len(df)):
        row=df.iloc[i]
        if pending is not None and position is None and cash>0:
            plan=pending.plan
            sign=1 if plan.direction.value=='LONG' else -1
            entry=float(row.open)*(1+sign*slippage)
            try:
                # Retain original levels; reject gaps crossing stop/first target.
                moved=TradePlan(direction=plan.direction,entry=entry,stop_loss=plan.stop_loss,
                                take_profits=plan.take_profits)
                if moved.rr>=2:
                    position=PaperPosition(moved,cash*allocation/entry,fee,slippage)
                    entry_time=str(row.time)
                    position.enter(row.time)
            except ValueError:
                pass
        pending=None
        if position is not None:
            position.on_bar(row)
            if i==len(df)-1 and position.remaining>1e-10:
                position.close(float(row.close),position.remaining,'END_OF_PERIOD',row.close_time)
            marked=cash+position.mark(float(row.close))
            if position.remaining<=1e-10:
                cash+=position.realized_pnl
                trades.append({'entry_time':entry_time,'exit_time':str(row.close_time),
                               'direction':position.plan.direction.value,'pnl':position.realized_pnl,
                               'profit':position.realized_pnl/(position.quantity*position.plan.entry)*100,
                               'fills':position.fills})
                fills.extend(position.fills)
                position=None
                marked=cash
        else:
            marked=cash
        equity.append(marked)
        signal=signals.get(i)
        if position is None and signal is not None and signal.plan is not None:
            pending=signal
    return {'stats':statistics(trades,equity,initial),'trades':trades,'equity':equity,'fills':fills}


def signals_for(df,symbol,timeframe):
    return {i:generate_signal(df.iloc[:i+1],symbol,timeframe,
                             df.close_time.iloc[i]+pd.Timedelta(milliseconds=1))
            for i in range(59,len(df))}


class AdvancedBacktester:
    def backtest_with_ai_filters(self,symbol,timeframe,days,min_ai_confidence,min_volume_ratio):
        try:
            if timeframe not in INTERVALS or not 1<=days<=3650:
                raise ValueError('Invalid historical period')
            count=int(days*86400/INTERVALS[timeframe])
            cutoff=utc()
            df=get_candles(symbol,timeframe,limit=count+60,as_of=cutoff)
            return self.compare(df,symbol,timeframe,min_ai_confidence,min_volume_ratio,days)
        except Exception as exc:
            return {'error':type(exc).__name__+': '+str(exc)}

    def compare(self,df,symbol,timeframe,min_quality=0,min_volume=0,days=None):
        df=validate_candles(df,timeframe,df.close_time.iloc[-1]+pd.Timedelta(milliseconds=1),min_bars=61)
        signals=signals_for(df,symbol,timeframe)
        selected={i:s for i,s in signals.items() if s.quality>=min_quality and
                  indicator_values(df.iloc[:i+1])['Volume_Ratio']>=min_volume}
        baseline=simulate(df,signals)
        filtered=simulate(df,selected)
        normal,ai=baseline['stats'],filtered['stats']
        n=sum(s.plan is not None for s in signals.values())
        a=sum(s.plan is not None for s in selected.values())
        return {'symbol':symbol,'timeframe':timeframe,'period_days':days,
                'period_start':str(df.time.iloc[60]),'period_end':str(df.close_time.iloc[-1]),
                'comparison':{'normal_trading':normal,'ai_trading':ai},
                'ai_efficiency':{'signals_before_filtering':n,'signals_after_filtering':a,
                                 'signals_filtered':n-a,'bad_signals_caught':None,'filter_efficiency':None,
                                 'risk_reduction_percent':None},
                'improvement':{'profit_improvement':ai['total_profit']-normal['total_profit'],
                               'win_rate_improvement':ai['win_rate']-normal['win_rate'],
                               'risk_reduction':normal['max_drawdown']-ai['max_drawdown'],'trades_filtered':n-a},
                'summary':'Historical heuristic filter comparison; not DeepSeek and not proof of future returns.',
                'baseline':baseline,'filtered':filtered}


backtester=AdvancedBacktester()
