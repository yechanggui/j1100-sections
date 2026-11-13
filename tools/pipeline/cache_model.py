import sys, time, pickle, numpy as np
from keyparse import read_key, to_arrays
t = time.time(); m = read_key(sys.argv[1]); print('parsed', len(m['nodes']), 'nodes', len(m['shells']), 'shells', len(m['parts']), 'parts', round(time.time() - t), 's', flush=True)
xyz, tri, pid = to_arrays(m)
np.savez(sys.argv[2], xyz=xyz, tri=tri, pid=pid, part_ids=np.array(list(m['parts'].keys())), part_titles=np.array(list(m['parts'].values())))
print('saved', xyz.shape, tri.shape, 'bbox', xyz.min(0), xyz.max(0), round(time.time() - t), 's')
