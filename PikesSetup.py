from pathlib import Path
import contextlib,datetime,hashlib,json,os,queue,sys,threading,tkinter as tk
from tkinter import ttk,filedialog,messagebox
import PikesMod as engine
from backup_status import inspect_backup
import ctypes

def enable_dpi():
 try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
 except (AttributeError,OSError):
  try:ctypes.windll.user32.SetProcessDPIAware()
  except (AttributeError,OSError):pass


class Sink:
 def __init__(self,q):self.q=q
 def write(self,s):
  if s.strip():self.q.put(('log',s.strip()))
 def flush(self):pass

class App:
 def __init__(self,root):
  self.root=root;self.busy=False;self.events=queue.Queue();self.controls=[];self.last_ok=None;self.backup_ok=False;self.backup_generation=0;self.backup_timer=None;self.backup_pending=False
  root.title('Pikes Peak | DiRT Rally 2.0');scale=root.winfo_fpixels('1i')/96;self.dpi_scale=scale
  width=min(round(940*scale),root.winfo_screenwidth()-60);height=min(round(900*scale),root.winfo_screenheight()-100)
  root.geometry(f'{width}x{height}');root.minsize(min(width,round(800*scale)),min(height,round(620*scale)));root.configure(bg='#101923')
  style=ttk.Style();style.theme_use('clam')
  style.configure('.',font=('Segoe UI',11),background='#101923',foreground='#e8eef3')
  style.configure('TFrame',background='#101923');style.configure('TLabel',background='#101923',foreground='#e8eef3')
  style.configure('Muted.TLabel',foreground='#bdcbd8');style.configure('Thanks.TLabel',foreground='#b9ccda',font=('Segoe UI',11))
  style.configure('TEntry',fieldbackground='#1d2b39',foreground='#ffffff',insertcolor='#ffffff',padding=9,borderwidth=0)
  style.map('TEntry',fieldbackground=[('disabled','#17232f')],foreground=[('disabled','#7e92a5')])
  style.configure('TButton',background='#26394a',foreground='#e8eef3',padding=(16,10),borderwidth=0)
  style.map('TButton',background=[('active','#37516a'),('disabled','#1b2a37')],foreground=[('disabled','#75899c')])
  style.configure('Accent.TButton',background='#e9b75d',foreground='#152331',font=('Segoe UI',11,'bold'))
  style.map('Accent.TButton',background=[('active','#ffd38a'),('disabled','#665a44')],foreground=[('disabled','#a39c8f')])
  style.configure('Horizontal.TProgressbar',background='#e9b75d',troughcolor='#223241',borderwidth=0)
  hero=tk.Canvas(root,height=round(164*scale),bg='#152637',highlightthickness=0);hero.pack(fill='x')
  def landscape(event):
   hero.delete('all');w=event.width
   hero.create_polygon(w*.36,164,w*.55,40,w*.65,102,w*.79,22,w,143,w,164,fill='#253f53',outline='')
   hero.create_polygon(w*.50,164,w*.72,90,w*.80,128,w*.90,64,w,114,w,164,fill='#355367',outline='')
   hero.create_line(w*.73,164,w*.77,144,w*.75,135,w*.84,116,w*.86,107,fill='#e9b75d',width=2)
   hero.create_text(30,31,anchor='w',text='UNOFFICIAL COMMUNITY PORT',fill='#e9b75d',font=('Segoe UI',9,'bold'))
   hero.create_text(28,78,anchor='w',text='PIKES PEAK',fill='#f4f7fa',font=('Segoe UI',32,'bold'))
   hero.create_text(30,125,anchor='w',text='DiRT Rally 2.0   /   EARLY PREVIEW 0.6',fill='#b5c7d6',font=('Segoe UI',11))
   hero.scale('all',0,0,1,scale)
  hero.bind('<Configure>',landscape)
  footer=ttk.Frame(root,padding=(30,10,30,18));footer.pack(side='bottom',fill='x')
  ttk.Separator(footer).pack(fill='x',pady=(0,12))
  ttk.Label(footer,text='Special thanks to Samurai for your support and for believing in this project.',style='Thanks.TLabel').pack(anchor='w')
  body=ttk.Frame(root);body.pack(fill='both',expand=True)
  surface=tk.Canvas(body,bg='#101923',highlightthickness=0);scroll=ttk.Scrollbar(body,orient='vertical',command=surface.yview);surface.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');surface.pack(fill='both',expand=True)
  main=ttk.Frame(surface,padding=(30,18,30,10));window=surface.create_window(0,0,window=main,anchor='nw')
  main.bind('<Configure>',lambda e:surface.configure(scrollregion=surface.bbox('all')))
  def resize(e):
   surface.itemconfigure(window,width=e.width)
   for widget in main.winfo_children():
    if isinstance(widget,ttk.Label):widget.configure(wraplength=max(200,e.width-70))
  surface.bind('<Configure>',resize)
  root.bind('<MouseWheel>',lambda e:surface.yview_scroll(-int(e.delta/120),'units'))
  ttk.Label(main,text='A classic climb. A new home.',font=('Segoe UI',15,'bold')).pack(anchor='w')
  ttk.Label(main,text='Replaces the supported Spain route. Includes tree visibility and start-scene fixes.',style='Muted.TLabel',wraplength=790).pack(anchor='w',pady=(5,8))
  ttk.Label(main,text='Known issues: terrain near 11 km and distant tree pop-in. Full-route testing is pending.',style='Muted.TLabel',wraplength=790).pack(anchor='w',pady=(0,10))
  self.game=tk.StringVar(value=self.detect());self.work=tk.StringVar();self.status=tk.StringVar(value='Choose your game folder, then check compatibility.')
  self.row(main,'01   GAME FOLDER',self.game)
  ttk.Label(main,text='Select the existing DiRT Rally 2.0 installation — the folder containing dirtrally2.exe. The mod is installed here.',style='Muted.TLabel',wraplength=790).pack(anchor='w',pady=(4,8))
  self.row(main,'02   BACKUP FOLDER',self.work)
  ttk.Label(main,text='Choose where to save the original files and settings. This can be on another drive. Keep this folder to restore the game later.',style='Muted.TLabel',wraplength=790).pack(anchor='w',pady=(4,8))
  self.backup_text=tk.StringVar(value='Checking for a backup…')
  self.backup_label=ttk.Label(main,textvariable=self.backup_text,wraplength=790,foreground='#e9b75d');self.backup_label.pack(anchor='w',pady=(8,2))
  self.work.trace_add('write',lambda *_:self.schedule_backup_check())
  self.game.trace_add('write',lambda *_:(self.default_work(),self.schedule_backup_check()));self.default_work()
  ttk.Label(main,text='Close the game. A fresh install saves about 2.35 GB of backups and uses up to 6.24 GB of temporary space. Available space is checked per drive.',wraplength=740).pack(anchor='w',pady=(8,12))
  actions=ttk.Frame(main);actions.pack(fill='x')
  for label,action in [('Check compatibility','verify'),('Install mod','install'),('Restore backup','uninstall')]:
   b=ttk.Button(actions,text=label,style='Accent.TButton' if action=='install' else 'TButton',command=lambda a=action:self.start(a));b.pack(side='left',padx=(0,10));self.controls.append(b)
   if action=='uninstall':self.restore_button=b;b.configure(state='disabled')
  self.bar=ttk.Progressbar(main,mode='indeterminate');self.bar.pack(fill='x',pady=(18,8))
  ttk.Label(main,textvariable=self.status,wraplength=740).pack(anchor='w')
  self.log=tk.Text(main,height=6,wrap='word',font=('Segoe UI',11),state='disabled',bg='#0c141d',fg='#d5e1eb',relief='flat',padx=12,pady=10);self.log.pack(fill='both',expand=True,pady=(10,0))
  root.protocol('WM_DELETE_WINDOW',self.close);root.after(100,self.poll);self.schedule_backup_check()
 def row(self,parent,title,var):
  ttk.Label(parent,text=title).pack(anchor='w',pady=(7,4));row=ttk.Frame(parent);row.pack(fill='x')
  e=ttk.Entry(row,textvariable=var,font=('Segoe UI',11));e.pack(side='left',fill='x',expand=True);self.controls.append(e)
  b=ttk.Button(row,text='Browse…',command=lambda:self.browse(var));b.pack(side='left',padx=(8,0));self.controls.append(b)
 def browse(self,var):
  p=filedialog.askdirectory(parent=self.root,initialdir=var.get() or None)
  if p:var.set(p)
 def detect(self):
  candidates=[]
  try:
   import winreg
   with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam') as k:base=Path(winreg.QueryValueEx(k,'SteamPath')[0])
   candidates.append(base/'steamapps/common/DiRT Rally 2.0')
   import re
   for x in re.findall(r'"path"\s+"([^"]+)"',(base/'steamapps/libraryfolders.vdf').read_text()):candidates.append(Path(x.replace('\\\\','\\'))/'steamapps/common/DiRT Rally 2.0')
  except (OSError,ValueError):pass
  return str(next((p for p in candidates if (p/'dirtrally2.exe').exists()),''))
 def default_work(self):
  if not self.game.get():return
  game=Path(self.game.get()).resolve();base=game.parent/'PikesPeak-backups'/hashlib.sha256(str(game).lower().encode()).hexdigest()[:12]
  # Reuse active receipts, choose a new transaction directory after a completed uninstall.
  active=sorted(base.glob('*/installed.json')) if base.exists() else []
  self.work.set(str(active[-1].parent if active else base/datetime.datetime.now().strftime('%Y%m%d-%H%M%S')))
 def schedule_backup_check(self):
  self.backup_generation+=1;self.backup_ok=False;self.backup_pending=True
  if hasattr(self,'restore_button'):self.restore_button.configure(state='disabled')
  self.backup_text.set('Checking backup files and compatibility…')
  self.backup_label.configure(foreground='#e9b75d')
  if self.backup_timer:self.root.after_cancel(self.backup_timer)
  self.backup_timer=self.root.after(450,self.check_backup)
 def check_backup(self):
  self.backup_timer=None;generation=self.backup_generation;game=self.game.get();work=self.work.get()
  def inspect():
   result=inspect_backup(game,work);self.events.put(('backup',(generation,result)))
  threading.Thread(target=inspect,daemon=True).start()
 def start(self,action):
  if self.busy:return
  if action=='uninstall' and not self.backup_ok:
   self.status.set('Restore is unavailable. Check the backup status above.');return
  self.backup_generation+=1
  if not self.game.get().strip() or not self.work.get().strip():messagebox.showerror('Choose a folder','Choose the game folder and a backup folder.');return
  self.busy=True;self.last_ok=None;self.action=action
  for c in self.controls:c.configure(state='disabled')
  self.bar.start(12);self.status.set('Checking files…')
  args=[action,'--game',self.game.get(),'--work',self.work.get()]
  def worker():
   try:
    if action=='uninstall':
     valid,reason=inspect_backup(args[2],args[4])
     if not valid:raise RuntimeError(reason)
    with contextlib.redirect_stdout(Sink(self.events)):engine.main(args)
    self.events.put(('done',True))
   except Exception as e:self.events.put(('log','ERROR: '+str(e)));self.events.put(('done',False))
  threading.Thread(target=worker,daemon=False).start()
 def poll(self):
  try:
   while True:
    kind,value=self.events.get_nowait()
    if kind=='backup':
     generation,(valid,reason)=value
     if generation==self.backup_generation and not self.busy:
      self.backup_pending=False;self.backup_ok=valid;self.backup_text.set(reason);self.backup_label.configure(foreground='#a4dcb5' if valid else '#e9b75d');self.restore_button.configure(state='normal' if valid else 'disabled')
    elif kind=='log':
     if value.startswith('{'):
      try:
       info=json.loads(value);value='Map: '+('Pikes Peak installed' if info['map']=='installed' else 'supported stock Spain')+' | Tree fix: '+', '.join(info['tree_blocks'])
      except (ValueError,KeyError):pass
     self.log.configure(state='normal');self.log.insert('end',value+'\n');self.log.see('end');self.log.configure(state='disabled');self.status.set(value[:180])
    else:
     self.busy=False;self.last_ok=value;self.bar.stop()
     for c in self.controls:c.configure(state='normal')
     self.schedule_backup_check()
     if value and self.action=='uninstall':self.default_work()
     self.status.set('Completed. See the activity log for details.' if value else 'Stopped. See the activity log for the reason.')
  except queue.Empty:pass
  self.root.after(100,self.poll)
 def close(self):
  if self.busy:messagebox.showinfo('Operation in progress','Please wait for the current operation to finish.');return
  self.root.destroy()

if __name__=='__main__':
 enable_dpi();root=tk.Tk();app=App(root)
 if '--smoke-test' in sys.argv:
  i=sys.argv.index('--smoke-test');game,work,report=sys.argv[i+1:i+4];app.game.set(game);app.work.set(work);app.start(sys.argv[i+4] if len(sys.argv)>i+4 else 'verify')
  def finish():
   if app.busy or app.backup_pending:root.after(100,finish);return
   Path(report).write_text(json.dumps({'ok':app.last_ok,'log':app.log.get('1.0','end'),'controls_enabled':all(str(c['state'])=='normal' for c in app.controls if c is not app.restore_button),'restore_enabled':str(app.restore_button['state'])=='normal','backup_status':app.backup_text.get(),'dpi':root.winfo_fpixels('1i')},ensure_ascii=False),encoding='utf-8');root.destroy()
  root.after(100,finish)
 root.mainloop()
