"""Two-resource, one pending block, perfect-candidate counterfactual. No physical-speed claim."""
def pipeline(blocks,producer_seconds_per_token,delivery_seconds):
 if producer_seconds_per_token<0 or delivery_seconds<0:raise ValueError('negative cost')
 produced=verified=previous_verify_start=0.;events=[]
 for b in blocks:
  start=max(produced,previous_verify_start)
  produced=start+b['width']*producer_seconds_per_token
  ready=produced+delivery_seconds
  verify_start=max(verified,ready);verified=verify_start+b['seconds']
  events.append(dict(producer_start=start,producer_finish=produced,ready=ready,verify_start=verify_start,verify_finish=verified))
  previous_verify_start=verify_start
 return dict(decode_seconds=verified,events=events)
