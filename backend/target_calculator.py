from trade_targets import targets_for


class TargetCalculator:
    def calculate_targets(self,symbol,timeframe='1h'):
        try:
            return targets_for(symbol,timeframe)
        except Exception as exc:
            return {'error':type(exc).__name__,'direction':'HOLD'}


target_calculator=TargetCalculator()
