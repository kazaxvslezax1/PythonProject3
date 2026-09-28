from datetime import datetime
import pytest
from position_manager import AutoTradeManager


class Bot:
    def send_message(self,*args,**kwargs):
        pass


def test_position_partial_statistics_and_save(tmp_path,monkeypatch):
    m=AutoTradeManager(Bot());m.data_path=tmp_path/'positions.json'
    monkeypatch.setattr(m,'start_monitoring',lambda:None)
    monkeypatch.setattr(m,'_get_current_price',lambda s:100)
    pid=m.create_auto_trade(1,'BTCUSDT',100,98,[102,104,106],'LONG',8,2)
    assert pid
    p=m.active_positions[pid]
    assert p['stop_loss']==98 # no silent tightening
    m._execute_take_profit(p,'TP1',102,102)
    realized=p['realized_pnl_pct']
    m.close_position_manually(pid,100)
    assert p['realized_pnl_pct']<realized # commission on residual
    assert p['realized_pnl_pct']>0
    assert not m.get_active_positions(1)
    assert m.get_trading_statistics(1)['total_pnl']==pytest.approx(p['realized_pnl_pct'])
    restored=AutoTradeManager(Bot());restored.data_path=m.data_path
    assert restored.load_data()
    assert len(restored.trade_history)==1


def test_closed_positions_do_not_exhaust_limit():
    m=AutoTradeManager(Bot())
    m.active_positions={str(i):{'chat_id':1,'status':'CLOSED'} for i in range(10)}
    m.last_trade_time=None
    assert m.should_open_trade(1,'BTCUSDT',8,2)[0]
