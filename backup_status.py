"""Read-only restore eligibility. Never treats a receipt alone as a valid backup."""
from pathlib import Path
import base64,json
import PikesMod as engine

def inspect_backup(game_text,work_text):
 if not game_text.strip() or not work_text.strip():return False,'Choose a game folder and a backup folder.'
 game=Path(game_text).resolve();work=Path(work_text).resolve()
 if (work/'pending.json').exists():return False,'Incomplete operation found. Keep these files for recovery; restore is disabled.'
 if not (work/'installed.json').is_file():return False,'No backup found for this installer. Choose an existing backup folder, or install to create one.'
 try:
  old=json.loads((work/'installed.json').read_text(encoding='utf-8'))
  if Path(old['game']).resolve()!=game:return False,'This backup belongs to another game folder.'
  initial=old['initial'];states=initial['tree_blocks'];m=engine.M
  if initial['map'] not in (m['stock_sha256'],m['installed_sha256']) or len(states)!=len(m['blocks']) or any(s not in ('stock','patched') for s in states):return False,'Unsupported installation record. Restore is disabled.'
  if not old['operations']:return False,'This installer made no changes. There is no backup to restore.'
  allowed={engine.target(game,m['map_path'])}|{engine.target(game,b['path']) for b in m['blocks']}
  for op in old['operations']:
   if Path(op['target']).resolve() not in allowed:return False,'Installation record contains an unsupported target.'
   backup=Path(op['backup']).resolve()
   if not backup.is_relative_to(work) or not backup.is_file():return False,'Backup files are missing or have moved. Select their original folder.'
   if op.get('kind')=='block':
    specs=[b for b in m['blocks'] if engine.target(game,b['path'])==Path(op['target']).resolve()]
    if len(specs)!=1 or op['offset']!=specs[0]['offset'] or backup.stat().st_size!=len(base64.b64decode(specs[0]['before'])):return False,'Invalid block backup. Restore is disabled.'
   if engine.sha(backup)!=op.get('backup_sha256',op['before']):return False,'A backup file failed its integrity check. Restore is disabled.'
  if initial['map']==m['stock_sha256']:
   original=Path(old['map_backup']).resolve()
   if not original.is_relative_to(work) or not original.is_file() or engine.sha(original)!=m['stock_sha256']:return False,'The original Spain backup is missing or damaged.'
  if engine.sha(engine.target(game,m['map_path']))!=m['installed_sha256']:return False,'The installed map has changed. This backup cannot be restored automatically.'
  changed=initial['map']==m['stock_sha256']
  for i,b in enumerate(m['blocks']):
   value=engine.block(engine.target(game,b['path']),b);before=base64.b64decode(b['before']);after=base64.b64decode(b['after'])
   if value not in (before,after):return False,'Tree settings were changed by another modification. Restore is disabled.'
   changed=changed or value!=(before if states[i]=='stock' else after)
  if not changed:return False,'There are no changes from this installation left to restore.'
  scope='original Spain and pre-install settings' if initial['map']==m['stock_sha256'] else 'pre-install tree settings only; the map was already installed'
  return True,'Verified backup available — restores '+scope+'.'
 except (OSError,ValueError,KeyError,TypeError,RuntimeError):return False,'Backup record is incomplete, unreadable or incompatible. Restore is disabled.'
