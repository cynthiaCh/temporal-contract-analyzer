"""This attempt is source-blocked. Do not auto-unlock or launch model endpoints."""
from guards import admission,AdmissionBlocked
if __name__=='__main__':
    try:admission()
    except AdmissionBlocked as e:raise SystemExit('BLOCKED_BEFORE_MODELS: '+str(e))
    raise SystemExit('A newly admitted source set requires a separate frozen execution plan; this offline-only attempt cannot be resumed into a formal search.')
