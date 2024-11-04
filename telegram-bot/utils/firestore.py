import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("utils/ngsi-ld-systems.json")
app = firebase_admin.initialize_app(cred)
db = firestore.client()

def check_user_exists(user_id):
    user_ref = db.collection('users').document(str(user_id))
    user_doc = user_ref.get()

    if user_doc.exists:
        return True
    return False

def store_user_preference(user_id, preference):
    user_ref = db.collection('users').document(str(user_id))
    user_ref.set({
        'preference': preference
    })

def get_user_preference(user_id):
    user_ref = db.collection('users').document(str(user_id))
    user_doc = user_ref.get()

    if user_doc.exists:
        return user_doc.to_dict()['preference']
    return None

def edit_user_preference(user_id, preference):
    user_ref = db.collection('users').document(str(user_id))
    user_ref.update({
        'preference': preference
    })

def store_user_filter(user_id, filter_name, filter_value):
    user_ref = db.collection('users').document(str(user_id))
    user_ref.set({
        filter_name: filter_value
    })

def get_user_filter(user_id, filter_name):
    user_ref = db.collection('users').document(str(user_id))
    user_doc = user_ref.get()

    if user_doc.exists:
        return user_doc.to_dict()[filter_name]
    return

def edit_user_filter(user_id, filter_name, filter_value):
    user_ref = db.collection('users').document(str(user_id))
    user_ref.update({
        filter_name: filter_value
    })