from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT_EXCLUDES={'.git','.pytest_cache','__pycache__','Runs','state'}
SECRET_PATTERNS={
 'REAL_SECRET': re.compile(r'(?i)(?:api[_-]?key|secret|password|token)\s*[:=]\s*["\'][^"\']{24,}["\']'),
 'PRIVATE_KEY': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
 'DISALLOWED_PII': re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', re.I),
}

def scan(root: Path) -> dict:
    root=root.resolve(); findings=[]
    for path in sorted(root.rglob('*')):
        if not path.is_file() or any(part in ROOT_EXCLUDES for part in path.relative_to(root).parts): continue
        if path.suffix.lower() not in {'.py','.js','.ts','.tsx','.html','.json','.yaml','.yml','.md','.txt','.log'}: continue
        try: text=path.read_text(encoding='utf-8')
        except UnicodeDecodeError: continue
        rel=path.relative_to(root).as_posix()
        for line_no,line in enumerate(text.splitlines(),1):
            for classification,pattern in SECRET_PATTERNS.items():
                if pattern.search(line) and not ('SAFE_SYNTHETIC_FIXTURE' in line or 'DOCUMENTATION_EXAMPLE' in line):
                    findings.append({'path':rel,'line':line_no,'classification':classification})
    counts={key:sum(f['classification']==key for f in findings) for key in SECRET_PATTERNS}
    return {'schema_version':'1','status':'PASS' if not findings else 'FAIL','findings':findings,'counts':counts,'unresolved':len(findings)}

def main():
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument('root',type=Path); parser.add_argument('--output',type=Path)
    result=scan(parser.parse_args().root); payload=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if parser.parse_args().output: parser.parse_args().output.write_text(payload,encoding='utf-8')
    else: print(payload,end='')
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__': raise SystemExit(main())

__all__=['scan']

# ponytail: bounded deterministic regex scan; upgrade to secret scanners when a declared dependency exists.
