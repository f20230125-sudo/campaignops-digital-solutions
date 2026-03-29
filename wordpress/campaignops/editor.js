/* Native Gutenberg document controls. Values save through the core post/meta API. */
(function(wp){
    const h=wp.element.createElement;
    const Panel=wp.editor.PluginDocumentSettingPanel;
    const TextControl=wp.components.TextControl;
    const CheckboxControl=wp.components.CheckboxControl;
    function Governance(){
        const meta=wp.data.useSelect(select=>select('core/editor').getEditedPostAttribute('meta')||{},[]);
        const type=wp.data.useSelect(select=>select('core/editor').getCurrentPostType(),[]);
        const dispatch=wp.data.useDispatch('core/editor');
        if(type!=='campaign_asset')return null;
        const set=(key,value)=>dispatch.editPost({meta:{...meta,[key]:value}});
        return h(Panel,{name:'campaignops-governance',title:'CampaignOps governance',initialOpen:true},
            h('p',null,'Asset: '+(meta.cops_asset_id||'Unassigned')),
            h(TextControl,{label:'Owner',value:meta.cops_owner||'',onChange:value=>set('cops_owner',value),__next40pxDefaultSize:true,__nextHasNoMarginBottom:true}),
            h(TextControl,{label:'Review date',type:'date',value:meta.cops_review_date||'',onChange:value=>set('cops_review_date',value),__next40pxDefaultSize:true,__nextHasNoMarginBottom:true}),
            h(CheckboxControl,{label:'Registration visible on mobile',checked:!!meta.cops_mobile_ready,onChange:value=>set('cops_mobile_ready',value),__nextHasNoMarginBottom:true}),
            h('p',null,'Save the change and run a fresh mobile test. Historical performance stays unchanged.')
        );
    }
    wp.plugins.registerPlugin('campaignops-governance',{render:Governance,icon:'chart-area'});
})(window.wp);
