from pathlib import Path
import json,hashlib,base64,sys
import PikesMod as e
from backup_status import inspect_backup
root=Path(__file__).resolve().parent/'compact-backup-tests';root.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
stock=b'stock-map';mod=b'mod-map-data';payload=root/'map-payload.bin';payload.write_bytes(mod)
e.ROOT=root;e.closed=lambda:None
e.M={'map_path':'map','stock_sha256':sha(stock),'installed_sha256':sha(mod),'installed_size':len(mod),'payload_sha256':sha(mod),'segments':[{'source':'payload','offset':0,'length':len(mod)}],'blocks':[{'path':name,'offset':2,'file_size':7,'before':base64.b64encode(b'old').decode(),'after':base64.b64encode(b'new').decode()} for name in ['tree1','tree2']]}
def setup(name):
 game=root/name;work=root/(name+'-backup');game.mkdir();(game/'map').write_bytes(stock)
 for n in ['tree1','tree2']:(game/n).write_bytes(b'AAoldZZ')
 return game,work
def run(action,game,work):e.main([action,'--game',str(game),'--work',str(work)])
game,work=setup('roundtrip');run('install',game,work)
r=json.loads((work/'installed.json').read_text());assert [Path(op['backup']).stat().st_size for op in r['operations']]==[len(stock),3,3]
assert inspect_backup(str(game),str(work))[0]
(game/'tree1').write_bytes(b'BAnewZZ');run('uninstall',game,work)
assert (game/'map').read_bytes()==stock and (game/'tree1').read_bytes()==b'BAoldZZ' and (game/'tree2').read_bytes()==b'AAoldZZ'
game,work=setup('rollback');replace=e.os.replace
failed=False
def fail_once(src,dst):
 global failed
 if Path(dst)==game/'tree2' and not failed:failed=True;raise OSError('simulated commit failure')
 return replace(src,dst)
e.os.replace=fail_once
try:
 try:run('install',game,work);raise AssertionError('expected failure')
 except OSError as err:assert 'simulated' in str(err)
finally:e.os.replace=replace
assert (game/'map').read_bytes()==stock
for n in ['tree1','tree2']:assert (game/n).read_bytes()==b'AAoldZZ'
assert (work/'pending.json').exists()
print('PASS: compact backup sizes, restore eligibility, unrelated edits preserved, rollback on commit failure')
