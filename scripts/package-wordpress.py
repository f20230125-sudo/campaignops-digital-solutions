"""Build a self-contained Blueprint bundle and plugin from reviewed source."""
import json, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'public/downloads'; out.mkdir(parents=True,exist_ok=True)
seed=(ROOT/'data/reference/assets.json').read_bytes()
(ROOT/'wordpress/campaignops/seed.json').write_bytes(seed)
with zipfile.ZipFile(out/'campaignops-plugin.zip','w',zipfile.ZIP_DEFLATED) as z:
    for file in sorted((ROOT/'wordpress/campaignops').glob('*')): z.write(file,'campaignops/'+file.name)
blueprint={
    '$schema':'https://playground.wordpress.net/blueprint-schema.json',
    'meta':{'title':'CampaignOps operations sandbox','author':'Uzair','description':'Independent demo: 12 original assets, real WordPress editing and isolated test journeys.'},
    'preferredVersions':{'php':'8.3','wp':'7.0'},
    'features':{'networking':True},'login':True,
    'landingPage':'/wp-admin/edit.php?post_type=campaign_asset',
    'steps':[{'step':'installPlugin','pluginData':{'resource':'bundled','path':'campaignops-plugin.zip'},'options':{'activate':True}},
             {'step':'setSiteOptions','options':{'blogname':'CampaignOps test workspace','blogdescription':'Isolated portfolio demonstration'}}],
}
with zipfile.ZipFile(out/'campaignops-blueprint.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('blueprint.json',json.dumps(blueprint,indent=2)); z.write(out/'campaignops-plugin.zip','campaignops-plugin.zip')
(ROOT/'wordpress/blueprint.json').write_text(json.dumps(blueprint,indent=2)+'\n')
print('Packaged plugin and portable Blueprint bundle.')
