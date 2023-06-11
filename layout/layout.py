import streamlit as st
from PIL import Image
import drowsy_detection
import requests
import json

FOOTER_FILE = "layout/src/markdowns/footer.md"

SIDEBAR_OPTIONS = {
    "🏠Home🌐": {
    "page_source": "layout/src/markdowns/home.md"
    },
    "🥱Drowsy Detection😪": {
    "page_source": "layout/src/markdowns/drowsiness_detector.md"
    },
    "🪪About Us🤷": {
    "page_source": "layout/src/markdowns/about.md",
    "image_source": "layout/src/images/about.png"
    },
    "🖁Contact📞": {
    "page_source": "layout/src/markdowns/contact.md",
    "image_source": "layout/src/images/contact.jpg"
    },
    "🛂Settings⚙️": {
    "page_source": "layout/src/markdowns/settings.md",
    },

}
def load_image(image_file):			#helps in loading images.
    img = Image.open(image_file)
    return img
def get_file_content(file_path):
    response = open(file_path, encoding="utf-8").read()
    return response
def display_about_image(file_path):
    img = load_image(file_path)
    st.image(img, width=560)

def display_contact_image(file_path):
    img = load_image(file_path)
    st.image(img, width=350)

def add_common_sidebars(user, db, storage):
    st.empty()

    st.sidebar.title("Choose one from the following options:")
    selection = st.sidebar.radio("", list(SIDEBAR_OPTIONS.keys()))

    with st.spinner(f"Loading {selection} ..."):
      markdown_content = get_file_content(SIDEBAR_OPTIONS[selection]["page_source"])
      st.markdown(markdown_content, unsafe_allow_html=True)  
      
    if selection == "🪪About Us🤷":
      display_about_image(SIDEBAR_OPTIONS[selection]["image_source"])

    if selection == "🖁Contact📞":
      display_contact_image(SIDEBAR_OPTIONS[selection]["image_source"])

    if selection == "🥱Drowsy Detection😪":
      drowsy_detection.run_drowsiness_detection()

    if selection == "🛂Settings⚙️":
      display_settings(user, db, storage)

def display_settings(user, db, storage):
  display_profile_picture(user, db, storage)
  display_emergency_contact(user, db)

def display_profile_picture(user, db, storage):
  # Check For Image
  nImage = db.child(user['localId']).child("Image").get().val()
  # IMAGE FOUND
  if nImage is not None:
    # We plan to store all our image under the child image
    Image = db.child(user['localId']).child("Image").get()
    for img in Image.each():
      img_choice = img.val()
    st.image(img_choice, width=500)
    exp = st.expander('Change Bio and Image')
    # User plan to change profile picture
    with exp:
      newImgPath = st.text_input('Enter full path of your profile image')
      upload_new = st.button('Upload')
      if upload_new:
        uid = user['localId']
        fireb_upload = storage.child(uid).put(newImgPath,user['idToken'])
        a_imgdata_url = storage.child(uid).get_url(fireb_upload['downloadTokens'])
        db.child(uid).child("Image").push(a_imgdata_url)
        st.success('Success!')
        # IF THERE IS NO IMAGE
  else:
    st.info("No profile picture yet")
    newImgPath = st.text_input('Enter full path of your profile image')
    upload_new = st.button('Upload')
    if upload_new:
      uid = user['localId']
      # Stored Initated Bucket in Firebase
      fireb_upload = storage.child(uid).put(newImgPath,user['idToken'])
      # Get the url for easy access
      a_imgdata_url = storage.child(uid).get_url(fireb_upload['downloadTokens'])
      # Put it in our real time database
      db.child(user['localId']).child("Image").push(a_imgdata_url)

def display_emergency_contact(user, db):
  emergency_contact = get_current_emergency_contact(user, db)
  if emergency_contact is not None:
    st.info("Current Emergency contact is " + emergency_contact)
  exp_text_number = st.expander('Change or Add emergency contact')
  with exp_text_number:
    emergency_number = st.text_input('Enter the emergency contact number')
    update = st.button('Update')
    if update:
      uid = user['localId']
      st.info(emergency_number)
      db.child(uid).child("emergency").remove()
      db.child(uid).child('emergency').push(emergency_number)
      st.success('Success!')

def add_common_footer():
  st.markdown(get_file_content(FOOTER_FILE), unsafe_allow_html=True)

def get_current_emergency_contact(user, db):
  emergency_contact_dict = db.child(user['localId']).child("emergency").get().val()
  if emergency_contact_dict is not None:
    return list(emergency_contact_dict.values())[0]
  return ""

def send_text_message(user, db):
  emergency_contact = get_current_emergency_contact(user, db)
  if emergency_contact is not None:
    url = "https://www.fast2sms.com/dev/bulkV2"

    my_data = {
        'sender_id': 'FTWSMS',
        'message': 'This is a test message',
        'language': 'english',
        'route': 'q3',
        'numbers': emergency_contact,
        'flash': '0',
    }

    headers = {
        'authorization': 'Yt6ju5AoSiVMkxbX3Q4Nnfw2DmWzJ8aGpKhv0dU9EPBLqcyZsFzKt7nvdfmWDBa80y2ZuHiGUhNceRrP',
        'Content-Type': "application/x-www-form-urlencoded",
        'Cache-Control': "no-cache"
    }

    response = requests.request("POST",
                                url,
                                data = my_data,
                                headers = headers)
    returned_msg = json.loads(response.text)
    st.info(returned_msg['message'])