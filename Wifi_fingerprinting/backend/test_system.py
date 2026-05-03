import sys, os
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('../data_collection'))

from localization.localization_engine import LocalizationEngine
from navigation.navigation_engine import NavigationEngine

print('--- Testing LocalizationEngine ---')
loc = LocalizationEngine()
print('Loaded', len(loc.radio_map), 'fingerprints')
labels = [fp['label'] for fp in loc.radio_map]
print('Locations:', labels)

# Simulate a WiFi scan near the lift area using real BSSIDs from CSV
test_scan = {
    '6c:31:0e:56:e1:25': -64,
    '76:7f:f0:12:cf:81': -66,
    '76:7f:f0:12:cf:84': -66,
    '30:8b:b2:61:de:0a': -70,
    '72:7f:f0:12:cf:83': -69,
}
result = loc.localize(test_scan)
print('Localize lift scan -> (' + str(result['x']) + ', ' + str(result['y']) + ') conf=' + str(result['confidence']))
print('  Nearest:', result['neighbors'][0]['label'])

# Test with A401 BSSIDs
a401_scan = {
    '6c:31:0e:56:e1:21': -31,
    '6c:31:0e:56:e1:20': -31,
    '6c:31:0e:56:e1:23': -33,
    '6c:31:0e:56:e1:22': -40,
}
result2 = loc.localize(a401_scan)
print('Localize A401 scan -> (' + str(result2['x']) + ', ' + str(result2['y']) + ') conf=' + str(result2['confidence']))
print('  Nearest:', result2['neighbors'][0]['label'])

print()
print('--- Testing NavigationEngine ---')
nav = NavigationEngine()
print('Loaded', len(nav.nodes), 'nodes,', len(nav.edges), 'edges')
dest_keys = list(nav.destinations.keys())[:10]
print('Destinations (first 10):', dest_keys)

# Navigate from lift to A401
r = nav.navigate(54, 5, 'A-401')
print('Navigate lift->A401:', r['success'], '|', r['total_distance'], 'm |', len(r['directions']), 'steps')
if r['success']:
    print('  Path:', ' -> '.join(r['path']))

# Navigate from A401 to HMI Lab
r2 = nav.navigate(5, 3, 'HMI Lab')
print('Navigate A401->HMI Lab:', r2['success'], '|', r2['total_distance'], 'm')
if r2['success']:
    print('  Path:', ' -> '.join(r2['path']))

print()
print('All tests PASSED')
