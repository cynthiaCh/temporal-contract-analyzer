"""Score-schema normalization and evidence separation; no causal inference."""
def checks(score):
    rows=[]; unknown=[]
    for name, schedule in score.get('schedules', {}).items():
        seen=False
        for field in ['checks','assertions']:
            if field not in schedule:continue
            seen=True
            if not isinstance(schedule[field],list):
                unknown.append({'schedule':name,'field':field,'reason':'not a list'});continue
            for index, item in enumerate(schedule[field]):
                if not isinstance(item,dict):
                    unknown.append({'schedule':name,'field':field,'ordinal':index,'reason':'non-object check'});continue
                rows.append({'schedule':name,'collection':field,'ordinal':index,'check':item,
                             'observation_kind':'actual_expected_check_not_cause'})
        if not seen:unknown.append({'schedule':name,'reason':'no recognized check collection'})
        if schedule.get('runtimeError'):unknown.append({'schedule':name,'runtimeError':schedule['runtimeError']})
    return rows,unknown


def feedback(original, repairs, standards):
    out={'schema':'evidence-feedback-2','standards':standards,'original_effects':original.get('observed_effects'),
         'runs':[],'source_facts':[],'interpretation_hypotheses':[],
         'causal_status':'No cause established by pass/fail or a multi-hunk patch. Agent claims are unverified unless corroborated by actual observations.'}
    for score in repairs:
        row={'verdict':score.get('verdict'),'relations':[],'actual_successes':[], 'original_successes':[],
             'retained_original_successes':[],'improvements':[],'regressions':[],'differences':[],
             'unchanged_failures':[],'unknown':[]}
        for rel in standards:
            key,expected=rel['effect'],rel['expected']
            before=original.get('observed_effects',{}).get(key);actual=score.get('observed_effects',{}).get(key)
            item={'effect':key,'requirement':rel['description'],'expected':expected,'original':before,'actual':actual,
                  'policy_support':rel.get('policy_support'),'kind':'observed_relation_not_causal_explanation'}
            row['relations'].append(item)
            if type(before) is bool and before==expected:
                row['original_successes'].append(item)
            if type(actual) is bool and actual==expected:
                row['actual_successes'].append(item)
            if type(actual) is not bool or type(before) is not bool:
                row['unknown'].append(item);continue
            if actual!=expected:row['differences'].append(item)
            if before==expected:
                row['retained_original_successes' if actual==expected else 'regressions'].append(item)
            elif actual==expected:row['improvements'].append(item)
            else:row['unchanged_failures'].append(item)
        row['all_checks'],row['unknown_check_schemas']=checks(score)
        row['failed_checks']=[x for x in row['all_checks'] if x['check'].get('passed') is False]
        out['runs'].append(row)
    return out
