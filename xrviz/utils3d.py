import numba

@numba.jit
def is_sorted(a):
    for i in range(a.size-1):
        if a[i+1] < a[i] :
            return False
    return True

def check_levs(is_sorted,levs):
    if is_sorted:
        return levs
    else:
        return levs[::-1]
    
def get_vals(is_sorted,arr,skip_lon,skip_lat,skip_lev):
    if is_sorted:
        return arr[::skip_lon,::skip_lat,::skip_lev]
    else:
        return (arr[::skip_lon,::skip_lat,::skip_lev])[::,::,::-1]