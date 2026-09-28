from trade_targets import targets_for


class DynamicRRCalculator:
    def __init__(self,ai_checker=None):
        self.ai_checker=ai_checker

    def calculate_adaptive_targets(self,symbol,direction=None,base_stop_loss_percent=.02,min_rr=2.5,
                                   ai_confidence=None,volume_ratio=None,confluence=None):
        try:
            targets=targets_for(symbol,requested_direction=direction)
            if 'error' not in targets and targets['risk_reward_ratio']<min_rr:
                return {'error':'Minimum R/R not met','direction':'HOLD'}
            return targets
        except Exception as exc:
            return {'error':type(exc).__name__,'direction':'HOLD'}

    def calculate_ai_optimized_targets(self,*args,**kwargs):
        return self.calculate_adaptive_targets(*args,**kwargs)

    def calculate_targets_from_signal(self,signal):
        # Never fetch today's prices when replaying an historical signal.
        plan=signal.get('plan')
        if not plan:
            raise ValueError('Historical signal must contain its original plan')
        from signal_models import TradePlan
        plan=TradePlan.model_validate(plan)
        return {'stop_loss':plan.stop_loss,'take_profit':plan.take_profits[-1],'rr_ratio':plan.rr}


dynamic_rr_calculator=DynamicRRCalculator()
