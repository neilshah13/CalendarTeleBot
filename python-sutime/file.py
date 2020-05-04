import json
import os
from sutime import SUTime

test_case = u'Training 8pm to 10pm'

jar_files = os.path.join(os.path.dirname(__file__), 'jars')
sutime = SUTime(jars=jar_files, mark_time_ranges=True)

print(json.dumps(sutime.parse(test_case), sort_keys=True, indent=4))