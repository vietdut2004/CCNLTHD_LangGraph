"""Local deterministic tool-execution evidence; this is NOT a Groq experiment."""
import json
import math
from pathlib import Path
from typing import TypedDict
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, ConfigDict
from telemetry import Trace, trace_scope, emit

class Numbers(BaseModel):
    model_config=ConfigDict(strict=True,allow_inf_nan=False)
    a:float
    b:float

def finite(value):
    if not math.isfinite(value): raise ArithmeticError('NON_FINITE_RESULT')
    return value

@tool(args_schema=Numbers)
def add(a:float,b:float)->float:
    """Add two finite numbers."""
    return finite(a+b)

@tool(args_schema=Numbers)
def multiply(a:float,b:float)->float:
    """Multiply two finite numbers."""
    return finite(a*b)

class State(TypedDict,total=False):
    name:str
    arguments:dict
    result:float
    final:str
    error:str

def execute(state):
    from telemetry import CURRENT
    trace=CURRENT.get()
    run_id=trace.begin_tool(state['name'],state['arguments'])
    try:
        result={'add':add,'multiply':multiply}[state['name']].invoke(state['arguments'])
        trace.end_tool(run_id,state['name'],result=result)
        return {'result':result,'error':''}
    except Exception as exc:
        trace.end_tool(run_id,state['name'],error=type(exc).__name__)
        return {'error':type(exc).__name__}

def finalize(state):
    final='Tool failed: '+state['error'] if state.get('error') else str(state['result'])
    emit('final',answer=final,status='error' if state.get('error') else 'ok')
    return {'final':final}

builder=StateGraph(State)
builder.add_node('execute',execute);builder.add_node('finalize',finalize)
builder.add_edge(START,'execute');builder.add_edge('execute','finalize');builder.add_edge('finalize',END)
graph=builder.compile()

def run_cases(output):
    cases=[('add_ok','add',{'a':5.0,'b':6.0},'11.0'),
           ('multiply_ok','multiply',{'a':5.0,'b':6.0},'30.0'),
           ('invalid_argument','add',{'a':'bad','b':6.0},None),
           ('tool_failure','multiply',{'a':1e308,'b':1e308},None)]
    rows=[]
    for case_id,name,args,expected in cases:
        trace=Trace('none','local_math_no_llm')
        with trace_scope(trace): result=graph.invoke({'name':name,'arguments':args})
        passed=(result['final']==expected) if expected else bool(result.get('error'))
        rows.append({'case_id':case_id,'passed':passed,'result':result,
                     'trace':trace.finish(200 if expected else 422,'OK' if expected else result['error'])})
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    assert all(x['passed'] for x in rows)
    print('PASS: add=11, multiply=30, invalid argument, tool failure; 0 LLM calls')
    return rows

if __name__=='__main__':
    run_cases('.cache/math_traces.json')
