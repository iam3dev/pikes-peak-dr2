"""Private preview installer. Exact map version and resource-block gates; Python 3.11+."""
from pathlib import Path
import argparse,base64,hashlib,json,os,shutil,subprocess,sys,datetime
ROOT=Path(sys.executable if getattr(sys,'frozen',False) else __file__).resolve().parent
M=json.loads((ROOT/'manifest.json').read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):
 tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(v,indent=2),encoding='utf-8');os.replace(tmp,p)
def closed():
 r=subprocess.run(['tasklist','/FI','IMAGENAME eq dirtrally2.exe','/FO','CSV','/NH'],capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
 if b'dirtrally2.exe' in r.stdout.lower():raise RuntimeError('Close DiRT Rally 2.0 first')
def target(game,rel):
 p=(game/rel).resolve()
 if not p.is_relative_to(game):raise RuntimeError('Path outside game')
 return p
def block(p,b):
 if p.stat().st_size!=b['file_size']:raise RuntimeError('Unsupported archive layout: '+str(p))
 with p.open('rb') as f:f.seek(b['offset']);return f.read(len(base64.b64decode(b['before'])))
def build_map(stock,dst):
 if sha(ROOT/'map-payload.bin')!=M['payload_sha256']:raise RuntimeError('Payload corrupt')
 with stock.open('rb') as a,(ROOT/'map-payload.bin').open('rb') as b,dst.open('wb') as out:
  for s in M['segments']:
   f=a if s['source']=='stock' else b;f.seek(s['offset']);n=s['length']
   while n:
    data=f.read(min(n,1048576))
    if not data:raise RuntimeError('Truncated input')
    out.write(data);n-=len(data)
 if sha(dst)!=M['installed_sha256']:raise RuntimeError('Map reconstruction mismatch')
def main(argv=None):
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['install','verify','uninstall']);ap.add_argument('--game',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);args=ap.parse_args(argv)
 print('Checking map and compatibility…',flush=True)
 game=args.game.resolve();work=args.work.resolve();mapfile=target(game,M['map_path']);maphash=sha(mapfile)
 states=[]
 for b in M['blocks']:
  value=block(target(game,b['path']),b);before=base64.b64decode(b['before']);after=base64.b64decode(b['after'])
  if value not in (before,after):raise RuntimeError('Unknown tree-settings block: '+b['path'])
  states.append('patched' if value==after else 'stock')
 if maphash not in (M['stock_sha256'],M['installed_sha256']):raise RuntimeError('Unknown Spain archive; nothing changed')
 if args.action=='verify':print(json.dumps({'map':'installed' if maphash==M['installed_sha256'] else 'stock','tree_blocks':states}));return
 closed();work.mkdir(parents=True,exist_ok=True);receipt=work/'installed.json'
 if (work/'pending.json').exists():raise RuntimeError('Pending transaction exists; inspect pending.json before continuing')
 if args.action=='install' and receipt.exists():raise RuntimeError('Installation receipt exists; use verify or uninstall')
 initial={'map':maphash,'tree_blocks':states}
 if args.action=='uninstall':
  if not receipt.exists():raise RuntimeError('Installation receipt missing')
  old=json.loads(receipt.read_text());initial=old['initial']
  if old['game']!=str(game) or maphash!=M['installed_sha256']:raise RuntimeError('Installation changed since receipt')
 # Reserve only the bytes this operation will allocate, grouped by volume.
 allocations={}
 def reserve(path,size):
  volume=Path(path).resolve().anchor
  allocations[volume]=allocations.get(volume,0)+size
 map_changes=maphash==M['stock_sha256'] if args.action=='install' else initial['map']==M['stock_sha256']
 if map_changes:
  reserve(work,mapfile.stat().st_size)
  reserve(mapfile,M['installed_size'] if args.action=='install' else Path(old['map_backup']).stat().st_size)
 for i,b in enumerate(M['blocks']):
  desired='patched' if args.action=='install' else initial['tree_blocks'][i]
  if states[i]!=desired:
   reserve(work,len(base64.b64decode(b['before'])))
   reserve(target(game,b['path']),b['file_size'])
 for volume,amount in allocations.items():
  needed=amount+256*1024**2
  print(f'Space required on {volume}: {needed/1024**3:.2f} GiB (including temporary files)',flush=True)
  if shutil.disk_usage(volume).free<needed:raise RuntimeError(f'Need {needed/1024**3:.2f} GiB free on {volume}')
 operations=[]
 def stage(rel,writer,block_info=None):
  p=target(game,rel);i=len(operations);backup=work/f'{args.action}-{i}.before';staged=p.with_name(p.name+'.pikes-next')
  if backup.exists() or staged.exists():raise RuntimeError('Staging/backup exists; choose a fresh work directory or inspect')
  print('Backing up: '+rel,flush=True)
  before=sha(p)
  if block_info is None:
   shutil.copy2(p,backup);backup_hash=before
  else:
   raw=block(p,block_info);backup.write_bytes(raw);backup_hash=hashlib.sha256(raw).hexdigest()
  if sha(backup)!=backup_hash:raise RuntimeError('Backup mismatch')
  print('Preparing and validating: '+rel,flush=True)
  writer(backup if block_info is None else p,staged);after=sha(staged)
  op={'target':str(p),'backup':str(backup),'stage':str(staged),'before':before,'after':after,'backup_sha256':backup_hash}
  if block_info is not None:op.update(kind='block',offset=block_info['offset'],length=len(raw))
  operations.append(op)
 if args.action=='install':
  if maphash==M['stock_sha256']:stage(M['map_path'],build_map)
 else:
  if initial['map']==M['stock_sha256']:
   original=Path(old['map_backup'])
   if sha(original)!=M['stock_sha256']:raise RuntimeError('Original Spain backup mismatch')
   stage(M['map_path'],lambda src,dst:shutil.copy2(original,dst))
 for i,b in enumerate(M['blocks']):
  desired='patched' if args.action=='install' else initial['tree_blocks'][i]
  if states[i]==desired:continue
  data=base64.b64decode(b['after'] if desired=='patched' else b['before'])
  def patch(src,dst,b=b,data=data):
   shutil.copy2(src,dst)
   with dst.open('r+b') as f:f.seek(b['offset']);f.write(data)
  stage(b['path'],patch,b)
 transaction={'game':str(game),'action':args.action,'initial':initial,'operations':operations,'committed':[]}
 save(work/'pending.json',transaction)
 try:
  for op in operations:
   print('Applying: '+Path(op['target']).name,flush=True)
   closed();p=Path(op['target'])
   if sha(p)!=op['before']:raise RuntimeError('File changed during staging: '+str(p))
   os.replace(op['stage'],p);transaction['committed'].append(op['target']);save(work/'pending.json',transaction)
   if sha(p)!=op['after']:raise RuntimeError('Installed hash mismatch')
 except Exception:
  for op in reversed(operations):
   if op['target'] in transaction['committed'] and sha(Path(op['target']))==op['after']:
    if op.get('kind')=='block':
     restored=Path(op['stage']);shutil.copy2(op['target'],restored)
     with restored.open('r+b') as f:f.seek(op['offset']);f.write(Path(op['backup']).read_bytes())
     if sha(restored)!=op['before']:raise RuntimeError('Rollback integrity check failed; keep pending.json')
     os.replace(restored,op['target'])
    else:shutil.copy2(op['backup'],op['target'])
  raise
 transaction['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 if args.action=='install':
  transaction['map_backup']=next((op['backup'] for op in operations if Path(op['target'])==mapfile),None);save(receipt,transaction)
 else:save(work/'uninstalled.json',transaction);receipt.rename(work/'previous-installed.json')
 (work/'pending.json').unlink();print('PASS: '+args.action+' completed; unrelated archive bytes retained')
if __name__=='__main__':
 try:main()
 except Exception as e:print('STOP: '+str(e),file=sys.stderr);sys.exit(1)
