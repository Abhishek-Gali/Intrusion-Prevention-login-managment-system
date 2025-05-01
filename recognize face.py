import cv2
import numpy as np
import pickle
from collections import deque
import time
import imutils
import sys
import os

# Load models
landmark_net = cv2.dnn.readNetFromONNX("models/face_detection_yunet/face_detection_yunet_2023mar_int8.onnx")
net = cv2.dnn.readNetFromCaffe('deploy.prototxt.txt', 'res10_300x300_ssd_iter_140000.caffemodel')

# Constants
SIMILARITY_THRESHOLD = 0.65
CONFIDENCE_THRESHOLD = 0.65
VOTING_FRAMES = 10
DISPLAY_SCALE = 1.0

def wait_for_seconds(seconds=5):
    print(f"Waiting for {seconds} seconds...")
    time.sleep(seconds)

def cosine_similarity(a, b):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    if a.shape != b.shape:
        return 0.0
    dot_product = np.sum(a * b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

def preprocess_face(face):
    if face.size == 0:
        return None
    face = cv2.resize(face, (100, 100))
    face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    face = cv2.equalizeHist(face)
    face = cv2.cvtColor(face, cv2.COLOR_GRAY2BGR)
    return face.astype(np.float32) / 255.0

def extract_features(face):
    if face is None:
        return None
    return face.flatten()

def eye_aspect_ratio(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def main(capture_mode=False):
    print("Starting face recognition...")
    
    # Load embeddings
    try:
        with open("embeddings.pickle", "rb") as f:
            data = pickle.load(f)
            known_embeddings = data["embeddings"]
            known_names = data["names"]
        print(f"Loaded embeddings for {len(set(known_names))} people")
    except Exception as e:
        print(f"Error loading embeddings: {e}")
        with open("recognition_result.txt", "w") as f:
            f.write("Unknown")
        return

    recent_predictions = deque(maxlen=VOTING_FRAMES)
    recent_similarities = deque(maxlen=VOTING_FRAMES)
    blink_count = 0
    blink_state = False
    consec_frames = 0

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        with open("recognition_result.txt", "w") as f:
            f.write("Unknown")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    start_time = time.time()

    while time.time() - start_time < 25:
        ret, frame = cap.read()
        if not ret:
            break

        frame = imutils.resize(frame, width=int(640 * DISPLAY_SCALE))
        h, w = frame.shape[:2]
        display_frame = frame.copy()

        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), (104, 177, 123))
        net.setInput(blob)
        detections = net.forward()

        faces = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > CONFIDENCE_THRESHOLD:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                startX, startY = max(0, startX), max(0, startY)
                endX, endY = min(w, endX), min(h, endY)
                faces.append((startX, startY, endX, endY))

        if faces:
            (startX, startY, endX, endY) = max(faces, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
            expansion = int(((endX - startX) + (endY - startY)) / 20)
            startX = max(0, startX - expansion)
            startY = max(0, startY - expansion)
            endX = min(w, endX + expansion)
            endY = min(h, endY + expansion)

            face_img = frame[startY:endY, startX:endX]
            if face_img.size == 0:
                continue

            # Blink detection
            face_input = cv2.resize(face_img, (192, 192))
            face_blob = cv2.dnn.blobFromImage(face_input, 1.0 / 255.0, (192, 192), swapRB=True, crop=False)
            landmark_net.setInput(face_blob)
            preds = landmark_net.forward()
            landmarks = preds[0].reshape(-1, 2) * np.array([face_img.shape[1], face_img.shape[0]])

            left_eye = landmarks[36:42]
            right_eye = landmarks[42:48]
            left_ear = eye_aspect_ratio(left_eye)
            right_ear = eye_aspect_ratio(right_eye)
            ear = (left_ear + right_ear) / 2.0



            # Face recognition
            processed_face = preprocess_face(face_img)
            features = extract_features(processed_face)
            if features is None or features.shape != (30000,):
                continue

            best_similarity = -1
            best_identity = "Unknown"
            for known_embedding, known_name in zip(known_embeddings, known_names):
                similarity = cosine_similarity(features, known_embedding)
                if similarity > best_similarity:
                    best_similarity = similarity
                    if similarity > SIMILARITY_THRESHOLD:
                        best_identity = known_name

            recent_predictions.append(best_identity)
            recent_similarities.append(best_similarity)

            identity = max(set(recent_predictions), key=recent_predictions.count)

            # Write result immediately
            with open("recognition_result.txt", "w") as f:
                f.write(identity)

            if capture_mode:
                cv2.imwrite("temp.jpg", face_img)
                break

                        # Display
            cv2.rectangle(display_frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
            cv2.putText(display_frame, identity, (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
            
        cv2.imshow("Face Recognition", display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q') or (capture_mode or liveness_mode) or (time.time() - start_time > 5):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_mode = "--capture" in sys.argv
    liveness_mode = "--liveness" in sys.argv
    main(capture_mode)
