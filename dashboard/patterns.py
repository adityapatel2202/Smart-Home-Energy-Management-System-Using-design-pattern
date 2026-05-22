"""
This file explicitly contains the implementation of the Design Patterns required for the assignment.
- Singleton Pattern
- Factory Pattern
- Observer Pattern
- Strategy Pattern
"""

from abc import ABC, abstractmethod
from typing import List, Any
import logging

logger = logging.getLogger(__name__)

# ==========================================
# 1. Strategy Pattern
# ==========================================
# Context: EnergyUsage calculation
# Matches Section 7.4 of the report

class PricingPlan(ABC):
    @abstractmethod
    def calculate_cost(self, kwh_used: float) -> float:
        pass

class FlatRatePlan(PricingPlan):
    """Standard fixed rate"""
    def __init__(self, rate_per_kwh=0.15):
        self.rate = rate_per_kwh

    def calculate_cost(self, kwh_used: float) -> float:
        return kwh_used * self.rate

class TimeOfUsePlan(PricingPlan):
    """Matches TimeOfUsePlan in report"""
    def __init__(self, base_rate=0.15, peak_multiplier=1.5):
        self.base_rate = base_rate
        self.peak_multiplier = peak_multiplier

    def calculate_cost(self, kwh_used: float, is_peak: bool = False) -> float:
        rate = self.base_rate * self.peak_multiplier if is_peak else self.base_rate
        return kwh_used * rate

class GreenEnergyPlan(PricingPlan):
    """Matches GreenEnergyPlan in report"""
    def __init__(self, base_rate=0.15, discount=0.20):
        self.base_rate = base_rate
        self.discount = discount

    def calculate_cost(self, kwh_used: float) -> float:
        return kwh_used * self.base_rate * (1 - self.discount)

# ==========================================
# 2. Observer Pattern
# ==========================================
# Matches Section 7.3 of the report

class Observer(ABC):
    @abstractmethod
    def update(self, message: str, user=None):
        pass

class HomeownerNotifier(Observer):
    def update(self, message: str, user=None):
        from .models import Alert
        if user:
            Alert.objects.create(user=user, message=f"[Homeowner Alert] {message}")
            print(f"Notified Homeowner {user.username}: {message}")

class TechnicianNotifier(Observer):
    def update(self, message: str, user=None):
        # Technicians respond to faults (Section 2.2)
        print(f"[Technician Alert]: Fault detected or system check required. {message}")

class Subject:
    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer):
        self._observers.append(observer)

    def detach(self, observer: Observer):
        self._observers.remove(observer)

    def notify(self, message: str, user=None):
        for observer in self._observers:
            observer.update(message, user)


# ==========================================
# 3. Factory Pattern
# ==========================================
# Matches Section 7.2 and 6.3 of the report

class ApplianceFactory:
    @staticmethod
    def create_appliance(app_type: str, name: str, user) -> Any:
        from .models import Appliance
        
        # Mapping to specialized types mentioned in report
        # Section 6.3: SmartLight, AirConditioner, Refrigerator
        defaults = {
            'SmartLight': 0.06,
            'AirConditioner': 2.5,
            'Refrigerator': 0.15,
            'Heater': 2.0,
            'Washing Machine': 1.0
        }
        
        power_rating = defaults.get(app_type, 0.5)
        
        return Appliance.objects.create(
            name=name,
            appliance_type=app_type,
            power_rating=power_rating,
            homeowner=user
        )

# ==========================================
# 4. Singleton Pattern
# ==========================================
# Matches Section 7.1 of the report

class EnergyManagementSystem:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EnergyManagementSystem, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.system_status = "Active"
        self._initialized = True
        self.notifier = Subject()
        self.notifier.attach(HomeownerNotifier())
        self.notifier.attach(TechnicianNotifier())

    def record_usage_and_check_threshold(self, appliance, usage_kwh):
        from .models import EnergyUsage, DeviceFault
        
        # Strategy selection matching report names
        strategy_obj = FlatRatePlan()
        if hasattr(appliance.homeowner, 'profile'):
            plan = appliance.homeowner.profile.pricing_plan
            if plan == 'Peak-Hour':
                strategy_obj = TimeOfUsePlan()
            elif plan == 'Renewable':
                strategy_obj = GreenEnergyPlan()
        
        cost = strategy_obj.calculate_cost(usage_kwh)
        
        EnergyUsage.objects.create(
            appliance=appliance,
            energy_consumed=usage_kwh,
            cost=cost
        )
        
        # Trigger Observer
        if usage_kwh > 5.0:
            self.notifier.notify(f"High usage: {usage_kwh} kWh", appliance.homeowner)
        
        # Simulate Fault Detection (Section 2.2)
        if usage_kwh == 0 and appliance.is_on:
            DeviceFault.objects.create(appliance=appliance, description="Device reporting ON but zero usage.")
            self.notifier.notify(f"FAULT DETECTED on {appliance.name}", appliance.homeowner)

