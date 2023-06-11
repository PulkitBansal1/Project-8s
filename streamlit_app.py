#Modules
import sys

if sys.version_info.major == 3 and sys.version_info.minor >= 10:
    import collections
    setattr(collections, "MutableMapping", collections.abc.MutableMapping)
    setattr(collections, "Mapping", collections.abc.Mapping)

from pyrebase import pyrebase
import streamlit as st
from layout import layout

# Configuration Key
firebaseConfig = {
    'apiKey': "AIzaSyDkndARN_GpKGpuTsn6rIFEj-OuGFFe1Bs",
    'authDomain': "major-project-1cd53.firebaseapp.com",
    'projectId': "major-project-1cd53",
    'databaseURL': "https://major-project-1cd53-default-rtdb.asia-southeast1.firebasedatabase.app/",
    'storageBucket': "major-project-1cd53.appspot.com",
    'messagingSenderId': "126083698151",
    'appId': "1:126083698151:web:92527f6a693a02dbec0142",
    'measurementId': "G-20EDGB6GTF"
}

# Firebase Authentication
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

#Database
db = firebase.database()
storage = firebase.storage()

st.set_page_config(
    page_title="Real Time Drowsiness Detection | Graphic Era",
    page_icon=':whale2:',
    layout="wide",  # centered, wide
    initial_sidebar_state="expanded",
)

st.sidebar.title("🆘OUR DROWSINESS APP" '🚗 🚕 🚙 🚌 🚓 🚐')

#Authentication

choice = st.sidebar.selectbox("📱" 'Login/Signup' "📲",['Login','Sign up'])

email = st.sidebar.text_input('Please Enter your Email Address'"🆔")
password = st.sidebar.text_input('Please Enter your Password' "🧠",type='password')

if choice == 'Sign up':
    handle = st.sidebar.text_input('Please input your app handle name',value = 'Default')
    submit = st.sidebar.button('Create My Account')

    if submit:
        user = auth.create_user_with_email_and_password(email,password)
        st.success('Your account is created Successfully')
        st.balloons()
        # Sign In
        user = auth.sign_in_with_email_and_password(email,password)
        db.child(user['localId']).child("Handle").set(handle)
        db.child(user['localId']).child("ID").set(user['localId'])
        st.title('Welcome ' + handle)
        st.info('Login via login drop down select box')
if choice == 'Login':
    login = st.sidebar.checkbox('Login')
    if login:
        user = auth.sign_in_with_email_and_password(email,password)
        st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)

        layout.add_common_sidebars(user, db, storage)
        layout.add_common_footer()
