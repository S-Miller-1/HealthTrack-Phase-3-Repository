import json
from pathlib import Path
collection = {
 'info': {'name':'HealthTrack Phase 3 - Local API Tests',
          '_postman_id':'a8fb4af6-1916-4b64-b333-35c0ecabd168',
          'schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
          'description':'Fictional local development requests; run login first to set the bearer token.'},
 'variable':[{'key':'baseUrl','value':'http://127.0.0.1:8000'},
             {'key':'token','value':''},{'key':'patientId','value':'1'},
             {'key':'vitalId','value':'1'}, {'key':'activityId','value':'1'},
             {'key':'assignmentId','value':'1'}, {'key':'staffUserId','value':'3'}],
 'item':[]
}
def add(name, method, path, body=None, *, auth=True, form=False, token_save=False, save_id=None):
    req = {'method':method, 'url':{'raw':'{{baseUrl}}'+path, 'host':['{{baseUrl}}'],
                                  'path':[x for x in path.lstrip('/').split('/') if x]},
           'header':[]}
    if auth: req['auth'] = {'type':'bearer','bearer':[{'key':'token','value':'{{token}}','type':'string'}]}
    if body is not None:
        if form:
            req['body']={'mode':'urlencoded','urlencoded':[{'key':k,'value':v,'type':'text'} for k,v in body.items()]}
        else:
            req['header'].append({'key':'Content-Type','value':'application/json'})
            req['body']={'mode':'raw','raw':json.dumps(body,indent=2),'options':{'raw':{'language':'json'}}}
    item={'name':name,'request':req,'response':[]}
    tests=[]
    if token_save:
        tests.append('if (pm.response.code === 200) pm.collectionVariables.set("token", pm.response.json().access_token);')
    if save_id:
        tests.append(f'if (pm.response.code === 201) pm.collectionVariables.set("{save_id}", String(pm.response.json().id));')
    if tests:
        item['event']=[{'listen':'test','script':{'type':'text/javascript','exec':tests}}]
    collection['item'].append(item)

add('Public health', 'GET', '/health',auth=False)
add('Log in as patient','POST','/auth/token',{'username':'demo_patient','password':'Demo-patient-ChangeMe!'},auth=False,form=True,token_save=True)
add('Log in as admin','POST','/auth/token',{'username':'demo_admin','password':'Demo-admin-ChangeMe!'},auth=False,form=True,token_save=True)
add('Log in as nurse','POST','/auth/token',{'username':'demo_nurse','password':'Demo-nurse-ChangeMe!'},auth=False,form=True,token_save=True)
add('List Patients','GET','/patients?skip=0&limit=50')
add('Get Patient','GET','/patients/{{patientId}}')
add('Create Patient - admin','POST','/patients',{'full_name':'Fictional Adult','date_of_birth':'1980-01-01','monitoring_consent':True})
add('Update Patient - admin','PATCH','/patients/{{patientId}}',{'enrolled':True,'monitoring_consent':True})
add('Delete Patient - admin - destructive!','DELETE','/patients/{{patientId}}')
add('Assign Nurse - admin','POST','/assignments',{'staff_user_id':3,'patient_id':1},save_id='assignmentId')
add('Revoke assignment - admin','DELETE','/assignments/{{assignmentId}}')
add('Create Vital','POST','/patients/{{patientId}}/vitals',{'systolic':122,'diastolic':79,'pulse':68,'measured_at':'2026-11-08T09:00:00Z','source':'manual'},save_id='vitalId')
add('List Vitals','GET','/patients/{{patientId}}/vitals?skip=0&limit=50')
add('Get Vital','GET','/vitals/{{vitalId}}')
add('Update Vital - patient','PUT','/vitals/{{vitalId}}',{'systolic':124,'diastolic':80,'pulse':70,'measured_at':'2026-11-08T09:00:00Z','source':'manual'})
add('Delete Vital - patient','DELETE','/vitals/{{vitalId}}')
add('Create Activity','POST','/patients/{{patientId}}/activities',{'steps':6000,'active_minutes':45,'activity_date':'2026-11-07'},save_id='activityId')
add('List Activities','GET','/patients/{{patientId}}/activities?skip=0&limit=50')
add('Get Activity','GET','/activities/{{activityId}}')
add('Update Activity - patient','PUT','/activities/{{activityId}}',{'steps':7000,'active_minutes':50,'activity_date':'2026-11-07'})
add('Delete Activity - patient','DELETE','/activities/{{activityId}}')
add('Invalid Vital - expects 422','POST','/patients/{{patientId}}/vitals',{'systolic':70,'diastolic':90,'pulse':68,'measured_at':'2026-11-08T09:00:00Z','source':'manual'})
add('Vitals date range','GET','/patients/{{patientId}}/vitals?start=2026-11-01T00%3A00%3A00Z&end=2026-11-30T00%3A00%3A00Z')
add('Activity date range','GET','/patients/{{patientId}}/activities?start=2026-11-01&end=2026-11-30')
Path('postman/HealthTrack_Phase3.postman_collection.json').write_text(json.dumps(collection,indent=2)+'\n')
