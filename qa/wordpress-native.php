<?php
require '/wordpress/wp-load.php';
$checks=[];
function verify_cops($label,$condition){global $checks;if(!$condition)throw new Exception('FAIL: '.$label);$checks[]=$label;}
wp_set_current_user(1);
$inventory=rest_do_request(new WP_REST_Request('GET','/campaignops/v1/inventory'));
verify_cops('Twelve seeded assets',$inventory->get_status()===200 && count($inventory->get_data())===12);
wp_set_current_user(0);$denied=rest_do_request(new WP_REST_Request('GET','/campaignops/v1/inventory'));verify_cops('Anonymous inventory denied',$denied->get_status()===401);
wp_set_current_user(1);
$id=wp_insert_post(['post_type'=>'campaign_asset','post_title'=>'Native lifecycle verification','post_content'=>'Original content','post_status'=>'draft','meta_input'=>['cops_asset_id'=>'qa-lifecycle','cops_campaign_id'=>'health','cops_owner'=>'Original owner','cops_mobile_ready'=>false]]);
verify_cops('Draft created',get_post_status($id)==='draft');
$request=new WP_REST_Request('POST','/wp/v2/campaign_asset/'.$id);$request->set_body_params(['status'=>'pending']);$result=rest_do_request($request);verify_cops('Native pending review',$result->get_status()===200 && get_post_status($id)==='pending');
$request=new WP_REST_Request('POST','/wp/v2/campaign_asset/'.$id);$request->set_body_params(['status'=>'publish','content'=>'Published original']);$result=rest_do_request($request);verify_cops('Native publication',$result->get_status()===200 && get_post_status($id)==='publish');
wp_save_post_revision($id);$revisions=wp_get_post_revisions($id);$restore_id=array_key_first($revisions);
$request=new WP_REST_Request('POST','/wp/v2/campaign_asset/'.$id);$request->set_body_params(['content'=>'Revised content','meta'=>['cops_owner'=>'Changed owner','cops_mobile_ready'=>true]]);$result=rest_do_request($request);verify_cops('REST content and governance edit',$result->get_status()===200 && get_post_meta($id,'cops_owner',true)==='Changed owner');
wp_restore_post_revision($restore_id);verify_cops('Native content revision restored',get_post($id)->post_content==='Published original');verify_cops('Native metadata revision restored',get_post_meta($id,'cops_owner',true)==='Original owner' && !get_post_meta($id,'cops_mobile_ready',true));
$subscriber=wp_create_user('qa-reader','demonstration-only-password');$user=new WP_User($subscriber);$user->set_role('subscriber');wp_set_current_user($subscriber);
$request=new WP_REST_Request('POST','/wp/v2/campaign_asset/'.$id);$request->set_body_params(['status'=>'draft']);verify_cops('Subscriber editing denied',rest_do_request($request)->get_status()===403);
wp_set_current_user(1);
$request=new WP_REST_Request('POST','/campaignops/v1/events');$request->set_body_params(['kind'=>'page_view','session_id'=>'native-session-123','event_id'=>'native-event-123','post_id'=>$id,'market'=>'AE','device'=>'mobile']);verify_cops('Missing journey nonce denied',rest_do_request($request)->get_status()===403);
$request->set_header('X-CampaignOps-Nonce',wp_create_nonce('cops_journey'));verify_cops('Valid journey captured',rest_do_request($request)->get_status()===201);verify_cops('Identical journey ID is idempotent',rest_do_request($request)->get_status()===200);
$request->set_param('kind','registration');verify_cops('Conflicting journey ID denied',rest_do_request($request)->get_status()===409);
$receipt=json_encode(['passed'=>count($checks),'checks'=>$checks],JSON_PRETTY_PRINT);
file_put_contents('/verification/wordpress-native.json',$receipt);
echo $receipt;
