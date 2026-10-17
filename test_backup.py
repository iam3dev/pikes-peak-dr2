from pathlib import Path
import json,hashlib,base64,copy
import backup_status as b
p=Path(__file__).resolve().parent;r=p/'test-fixtures';game=r/'game';work=r/'work';game.mkdir(parents=True,exist_ok=True);work.mkdir(exist_ok=True)
stock=b'original map';modified=b'mod map';(game/'map').write_bytes(modified);(game/'tree').write_bytes(b'AAnewZZ');(work/'map.before').write_bytes(stock)
sha=lambda v:hashlib.sha256(v).hexdigest();original=b.engine.M
b.engine.M={'map_path':'map','stock_sha256':sha(stock),'installed_sha256':sha(modified),'blocks':[{'path':'tree','offset':2,'file_size':7,'before':base64.b64encode(b'old').decode(),'after':base64.b64encode(b'new').decode()}]}
receipt={'game':str(game),'initial':{'map':sha(stock),'tree_blocks':['stock']},'operations':[{'target':str(game/'map'),'backup':str(work/'map.before'),'before':sha(stock)}],'map_backup':str(work/'map.before')}
def record(v):(work/'installed.json').write_text(json.dumps(v))
def check(expected):
 actual=b.inspect_backup(str(game),str(work));assert actual[0]==expected,actual;return actual[1]
results={'missing_record':b.inspect_backup(str(game),str(r/'empty'))[0]};assert results['missing_record'] is False
record(receipt);results['valid']=check(True)
(work/'map.before').write_bytes(b'damaged');results['corrupt']=check(False);(work/'map.before').write_bytes(stock)
(work/'pending.json').write_text('{}');results['pending']=check(False);(work/'pending.json').unlink()
other=copy.deepcopy(receipt);other['game']=str(r/'other');record(other);results['wrong_game']=check(False)
other=copy.deepcopy(receipt);other['operations']=[];record(other);results['no_changes']=check(False)
record(receipt);(game/'map').write_bytes(b'other mod');results['changed_map']=check(False);(game/'map').write_bytes(modified)
(game/'tree').write_bytes(b'AAbadZZ');results['changed_tree']=check(False);(game/'tree').write_bytes(b'AAnewZZ')
(work/'installed.json').write_text('{');results['broken_receipt']=check(False);record(receipt)
# Exercise async UI gate, including stale success after switching folders.
import PikesSetup as ui,time
ui.enable_dpi();root=ui.tk.Tk();app=ui.App(root);app.game.set(str(game));app.work.set(str(work))
def wait():
 deadline=time.monotonic()+10
 while app.backup_pending and time.monotonic()<deadline:root.update();time.sleep(.02)
 assert not app.backup_pending
wait();assert app.backup_ok and str(app.restore_button['state'])=='normal'
app.work.set(str(r/'empty'));assert str(app.restore_button['state'])=='disabled';wait();assert not app.backup_ok
results['async_button_gating']='passed';results['dpi']=root.winfo_fpixels('1i');root.destroy();b.engine.M=original
(p/'backup-tests.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print(json.dumps(results,indent=2))
