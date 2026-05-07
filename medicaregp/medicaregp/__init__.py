import importlib
import sys


for app_name in ('appointments', 'consultations', 'patients', 'scripts'):
    try:
        sys.modules[f'{__name__}.{app_name}'] = importlib.import_module(app_name)
    except ImportError:
        continue

sys.modules[f'{__name__}.medicaregp'] = sys.modules[__name__]
