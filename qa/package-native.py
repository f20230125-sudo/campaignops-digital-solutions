import json,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with zipfile.ZipFile(root/'public/downloads/campaignops-blueprint.zip') as z:
    blueprint=json.loads(z.read('blueprint.json'));plugin=z.read('campaignops-plugin.zip')
blueprint['steps'].append({'step':'runPHP','code':(root/'qa/wordpress-native.php').read_text(encoding='utf-8')})
(root/'runtime').mkdir(exist_ok=True)
with zipfile.ZipFile(root/'runtime/native-qa.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('blueprint.json',json.dumps(blueprint));z.writestr('campaignops-plugin.zip',plugin)
