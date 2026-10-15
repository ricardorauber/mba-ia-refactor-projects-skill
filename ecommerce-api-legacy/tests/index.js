// Node >= 21 treats `node --test tests/` as a path pattern and loads this
// directory's index instead of discovering files, so register the suites here.
require('./smoke.test');
