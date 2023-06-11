import av                                                   #it is for direct and precise access to your media via containers, streams, packets, codecs, and frames.
import cv2                                                  #a function to read video.
import time
import threading
import os                                                   #it provides an easy way for the user to interact with several os functions that come in handy in day to day programming.import threading
import numpy as np                                          #used for working with arrays and also has functions for working in domain of linear algebra, fourier transform, and matrices. 
import mediapipe as mp                                      # Google's open-source framework, used for media processing.
import streamlit as st
from mediapipe.python.solutions.drawing_utils import _normalized_to_pixel_coordinates as denormalize_coordinates
from streamlit_webrtc import VideoHTMLAttributes, webrtc_streamer
from audio_handling import AudioFrameHandler

def mediapipe_app(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
):
   
    face_mesh = mp.solutions.face_mesh.FaceMesh(                                #Initializing and return Mediapipe FaceMesh Solution Graph object.
        max_num_faces=max_num_faces,
        refine_landmarks=refine_landmarks,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )

    return face_mesh

def extent(point_1, point_2):
    dist = sum([(i - j) ** 2 for i, j in zip(point_1, point_2)]) ** 0.5         #Calculate l2-norm between two points.
    return dist


def getting_ear(landmarks, refer_idxs, frame_width, frame_height):
    """
    Calculate Eye Aspect Ratio for one eye.

    Args:
        landmarks: (list) Detected landmarks list
        refer_idxs: (list) Index positions of the chosen landmarks
                            in order P1, P2, P3, P4, P5, P6
        frame_width: (int) Width of captured frame
        frame_height: (int) Height of captured frame

    Returns:
        ear: (float) Eye aspect ratio
    """
    try:
        coords_points = []                                                      # Computing the euclidean distance between the horizontal.
        for i in refer_idxs:
            lm = landmarks[i]
            coord = denormalize_coordinates(lm.x, lm.y, frame_width, frame_height)
            coords_points.append(coord)

        P2_P6 = extent(coords_points[1], coords_points[5])                      # Eye landmark (x, y)-coordinates.
        P3_P5 = extent(coords_points[2], coords_points[4])                      # Eye landmark (x, y)-coordinates.
        P1_P4 = extent(coords_points[0], coords_points[3])                      # Eye landmark (x, y)-coordinates

        ear = (P2_P6 + P3_P5) / (2.0 * P1_P4)                                   #Computing the eye aspect ratio.

    except:
        ear = 0.0
        coords_points = None

    return ear, coords_points


def avg_ear(landmarks, left_eye_idxs, right_eye_idxs, image_w, image_h):

    left_ear, left_lm_coordinates = getting_ear(landmarks, left_eye_idxs, image_w, image_h)         # Calculating Eye aspect ratio.
    right_ear, right_lm_coordinates = getting_ear(landmarks, right_eye_idxs, image_w, image_h)      # Calculating Eye aspect ratio.
    Avg_EAR = (left_ear + right_ear) / 2.0

    return Avg_EAR, (left_lm_coordinates, right_lm_coordinates)


def plotting_eye_landmarks(frame, left_lm_coordinates, right_lm_coordinates, color):
    for lm_coordinates in [left_lm_coordinates, right_lm_coordinates]:
        if lm_coordinates:
            for coord in lm_coordinates:
                cv2.circle(frame, coord, 2, color, -1)

    frame = cv2.flip(frame, 1)
    return frame


def game_text(image, text, origin, color, font=cv2.FONT_HERSHEY_SIMPLEX, fntScale=0.8, thickness=2):
    image = cv2.putText(image, text, origin, font, fntScale, color, thickness)
    return image


class VideoFrameHandler:
    def __init__(self):
        """
        Initialize the necessary constants, mediapipe app
        and tracker variables
        """
        
        self.eye_idxs = {                                               # Left and right eye chosen landmarks.
            "left": [362, 385, 387, 263, 373, 380],
            "right": [33, 160, 158, 133, 153, 144],
        }

        #Used for coloring landmark points. Its value depends on the current EAR value.
        self.RED = (0, 0, 255)      # BGR
        self.GREEN = (0, 255, 0)    # BGR

        self.facemesh_model = mediapipe_app()                           #Initializing Mediapipe FaceMesh solution pipeline.

        self.state_tracker = {                                          #For tracking counters and sharing states in and out of callbacks.
            "start_time": time.perf_counter(),
            "DROWSINESS_TIME": 0.0,                                     #Holds the amount of time passed with EAR < EAR_THRESH.
            "COLOR": self.GREEN,
            "play_alarm": False,
        }

        self.EAR_txt_pos = (10, 30)

    def process(self, frame: np.array, thresholds: dict):
        """
        This function is used to implement our Drowsy detection algorithm

        Args:
            frame: (np.array) Input frame matrix.
            thresholds: (dict) Contains the two threshold values
                               WAIT_TIME and EAR_THRESH.

        Returns:
            The processed frame and a boolean flag to
            indicate if the alarm should be played or not.
        """

        frame.flags.writeable = False                                   #To improve performance, marking the frame as not writeable to pass by reference.
        frame_h, frame_w, _ = frame.shape

        DROWSY_TIME_txt_pos = (10, int(frame_h // 2 * 1.7))
        ALM_txt_pos = (10, int(frame_h // 2 * 1.85))

        results = self.facemesh_model.process(frame)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            EAR, coordinates = avg_ear(landmarks, self.eye_idxs["left"], self.eye_idxs["right"], frame_w, frame_h)
            frame = plotting_eye_landmarks(frame, coordinates[0], coordinates[1], self.state_tracker["COLOR"])

            if EAR < thresholds["EAR_THRESH"]:

                end_time = time.perf_counter()                      #Increase DROWSY_TIME to track the time period with EAR less than the threshold and reset the start_time for the next iteration.

                self.state_tracker["DROWSINESS_TIME"] += end_time - self.state_tracker["start_time"]
                self.state_tracker["start_time"] = end_time
                self.state_tracker["COLOR"] = self.RED

                if self.state_tracker["DROWSINESS_TIME"] >= thresholds["WAIT_TIME"]:
                    self.state_tracker["play_alarm"] = True
                    game_text(frame, "WAKE UP! WAKE UP", ALM_txt_pos, self.state_tracker["COLOR"])

            else:
                self.state_tracker["start_time"] = time.perf_counter()
                self.state_tracker["DROWSINESS_TIME"] = 0.0
                self.state_tracker["COLOR"] = self.GREEN
                self.state_tracker["play_alarm"] = False

            EAR_txt = f"EAR: {round(EAR, 2)}"
            DROWSY_TIME_txt = f"DROWSY: {round(self.state_tracker['DROWSINESS_TIME'], 3)} Secs"
            game_text(frame, EAR_txt, self.EAR_txt_pos, self.state_tracker["COLOR"])
            game_text(frame, DROWSY_TIME_txt, DROWSY_TIME_txt_pos, self.state_tracker["COLOR"])

        else:
            self.state_tracker["start_time"] = time.perf_counter()
            self.state_tracker["DROWSINESS_TIME"] = 0.0
            self.state_tracker["COLOR"] = self.GREEN
            self.state_tracker["play_alarm"] = False

            frame = cv2.flip(frame, 1)                                #Flip the frame horizontally for a selfie-view display.

        return frame, self.state_tracker["play_alarm"]

def run_drowsiness_detection():
    alarm_file_path = os.path.join("audio", "wake_up.wav")              #Define the audio file to use.
    col1, col2 = st.columns(spec=[6, 2], gap="medium")

    with st.container():
        c1, c2 = st.columns(spec=[1, 1])
        with c1:
            WAIT_TIME = st.slider("Seconds to wait before sounding alarm:", 0.0, 5.0, 1.0, 0.25)    #The amount of time (in seconds) to wait before sounding the alarm.

        with c2:
            EAR_THRESH = st.slider("Eye Aspect Ratio threshold:", 0.0, 0.4, 0.18, 0.01)             #Lowest valid value of Eye Aspect Ratio. Ideal values [0.15, 0.2].

    thresholds = {
        "EAR_THRESH": EAR_THRESH,
        "WAIT_TIME": WAIT_TIME,
    }

    video_handler = VideoFrameHandler()                                                                 #For streamlit-webrtc.
    audio_handler = AudioFrameHandler(sound_file_path=alarm_file_path)                                  #For streamlit-webrtc.

    lock = threading.Lock()                                                                             #For thread-safe access & to prevent race-condition.
    shared_state = {"play_alarm": False}

    def video_frame_callback(frame: av.VideoFrame):
        frame = frame.to_ndarray(format="bgr24")                                                        #Decode and convert frame to RGB.

        frame, play_alarm = video_handler.process(frame, thresholds)                                    #Process frame.
        with lock:
            shared_state["play_alarm"] = play_alarm                                                     #Update shared state.

        return av.VideoFrame.from_ndarray(frame, format="bgr24")                                        #Encode and return BGR frame.

    def audio_frame_callback(frame: av.AudioFrame):
        with lock:                                                                                      #access the current “play_alarm” state.
            play_alarm = shared_state["play_alarm"]

        new_frame: av.AudioFrame = audio_handler.process(frame, play_sound=play_alarm)
        return new_frame

    with col1:
        ctx = webrtc_streamer(
            key="drowsiness-detection",
            video_frame_callback=video_frame_callback,
            audio_frame_callback=audio_frame_callback,
            media_stream_constraints={"video": {"height": {"ideal": 480}}, "audio": True},
            video_html_attrs=VideoHTMLAttributes(autoPlay=True, controls=False, muted=False),
        )
