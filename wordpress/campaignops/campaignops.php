<?php
/**
 * Plugin Name: CampaignOps
 * Description: Campaign asset governance and isolated demonstration journey capture.
 * Version: 1.0.1
 * License: GPL-2.0-or-later
 */
if (!defined('ABSPATH')) exit;

function cops_register() {
    register_post_type('campaign_asset', [
        'label'=>'Campaign assets','public'=>true,'show_in_rest'=>true,
        'supports'=>['title','editor','revisions','custom-fields','author'],
        'menu_icon'=>'dashicons-chart-area','rewrite'=>false,
    ]);
    foreach (['asset_id','campaign_id','owner','review_date','reference_url'] as $key) {
        register_post_meta('campaign_asset', 'cops_'.$key, [
            'type'=>'string','single'=>true,'show_in_rest'=>true,'revisions_enabled'=>true,
            'sanitize_callback'=>$key==='reference_url'?'esc_url_raw':'sanitize_text_field',
            'auth_callback'=>function($allowed,$name,$post_id){return current_user_can('edit_post',$post_id);},
        ]);
    }
    register_post_meta('campaign_asset','cops_mobile_ready',[
        'type'=>'boolean','single'=>true,'show_in_rest'=>true,'revisions_enabled'=>true,
        'sanitize_callback'=>'rest_sanitize_boolean',
        'auth_callback'=>function($allowed,$name,$post_id){return current_user_can('edit_post',$post_id);},
    ]);
}
add_action('init','cops_register');

function cops_seed() {
    cops_register();
    if (get_option('cops_seeded_v1')) return;
    $assets=json_decode(file_get_contents(__DIR__.'/seed.json'),true);
    foreach ($assets as $a) {
        $content='<!-- wp:paragraph --><p>'.esc_html($a['summary']).'</p><!-- /wp:paragraph -->';
        $content.='<!-- wp:paragraph --><p>Independent portfolio demonstration. This page uses original awareness copy and fictional campaign operations. It is not affiliated with WHO or MSD.</p><!-- /wp:paragraph -->';
        $content.='<!-- wp:paragraph --><p><a href="'.esc_url($a['source']).'">Read the public WHO campaign reference</a></p><!-- /wp:paragraph -->';
        $content.='<!-- wp:shortcode -->[campaignops_journey]<!-- /wp:shortcode -->';
        $id=wp_insert_post(['post_type'=>'campaign_asset','post_title'=>$a['title'],'post_content'=>$content,'post_status'=>$a['status'],'post_author'=>1],true);
        if (is_wp_error($id)) continue;
        foreach (['asset_id','campaign_id','owner','review_date'] as $key) update_post_meta($id,'cops_'.$key,$a[$key]);
        update_post_meta($id,'cops_reference_url',$a['source']);
        update_post_meta($id,'cops_mobile_ready',$a['mobile_ready']);
    }
    update_option('cops_seeded_v1',1); flush_rewrite_rules();
}
register_activation_hook(__FILE__,'cops_seed');

add_action('enqueue_block_editor_assets',function(){
    $screen=get_current_screen();
    if(!$screen || $screen->post_type!=='campaign_asset')return;
    wp_enqueue_script('campaignops-editor',plugins_url('editor.js',__FILE__),['wp-element','wp-data','wp-components','wp-editor','wp-plugins'],'1.0.1',true);
});

add_action('add_meta_boxes',function($post_type,$post){
    if($post && use_block_editor_for_post($post))return;
    add_meta_box('cops-governance','CampaignOps governance',function($post){
        wp_nonce_field('cops_save','cops_save_nonce');
        echo '<p>Asset: <code>'.esc_html(get_post_meta($post->ID,'cops_asset_id',true)).'</code></p>';
        foreach (['owner'=>'Owner','review_date'=>'Review date'] as $key=>$label) {
            echo '<p><label>'.esc_html($label).'<br><input name="cops_'.esc_attr($key).'" value="'.esc_attr(get_post_meta($post->ID,'cops_'.$key,true)).'"></label></p>';
        }
        echo '<p><label><input type="checkbox" name="cops_mobile_ready" value="1" '.checked(get_post_meta($post->ID,'cops_mobile_ready',true),true,false).'> Registration visible on mobile</label></p>';
        echo '<p>Publish the change and run a new mobile test. Historical performance is unchanged.</p>';
    },'campaign_asset','normal');
},10,2);
add_action('save_post_campaign_asset',function($id){
    if (!isset($_POST['cops_save_nonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['cops_save_nonce'])),'cops_save') || !current_user_can('edit_post',$id) || wp_is_post_revision($id)) return;
    foreach (['owner','review_date'] as $key) if(isset($_POST['cops_'.$key])) update_post_meta($id,'cops_'.$key,sanitize_text_field(wp_unslash($_POST['cops_'.$key])));
    update_post_meta($id,'cops_mobile_ready',isset($_POST['cops_mobile_ready']));
});

function cops_can_edit(){ return current_user_can('edit_posts'); }
add_action('rest_api_init',function(){
    register_rest_route('campaignops/v1','/inventory',[
        'methods'=>'GET','permission_callback'=>'cops_can_edit',
        'callback'=>function(){
            $result=[];
            foreach (get_posts(['post_type'=>'campaign_asset','post_status'=>['draft','pending','publish','private'],'numberposts'=>100]) as $post) {
                $a=['id'=>$post->ID,'title'=>$post->post_title,'status'=>$post->post_status,'modified'=>$post->post_modified_gmt.'Z','url'=>get_permalink($post),'edit_url'=>get_edit_post_link($post->ID,'raw'),'revision_count'=>count(wp_get_post_revisions($post->ID))];
                foreach (['asset_id','campaign_id','owner','review_date','mobile_ready','reference_url'] as $k) $a[$k]=get_post_meta($post->ID,'cops_'.$k,true);
                $a['mobile_ready']=(bool)$a['mobile_ready']; $a['provenance']='observed_cms'; $result[]=$a;
            }
            return rest_ensure_response($result);
        },
    ]);
    register_rest_route('campaignops/v1','/events',[
        ['methods'=>'GET','permission_callback'=>'cops_can_edit','callback'=>function(){return rest_ensure_response(get_option('cops_test_events',[]));}],
        ['methods'=>'POST','permission_callback'=>function($r){return (bool)wp_verify_nonce($r->get_header('X-CampaignOps-Nonce'),'cops_journey');},
         'args'=>[
            'kind'=>['required'=>true,'type'=>'string','enum'=>['page_view','cta_click','registration']],
            'session_id'=>['required'=>true,'type'=>'string','validate_callback'=>function($v){return is_string($v) && preg_match('/^[a-zA-Z0-9-]{8,80}$/',$v);}],
            'event_id'=>['required'=>true,'type'=>'string','validate_callback'=>function($v){return is_string($v) && preg_match('/^[a-zA-Z0-9-]{8,80}$/',$v);}],
            'post_id'=>['required'=>true,'type'=>'integer'],
            'market'=>['required'=>true,'type'=>'string','enum'=>['AE','SA','QA']],
            'device'=>['required'=>true,'type'=>'string','enum'=>['mobile','desktop']],
         ],
         'callback'=>function($r){
            $id=(int)$r['post_id'];
            if (get_post_type($id)!=='campaign_asset' || get_post_status($id)!=='publish') return new WP_Error('invalid_asset','Asset must be published.',['status'=>400]);
            $events=get_option('cops_test_events',[]);
            $event=['event_id'=>$r['event_id'],'kind'=>$r['kind'],'session_id'=>$r['session_id'],'asset_id'=>get_post_meta($id,'cops_asset_id',true),'campaign_id'=>get_post_meta($id,'cops_campaign_id',true),'market'=>$r['market'],'device'=>$r['device'],'timestamp'=>gmdate('c'),'provenance'=>'observed_test'];
            foreach ($events as $e) if ($e['event_id']===$event['event_id']) {
                $same=$e; unset($same['timestamp']); $incoming=$event; unset($incoming['timestamp']);
                return $same===$incoming ? rest_ensure_response(['accepted'=>true,'duplicate'=>true]) : new WP_Error('conflicting_id','Conflicting event ID.',['status'=>409]);
            }
            if (count($events)>=500) return new WP_Error('demo_full','Export the test ledger and reset the sandbox.',['status'=>429]);
            $events[]=$event; update_option('cops_test_events',$events,false);
            return new WP_REST_Response(['accepted'=>true,'event_id'=>$event['event_id']],201);
         }],
    ]);
});

add_shortcode('campaignops_journey',function(){
    $id=get_the_ID(); if(get_post_status($id)!=='publish') return '<p>Publish this asset to run the journey.</p>';
    $broken=!get_post_meta($id,'cops_mobile_ready',true);
    ob_start(); ?>
    <section id="cops-journey" style="padding:24px;border:1px solid #aabdb4;border-radius:12px;font-family:system-ui">
    <h2>Try the registration journey</h2><p>Isolated test only. No messages are sent. A random session ID records this test in this sandbox.</p>
    <label>Demonstration market <select id="cops-market"><option value="AE">United Arab Emirates</option><option value="SA">Saudi Arabia</option><option value="QA">Qatar</option></select></label>
    <p><button type="button" id="cops-cta">Open demo registration</button></p>
    <form id="cops-form" hidden><p>Fictional attendee. No personal details required.</p><button type="submit">Complete demo registration</button></form>
    <p id="cops-feedback" role="status"></p></section>
    <?php if($broken): ?><style>@media(max-width:600px){#cops-cta{display:none}}</style><?php endif; ?>
    <script>
    (function(){
      const session=crypto.randomUUID(); const endpoint=<?php echo wp_json_encode(rest_url('campaignops/v1/events')); ?>; const nonce=<?php echo wp_json_encode(wp_create_nonce('cops_journey')); ?>;
      const feedback=document.getElementById('cops-feedback');
      async function record(kind){
        const response=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json','X-CampaignOps-Nonce':nonce,'X-WP-Nonce':<?php echo wp_json_encode(wp_create_nonce('wp_rest')); ?>},body:JSON.stringify({event_id:crypto.randomUUID(),session_id:session,post_id:<?php echo (int)$id; ?>,market:document.getElementById('cops-market').value,device:innerWidth<=600?'mobile':'desktop',kind})});
        if(!response.ok) throw new Error('Event capture failed: '+response.status);
      }
      record('page_view').catch(e=>feedback.textContent=e.message);
      document.getElementById('cops-cta').onclick=async()=>{try{await record('cta_click');document.getElementById('cops-form').hidden=false;}catch(e){feedback.textContent=e.message;}};
      document.getElementById('cops-form').onsubmit=async e=>{e.preventDefault();try{await record('registration');feedback.textContent='Demo registration recorded in WordPress.';e.target.querySelector('button').disabled=true;}catch(err){feedback.textContent=err.message;}};
    })();
    </script>
    <?php return ob_get_clean();
});
