

def format_trace(varname, var, padding=20):
    return f'{varname:<{padding}}: {var}'

def xray(var, **formatting_kwargs):
    """Return name of variable and its state,
        for logging purposes."""
    
    import inspect, re

    string = inspect.getframeinfo(
        inspect.getouterframes(
        inspect.currentframe()
        )[1][0]).code_context[0]
    
    lpar = [m.start() for m in re.finditer(pattern="\(", string=string)]
    rpar = [m.start() for m in re.finditer(pattern="\)", string=string)]
    ipar = lpar.index(string.find("xray(")+4)
        
    varname = string[lpar[ipar]+1:rpar[-ipar-1]]
    
    return format_trace(varname, var, **formatting_kwargs)