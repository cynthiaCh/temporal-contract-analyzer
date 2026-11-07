"""Exactly one independent tool-free reflection request; never retries."""
from run import OUT,read,save,sha,one
if __name__=='__main__':
 assert (OUT/'K0-complete.json').exists() and not (OUT/'reflection.freeze.json').exists()
 files=[OUT/'reflection.prompt.md',OUT/'difference-feedback.json',OUT/'baseline-review.csv']+[OUT/'runs'/c/'raw-answer.txt' for c in ['a01','a02','a03','a04']]
 save(OUT/'reflection.freeze.json',dict(files={str(p):sha(p.read_bytes()) for p in files},before_request=True))
 slot=next(s for s in read(OUT/'schedule.json')['order'] if s['phase']=='reflection');one(slot,(OUT/'reflection.prompt.md').read_text())
