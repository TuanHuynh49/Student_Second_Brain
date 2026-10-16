



def matches_metadata(chunk_meta: dict, query_meta: dict) -> bool:
    """Kiểm tra xem chunk metadata có thỏa mãn tất cả điều kiện trong query metadata hay không."""
    if not query_meta:
        return True
        
    for key, filter_val in query_meta.items():
        chunk_val = chunk_meta.get(key)
        if chunk_val is None:
            return False
            
        filters = [str(v).strip().lower() for v in filter_val] if isinstance(filter_val, list) else [str(filter_val).strip().lower()]
        
        if isinstance(chunk_val, list):
            chunk_vals = [str(v).strip().lower() for v in chunk_val]
            if not any(f in chunk_vals for f in filters):
                return False
        else:
            norm_chunk_val = str(chunk_val).strip().lower()
            if norm_chunk_val not in filters:
                return False
                
    return True