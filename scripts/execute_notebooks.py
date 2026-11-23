from pathlib import Path
import os
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager
import json
ROOT=Path(__file__).resolve().parents[1]
local=ROOT/'.jupyter'
kernel=local/'kernels'/'workshop'
kernel.mkdir(parents=True,exist_ok=True)
(kernel/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Workshop Python','language':'python'}))
os.environ['JUPYTER_PATH']=str(local)
os.environ['JUPYTER_RUNTIME_DIR']=str(local/'runtime')
os.environ['MPLCONFIGDIR']=str(local/'matplotlib')
for path in sorted((ROOT/'notebooks').glob('*.ipynb')):
    notebook=nbformat.read(path,as_version=4)
    NotebookClient(notebook,timeout=180,kernel_name='workshop',resources={'metadata':{'path':str(ROOT)}}).execute()
    notebook.metadata.kernelspec={'name':'python3','display_name':'Python 3','language':'python'}
    nbformat.write(notebook,path)
    print('Ejecutado:',path.name,flush=True)
